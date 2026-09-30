"""Orchestration de l'estimation : rotations (train) -> params.json (M1..M5) + fit_report.json."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess

import numpy as np
import pandas as pd

from delaygen.config import load_config
from delaygen.models import dependence, ground, marginals, propagation, regime

log = logging.getLogger(__name__)


def config_hash(cfg: dict) -> str:
    return hashlib.sha1(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:10]


def git_revision() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:  # noqa: BLE001
        return None


def fit(rot_train: pd.DataFrame, regime_series: pd.Series, cfg: dict) -> tuple[dict, dict]:
    """Retourne (params, report). `rot_train` : rotations de la période d'estimation."""
    report = {}
    states = cfg["regime"]["states"]
    grid = np.linspace(0.005, 0.995, cfg["marginals"]["grid_points"])
    max_delay = cfg["cleaning"]["max_delay"]
    min_obs = cfg["marginals"]["min_obs_per_class"]

    # M1
    p_regime = regime.fit(regime_series, states)
    report["regime"] = p_regime

    # M2 : marginales de A (rotations avec arrivée réelle)
    arr = rot_train[~rot_train.first_departure].dropna(subset=["A"])
    tA = marginals.fit(arr, "A", "hour_block_arr", "regime", min_obs, grid, max_delay, states)
    report["marginals_A"] = {"n_classes": len(tA.resolved), "n_merged": sum(k != v for k, v in tA.resolved.items()),
                             "n_obs_min": int(min(tA.n_obs.values())), "n_obs_total": int(len(arr))}
    # option paramétrique (comparaison AIC, globale et par régime)
    report["parametric_A"] = {r: marginals.fit_parametric(arr.loc[arr.regime == r, "A"].to_numpy())
                              for r in states}
    for r in states:
        for k, v in report["parametric_A"][r]["fits"].items():
            v.pop("params", None)

    # M3 : copule à facteurs (scores normaux par classe (heure, régime))
    S = dependence.normal_scores(arr, ["hour_block_arr", "regime"], "A")
    lam_all = dependence.fit_moments(arr, S, max_pairs_per_day=cfg["dependence"]["max_pairs_per_day"])
    lam = {"all": lam_all}
    if cfg["dependence"].get("lambda_by_regime", False):
        for r in states:
            m = arr.regime == r
            lam[r] = dependence.fit_moments(arr[m], S[m[m].index.intersection(S.index)],
                                            max_pairs_per_day=cfg["dependence"]["max_pairs_per_day"])
    report["dependence"] = lam

    # M4 : MTT
    mtt = propagation.fit_mtt(rot_train, "category", cfg["propagation"]["mtt_quantile"],
                              cfg["propagation"]["mtt_min_A"], cfg["propagation"]["mtt_default"])
    mtt_real = propagation.fit_mtt(rot_train, "category", cfg["propagation"]["mtt_quantile"],
                                   defaults=cfg["propagation"]["mtt_default"], use_real_ground=True)
    report["mtt"] = {"scheduled_tight": mtt, "real_ground_q05": mtt_real}

    # M5 : retard sol
    tG = ground.fit(rot_train, min_obs, grid, max_delay, states, cfg["generation"].get("allow_early_departure", True))
    report["ground"] = {"n_classes": len(tG.resolved), "n_merged": sum(k != v for k, v in tG.resolved.items())}

    # part observée du retard réactionnel (référence BTS LateAircraftDelay)
    full = rot_train[(~rot_train.open_rotation) & (~rot_train.first_departure)]
    late = full.late_aircraft_delay.fillna(0).sum()
    dep_tot = full.D.clip(lower=0).sum()
    report["bts_late_aircraft_share_of_departure_delay"] = float(late / dep_tot) if dep_tot else None

    params = {
        "hub": cfg["hub"], "config_hash": config_hash(cfg), "git": git_revision(),
        "train_period": cfg["train_period"], "states": states,
        "regime": p_regime, "marginals_A": tA.to_dict(), "dependence": lam, "mtt": mtt,
        "ground": tG.to_dict(), "rho_G": cfg["ground"]["rho_G"],
        "allow_early_departure": cfg["generation"].get("allow_early_departure", True),
        "ground_composition": cfg["ground"].get("composition", "max"),
        "peak_hours": _peak_hours(rot_train),
    }
    return params, report


def _peak_hours(rot: pd.DataFrame) -> list[int]:
    """Heures-blocs de pointe : nombre moyen de rotations par heure > quantile 75 des heures."""
    per_day_hour = rot.groupby(["date", "hour_block_arr"]).size().groupby("hour_block_arr").mean()
    return [int(h) for h in per_day_hour[per_day_hour > per_day_hour.quantile(0.75)].index]


def save(params: dict, report: dict, out_dir: str, hub: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"params_{hub}.json"), "w", encoding="utf-8") as fh:
        json.dump(params, fh, default=_np)
    with open(os.path.join(out_dir, f"fit_report_{hub}.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=_np)


def load_params(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh)
    p["marginals_A_table"] = marginals.QuantileTable.from_dict(p["marginals_A"])
    p["ground_table"] = marginals.QuantileTable.from_dict(p["ground"])
    return p


def _np(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def main(cfg_path: str | None = None, hub: str | None = None) -> None:
    cfg = load_config(cfg_path)
    hub = hub or cfg["hub"]
    proc = cfg["paths"]["processed"]
    rot = pd.read_parquet(os.path.join(proc, f"rotations_{hub}.parquet"))
    reg = pd.read_parquet(os.path.join(proc, f"regime_{hub}.parquet"))
    tr = cfg["train_period"]
    rot_tr = rot[(rot.date >= pd.Timestamp(tr["start"])) & (rot.date <= pd.Timestamp(tr["end"]))]
    reg_tr = reg[(reg.date >= pd.Timestamp(tr["start"])) & (reg.date <= pd.Timestamp(tr["end"]))].sort_values("date")
    params, report = fit(rot_tr, reg_tr["regime"], cfg)
    # un jeu de paramètres par période d'estimation : params_<HUB>_train<YYYY>.json (évite qu'une variante
    # de configuration écrase les paramètres de référence)
    y = str(tr["start"])[:4]
    save(params, report, proc, f"{hub}_train{y}")
    log.info("fit terminé : %s", {k: report["dependence"]["all"][k] for k in ["lambda_d", "lambda_h", "lambda_c", "lambda_r", "sigma_eps"]})


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--hub", default=None)
    a = ap.parse_args()
    main(a.config, a.hub)
