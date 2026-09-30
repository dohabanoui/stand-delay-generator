"""Instance synthétique de stands (cahier des charges §5.1)."""
from __future__ import annotations

import numpy as np
import pandas as pd

CAT_RANK = {"RJ": 0, "NB": 1, "WB": 2}


def peak_occupancy(schedule: pd.DataFrame, step: int = 5) -> int:
    """Nombre maximal de rotations simultanément au sol (horaires programmés), pas de `step` minutes."""
    a = schedule["a_sched"].to_numpy(); d = schedule["d_sched"].to_numpy()
    t = np.arange(min(a.min(), 0), max(d.max(), 1440) + step, step)
    occ = ((a[None, :] <= t[:, None]) & (d[None, :] > t[:, None])).sum(axis=1)
    return int(occ.max())


def build(schedule: pd.DataFrame, n_stands: int | None = None, target_peak_occupancy: float = 0.88,
          shares: dict | None = None, seed: int = 0, dist_range: tuple = (50, 600)) -> pd.DataFrame:
    """Stands avec catégorie maximale admissible et distance de marche. Le nombre de stands est fixé pour
    que l'occupation de pointe programmée soit ~ target_peak_occupancy. Les parts par catégorie sont
    ajustées pour que chaque catégorie de trafic dispose d'au moins sa pointe propre (faisabilité)."""
    shares = shares or {"WB": 0.15, "NB": 0.70, "RJ": 0.15}
    rng = np.random.default_rng(seed)
    if n_stands is None:
        n_stands = int(np.ceil(peak_occupancy(schedule) / target_peak_occupancy))
    n_wb = max(int(round(shares["WB"] * n_stands)), int((schedule.category == "WB").sum() > 0))
    # faisabilité : au moins la pointe WB propre
    wb = schedule[schedule.category == "WB"]
    if len(wb):
        n_wb = max(n_wb, peak_occupancy(wb))
    n_nb = int(round(shares["NB"] * n_stands))
    n_rj = max(n_stands - n_wb - n_nb, 0)
    cats = ["WB"] * n_wb + ["NB"] * n_nb + ["RJ"] * n_rj
    dist = rng.uniform(dist_range[0], dist_range[1], size=n_stands)
    # les stands WB (plus rares) sont en général plus éloignés du terminal : tri croissant des distances
    # attribué RJ < NB < WB pour éviter un biais aléatoire d'une instance à l'autre
    dist = np.sort(dist)
    order = np.argsort([CAT_RANK[c] for c in cats], kind="stable")
    out = pd.DataFrame({"stand": [f"S{i:03d}" for i in range(n_stands)], "cat": np.array(cats)[order], "dist": dist})
    out["cat_rank"] = out["cat"].map(CAT_RANK)
    return out.reset_index(drop=True)


def compatible(schedule: pd.DataFrame, stands: pd.DataFrame) -> np.ndarray:
    """Matrice booléenne (rotations x stands) : cat(t_i) <= cat(k)."""
    r = schedule["category"].astype(str).map(CAT_RANK).fillna(1).to_numpy()
    return r[:, None] <= stands["cat_rank"].to_numpy()[None, :]
