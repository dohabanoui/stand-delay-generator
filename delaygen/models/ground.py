"""M5 — Retard côté sol (départ) non expliqué par l'arrivée, corrélé aux facteurs jour/heure."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from delaygen.models import marginals


def fit(rot: pd.DataFrame, min_obs: int = 200, grid=marginals.GRID_DEFAULT, max_value: float = 360.0,
        regimes: list[str] | None = None, allow_early_departure: bool = True) -> marginals.QuantileTable:
    """Quantiles de D sur les rotations arrivées à l'heure ou en avance (A <= 0), classe (heure départ, régime).
    Si `allow_early_departure` est faux, les départs anticipés (D < 0) sont ramenés à 0."""
    d = rot[(~rot.open_rotation) & (~rot.first_departure) & (rot.A <= 0)].dropna(subset=["D"])
    if not allow_early_departure:
        d = d.assign(D=np.clip(d["D"], 0, None))
    return marginals.fit(d, target="D", hour_col="hour_block_dep", regime_col="regime", min_obs=min_obs,
                         grid=grid, max_value=max_value, regimes=regimes)


def sample(day: pd.DataFrame, table: marginals.QuantileTable, regime: np.ndarray, factors: dict, lam: dict,
           rho_G: float, rng: np.random.Generator) -> np.ndarray:
    """G (n_scenarios x n) : score S^G = rho_G * (lambda_d Z_d + lambda_h Z_h')/sqrt(lambda_d^2+lambda_h^2)
    + sqrt(1-rho_G^2) eta, puis G = F_G^{-1}(Phi(S^G)) par classe (heure départ, régime)."""
    n_sc, n = factors["Z_d"].shape[0], len(day)
    hdep = day["hour_block_dep"].to_numpy()
    # facteur horaire du départ : réutilise Z_h des heures d'arrivée si présente, sinon tirage propre
    h_codes = list(factors["h_codes"])
    Z_h_all = factors["Z_h"]
    extra = {}
    Zh = np.empty((n_sc, n))
    for k, h in enumerate(hdep):
        if h in h_codes:
            Zh[:, k] = Z_h_all[:, h_codes.index(h)]
        else:
            if h not in extra:
                extra[h] = rng.standard_normal(n_sc)
            Zh[:, k] = extra[h]
    denom = np.sqrt(lam["lambda_d"] ** 2 + lam["lambda_h"] ** 2)
    common = (lam["lambda_d"] * factors["Z_d"] + lam["lambda_h"] * Zh) / denom if denom > 0 else np.zeros((n_sc, n))
    S = rho_G * common + np.sqrt(1 - rho_G ** 2) * rng.standard_normal((n_sc, n))
    U = stats.norm.cdf(S)
    G = np.empty_like(U)
    for s in range(n_sc):
        r = regime[s]
        for h in np.unique(hdep):
            m = hdep == h
            G[s, m] = table.inverse_cdf((int(h), r), U[s, m])
    return G
