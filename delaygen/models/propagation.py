"""M4 — Propagation arrivée -> rotation -> départ : temps minimal de rotation (MTT), slack, retard réactionnel."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def fit_mtt(rot: pd.DataFrame, by: str = "category", q: float = 0.05, min_A: float = 30.0,
            defaults: dict | None = None, use_real_ground: bool = False) -> dict:
    """MTT(t) = quantile_q(d_sched - a_sched | catégorie t, A >= min_A) sur les rotations complètes.
    Alternative (`use_real_ground`) : quantile q du temps au sol réel (d_real - a_real)."""
    defaults = defaults or {"RJ": 25, "NB": 35, "WB": 60}
    d = rot[(~rot.open_rotation) & (~rot.first_departure)].dropna(subset=["A", "D"])
    col = "ground_real" if use_real_ground else "ground_sched"
    if not use_real_ground:
        d = d[d.A >= min_A]
    d = d[d[col] > 0]
    out = {}
    for cat in ["RJ", "NB", "WB"]:
        g = d[d[by] == cat][col]
        if len(g) >= 50:
            out[cat] = float(np.quantile(g, q))
        else:
            out[cat] = float(defaults.get(cat, 35))
            log.warning("MTT %s : %d obs, valeur par défaut %s", cat, len(g), out[cat])
    log.info("MTT (q=%.2f) : %s", q, {k: round(v, 1) for k, v in out.items()})
    return out


def slack(day: pd.DataFrame, mtt: dict) -> np.ndarray:
    m = day["category"].astype(str).map(mtt).fillna(mtt.get("NB", 35)).to_numpy(dtype=float)
    return np.clip(day["d_sched"].to_numpy(dtype=float) - day["a_sched"].to_numpy(dtype=float) - m, 0, None)


def reactionary(A: np.ndarray, slack_: np.ndarray) -> np.ndarray:
    """D_react = max(0, A - slack) (A peut être une matrice scénarios x rotations)."""
    return np.clip(A - slack_, 0, None)
