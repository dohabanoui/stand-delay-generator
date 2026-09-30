"""Génération de scénarios de retards pour une journée programmée (vectorisé NumPy).

Chaque scénario : régime -> scores S (M3) -> A = F^{-1}(Phi(S)) (M2) -> slack, D_react (M4) -> G (M5) -> D.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from delaygen.models import dependence, ground, propagation, regime

SCHEDULE_COLS = ["rot_id", "category", "carrier", "origin_region", "a_sched", "d_sched", "hour_block_arr", "hour_block_dep"]


def generate_day(schedule: pd.DataFrame, params: dict, n_scenarios: int, seed: int,
                 forced_regime: str | None = None, peak_multiplier: float = 1.0, weather_shift: float = 0.0,
                 correlation_scale: float = 1.0, propagation_on: bool = True, ground_on: bool = True,
                 lambda_by_regime: bool = True, independent_D: bool = False) -> dict:
    """Retourne un dict d'arrays (n_scenarios x n) : regime, A, D_react, G, D, a_real, d_real."""
    rng = np.random.default_rng(seed)
    day = schedule.reset_index(drop=True)
    n = len(day)
    tA = params["marginals_A_table"]
    tG = params["ground_table"]

    reg = regime.sample_independent(params["regime"], n_scenarios, rng, forced_regime)

    # --- scores et A
    lam_all = dependence.scale_lambdas(params["dependence"]["all"], correlation_scale)
    if lambda_by_regime and all(r in params["dependence"] for r in params["states"]):
        S = np.empty((n_scenarios, n))
        factors = {"Z_d": np.empty((n_scenarios, 1)), "Z_h": None, "h_codes": None}
        for r in params["states"]:
            m = reg == r
            if not m.any():
                continue
            lam_r = dependence.scale_lambdas(params["dependence"][r], correlation_scale)
            S_r, f_r = dependence.sample_scores(day, lam_r, rng, int(m.sum()))
            S[m] = S_r
            factors["Z_d"][m] = f_r["Z_d"]
            if factors["Z_h"] is None:
                factors["Z_h"] = np.empty((n_scenarios, f_r["Z_h"].shape[1]))
                factors["h_codes"] = f_r["h_codes"]
            factors["Z_h"][m] = f_r["Z_h"]
        lam_used = lam_all
    else:
        S, factors = dependence.sample_scores(day, lam_all, rng, n_scenarios)
        lam_used = lam_all
    U = stats.norm.cdf(S)
    A = np.empty((n_scenarios, n))
    h_arr = day["hour_block_arr"].to_numpy()
    peak = np.isin(h_arr, params.get("peak_hours", []))
    for s in range(n_scenarios):
        for h in np.unique(h_arr):
            m = h_arr == h
            A[s, m] = tA.inverse_cdf((int(h), reg[s]), U[s, m])
    if peak_multiplier != 1.0:
        A[:, peak] = np.where(A[:, peak] > 0, A[:, peak] * peak_multiplier, A[:, peak])
    if weather_shift:
        A[reg == "degrade"] += weather_shift
    # arrivées fictives (first_departure) : A = 0
    if "first_departure" in day:
        A[:, day["first_departure"].to_numpy(dtype=bool)] = 0.0

    # --- propagation
    slack = propagation.slack(day, params["mtt"])
    D_react = propagation.reactionary(A, slack) if propagation_on else np.zeros_like(A)

    # --- retard sol
    if ground_on:
        if independent_D:
            # baseline : D tiré indépendamment de sa marginale globale (classe (heure dep, régime)), sans A
            U2 = rng.random((n_scenarios, n))
            G = np.empty_like(U2)
            hdep = day["hour_block_dep"].to_numpy()
            tD = params["marginals_D_table"]
            for s in range(n_scenarios):
                for h in np.unique(hdep):
                    m = hdep == h
                    G[s, m] = tD.inverse_cdf((int(h), reg[s]), U2[s, m])
        else:
            G = ground.sample(day, tG, reg, factors, lam_used, params["rho_G"], rng)
    else:
        G = np.zeros_like(A)
    if not params.get("allow_early_departure", True):
        G = np.clip(G, 0, None)
    # --- composition : le départ a lieu au plus tard entre « avion prêt » (arrivée + MTT) et « départ
    # programmé + retard sol propre » : D = max(A - slack, G) (composition 'max', turnaround critique) ;
    # variante 'additive' du cahier des charges : D = D_react + G.
    if propagation_on:
        if params.get("ground_composition", "max") == "additive":
            D = np.maximum(D_react + G, A - slack)
        else:
            D = np.maximum(A - slack, G)
    else:
        D = G
    if "open_rotation" in day:  # départ fictif : D = 0 (avion reste la nuit)
        D[:, day["open_rotation"].to_numpy(dtype=bool)] = 0.0
    a_real = day["a_sched"].to_numpy(dtype=float)[None, :] + A
    d_real = day["d_sched"].to_numpy(dtype=float)[None, :] + D
    return {"regime": reg, "A": A, "D_react": D_react, "G": G, "D": D, "a_real": a_real, "d_real": d_real}


def to_long(schedule: pd.DataFrame, out: dict, date=None, generator: str = "proposed") -> pd.DataFrame:
    n_sc, n = out["A"].shape
    rot_id = np.tile(schedule["rot_id"].to_numpy(), n_sc)
    df = pd.DataFrame({
        "scenario": np.repeat(np.arange(n_sc), n), "rot_id": rot_id,
        "regime": np.repeat(out["regime"].astype(str), n),
        "A": out["A"].ravel(), "D_react": out["D_react"].ravel(), "G": out["G"].ravel(), "D": out["D"].ravel(),
        "a_real": out["a_real"].ravel(), "d_real": out["d_real"].ravel(),
    })
    df["generator"] = generator
    if date is not None:
        df["date"] = date
    return df
