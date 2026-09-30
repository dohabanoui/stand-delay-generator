"""Validation statistique (niveau 1) : marginales réelles vs générées."""
from __future__ import annotations

import numpy as np
from scipy import stats


def compare(real: np.ndarray, gen: np.ndarray, max_n: int = 200_000, seed: int = 0) -> dict:
    """KS, Wasserstein-1, part > 15 min, quantiles, moyenne, écart-type (réel vs généré)."""
    rng = np.random.default_rng(seed)
    real = np.asarray(real, dtype=float)
    gen = np.asarray(gen, dtype=float)
    real = real[~np.isnan(real)]
    gen = gen[~np.isnan(gen)]
    if len(gen) > max_n:
        gen = rng.choice(gen, max_n, replace=False)
    if len(real) > max_n:
        real = rng.choice(real, max_n, replace=False)
    ks = stats.ks_2samp(real, gen)
    q = [0.5, 0.9, 0.95, 0.99]
    qr, qg = np.quantile(real, q), np.quantile(gen, q)
    return {
        "n_real": int(len(real)), "n_gen": int(len(gen)),
        "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
        "wasserstein": float(stats.wasserstein_distance(real, gen)),
        "share_gt15_real": float((real > 15).mean()), "share_gt15_gen": float((gen > 15).mean()),
        "mean_real": float(real.mean()), "mean_gen": float(gen.mean()),
        "std_real": float(real.std()), "std_gen": float(gen.std()),
        "q50_real": float(qr[0]), "q50_gen": float(qg[0]), "q90_real": float(qr[1]), "q90_gen": float(qg[1]),
        "q95_real": float(qr[2]), "q95_gen": float(qg[2]), "q99_real": float(qr[3]), "q99_gen": float(qg[3]),
    }


def qq_points(real: np.ndarray, gen: np.ndarray, grid: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    grid = grid if grid is not None else np.linspace(0.01, 0.99, 99)
    real = np.asarray(real, dtype=float); gen = np.asarray(gen, dtype=float)
    return np.quantile(real[~np.isnan(real)], grid), np.quantile(gen[~np.isnan(gen)], grid)
