"""Utilitaires partagés par les scripts d'expériences."""
from __future__ import annotations

import json
import logging
import os

import numpy as np
import pandas as pd

from delaygen import baselines, fit
from delaygen.config import load_config

log = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def in_period(rot: pd.DataFrame, period: dict) -> pd.Series:
    return (rot.date >= pd.Timestamp(period["start"])) & (rot.date <= pd.Timestamp(period["end"]))


def params_path(cfg: dict, hub: str) -> str:
    """Les paramètres sont nommés d'après le hub et l'année de début de la période d'estimation, ce qui permet
    plusieurs jeux (ex. estimation 2023 vs estimation in-sample 2024) à côté des mêmes rotations."""
    y = str(cfg["train_period"]["start"])[:4]
    return os.path.join(cfg["paths"]["processed"], f"params_{hub}_train{y}.json")


def load_all(cfg_path: str | None = None, hub: str | None = None):
    cfg = load_config(cfg_path)
    hub = hub or cfg["hub"]
    proc = cfg["paths"]["processed"]
    rot = pd.read_parquet(os.path.join(proc, f"rotations_{hub}.parquet"))
    params = fit.load_params(params_path(cfg, hub))
    params = baselines.add_marginal_D(params, rot[in_period(rot, cfg["train_period"])], cfg["marginals"]["min_obs_per_class"])
    return cfg, hub, rot, params


def test_days(rot: pd.DataFrame, every: int = 1, max_days: int | None = None, seed: int = 0, cfg: dict | None = None) -> list:
    mask = in_period(rot, cfg["test_period"]) if cfg else (rot.split == "test")
    days = sorted(rot.loc[mask, "date"].unique())
    days = days[::every]
    if max_days and len(days) > max_days:
        rng = np.random.default_rng(seed)
        days = sorted(rng.choice(days, max_days, replace=False))
    return list(days)


def day_schedule(rot: pd.DataFrame, date) -> pd.DataFrame:
    """Programme d'une journée (toutes rotations, y compris ouvertes / premiers départs) trié par a_sched."""
    d = rot[rot.date == date].sort_values("a_sched").reset_index(drop=True)
    return d


def real_times(day: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Horaires réalisés réels : rotations ouvertes -> d_real = d_sched (fictif) ; premiers départs -> a_real = a_sched."""
    a = day["a_real"].to_numpy(dtype=float); d = day["d_real"].to_numpy(dtype=float)
    a = np.where(np.isnan(a), day["a_sched"].to_numpy(dtype=float), a)
    d = np.where(np.isnan(d), day["d_sched"].to_numpy(dtype=float), d)
    d = np.maximum(d, a)  # cohérence physique minimale
    return a, d


def write_table(df: pd.DataFrame, out_dir: str, name: str, float_fmt: str = "%.2f", caption: str = "", label: str = ""):
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, name + ".csv"), index=False)
    try:
        tex = df.to_latex(index=False, float_format=lambda x: float_fmt % x, escape=True, caption=caption or None,
                          label=label or None)
    except Exception:  # noqa: BLE001
        tex = df.to_latex(index=False, escape=True)
    with open(os.path.join(out_dir, name + ".tex"), "w", encoding="utf-8") as fh:
        fh.write(tex)
    try:
        from tabulate import tabulate
        with open(os.path.join(out_dir, name + ".md"), "w", encoding="utf-8") as fh:
            fh.write(tabulate(df, headers="keys", tablefmt="github", showindex=False, floatfmt=".2f"))
    except ImportError:
        pass


def dump_json(obj, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
