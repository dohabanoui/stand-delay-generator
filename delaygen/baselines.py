"""Générateurs de référence (« avant ») et variantes d'ablation.

- independent           : mêmes marginales, aucune corrélation, aucune propagation, D indépendant (Monte-Carlo sans corrélation)
- hour_region           : corrélation heure + région seulement, sans propagation (inspiré de Dijk et al. 2019)
- proposed_noprop       : générateur proposé sans propagation (ablation)
- proposed              : générateur complet
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from delaygen import generate
from delaygen.models import marginals

GENERATORS = ["independent", "hour_region", "proposed_noprop", "proposed"]
LABELS = {"independent": "Indépendant (marginales seules)", "hour_region": "Heure+région, sans propagation",
          "proposed_noprop": "Proposé sans propagation (ablation)", "proposed": "Proposé (complet)"}


def add_marginal_D(params: dict, rot_train: pd.DataFrame, min_obs: int = 200) -> dict:
    """Marginale globale de D (toutes rotations complètes), utilisée par la baseline indépendante."""
    d = rot_train[(~rot_train.open_rotation) & (~rot_train.first_departure)].dropna(subset=["D"])
    if not params.get("allow_early_departure", True):
        d = d.assign(D=np.clip(d["D"], 0, None))
    tD = marginals.fit(d, "D", "hour_block_dep", "regime", min_obs, params["marginals_A_table"].grid,
                       params["marginals_A_table"].max_value, params["states"])
    params["marginals_D_table"] = tD
    params["marginals_D"] = tD.to_dict()
    return params


def hour_region_params(params: dict) -> dict:
    """lambda_c = lambda_d = 0 ; garde lambda_h, lambda_r ; renormalise."""
    p = dict(params)
    dep = {}
    for k, v in params["dependence"].items():
        lam_h, lam_r = v["lambda_h"], v["lambda_r"]
        dep[k] = {"lambda_d": 0.0, "lambda_h": lam_h, "lambda_c": 0.0, "lambda_r": lam_r,
                  "sigma_eps": float(np.sqrt(max(1 - lam_h ** 2 - lam_r ** 2, 0.01)))}
    p["dependence"] = dep
    return p


def run(name: str, schedule: pd.DataFrame, params: dict, n_scenarios: int, seed: int, **kw) -> dict:
    """kw transmis à generate_day (ex. forced_regime=<régime réel du jour> pour une génération conditionnée
    à la prévision météo J-1)."""
    if name == "independent":
        return generate.generate_day(schedule, params, n_scenarios, seed, correlation_scale=0.0,
                                     propagation_on=False, independent_D=True, **kw)
    if name == "hour_region":
        return generate.generate_day(schedule, hour_region_params(params), n_scenarios, seed,
                                     propagation_on=False, independent_D=True, lambda_by_regime=True, **kw)
    if name == "proposed_noprop":
        return generate.generate_day(schedule, params, n_scenarios, seed, propagation_on=False, **kw)
    if name == "proposed":
        return generate.generate_day(schedule, params, n_scenarios, seed, **kw)
    raise ValueError(name)
