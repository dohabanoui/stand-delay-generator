"""Validation structurelle (niveau 2) : corrélations intra-groupe, dispersion des comptes horaires, E[D|A]."""
from __future__ import annotations

import numpy as np
import pandas as pd

A_BINS = [-np.inf, 0, 15, 45, np.inf]
A_LABELS = ["A<=0", "0<A<=15", "15<A<=45", "A>45"]


def intra_group_corr(values: np.ndarray, groups: np.ndarray, max_pairs: int = 200_000, seed: int = 0) -> float:
    """Corrélation moyenne des paires (i, j) appartenant au même groupe : E[s_i s_j] sur scores centrés-réduits.
    `values` : 1-D (une journée réelle) ou 2-D (scénarios x rotations, chaque ligne traitée comme une journée)."""
    rng = np.random.default_rng(seed)
    V = np.atleast_2d(np.asarray(values, dtype=float))
    V = (V - np.nanmean(V, axis=1, keepdims=True)) / (np.nanstd(V, axis=1, keepdims=True) + 1e-9)
    codes, inv = np.unique(np.asarray(groups).astype(str), return_inverse=True)
    prods, n = 0.0, 0
    for g in range(len(codes)):
        idx = np.where(inv == g)[0]
        if len(idx) < 2:
            continue
        iu = np.triu_indices(len(idx), k=1)
        i, j = idx[iu[0]], idx[iu[1]]
        if len(i) > max_pairs:
            sel = rng.choice(len(i), max_pairs, replace=False)
            i, j = i[sel], j[sel]
        p = V[:, i] * V[:, j]
        prods += np.nansum(p); n += np.sum(~np.isnan(p))
    return float(prods / n) if n else float("nan")


def late_count_dispersion(late_matrix: np.ndarray, hours: np.ndarray) -> dict:
    """Indice de dispersion du nombre de rotations en retard (>15) par heure : var / moyenne
    (1 = Poisson). `late_matrix` : (scénarios ou jours) x rotations booléen."""
    L = np.atleast_2d(late_matrix).astype(float)
    counts = np.stack([L[:, hours == h].sum(axis=1) for h in np.unique(hours)], axis=1)  # (S, H)
    m = counts.mean(axis=0); v = counts.var(axis=0)
    ok = m > 0.5
    return {"mean": float(m[ok].mean()), "var": float(v[ok].mean()), "index_of_dispersion": float((v[ok] / m[ok]).mean())}


def conditional_departure(A: np.ndarray, D: np.ndarray) -> pd.DataFrame:
    """Table E[D|A] par tranche d'A (bins du cahier des charges)."""
    a = np.asarray(A, dtype=float).ravel(); d = np.asarray(D, dtype=float).ravel()
    m = ~(np.isnan(a) | np.isnan(d))
    df = pd.DataFrame({"A": a[m], "D": d[m]})
    df["bin"] = pd.cut(df.A, A_BINS, labels=A_LABELS)
    return df.groupby("bin", observed=True).D.agg(n="size", mean="mean", median="median", q90=lambda s: s.quantile(.9),
                                                  share_gt15=lambda s: (s > 15).mean())


def reactionary_share(D_react: np.ndarray, D: np.ndarray) -> float:
    """Part du retard de départ positif expliquée par le retard réactionnel."""
    D = np.clip(np.asarray(D, dtype=float), 0, None)
    tot = D.sum()
    return float(np.asarray(D_react).sum() / tot) if tot > 0 else float("nan")
