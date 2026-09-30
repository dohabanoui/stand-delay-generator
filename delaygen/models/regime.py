"""M1 — Régime météo : chaîne de Markov à deux (ou trois) états."""
from __future__ import annotations

import numpy as np
import pandas as pd


def fit(regimes: pd.Series, states: list[str] | None = None, laplace: float = 1.0) -> dict:
    """Matrice de transition estimée par comptage sur la séquence journalière (lissage de Laplace)."""
    states = list(states or sorted(regimes.dropna().unique()))
    idx = {s: i for i, s in enumerate(states)}
    seq = [idx[s] for s in regimes.dropna() if s in idx]
    counts = np.full((len(states), len(states)), laplace)
    for a, b in zip(seq[:-1], seq[1:]):
        counts[a, b] += 1
    P = counts / counts.sum(axis=1, keepdims=True)
    w, v = np.linalg.eig(P.T)
    pi = np.real(v[:, np.argmin(np.abs(w - 1))])
    pi = pi / pi.sum()
    return {"states": states, "transition_matrix": P.tolist(), "stationary": pi.tolist(),
            "empirical_share": {s: float((regimes == s).mean()) for s in states}}


def sample(params: dict, n_days: int, rng: np.random.Generator, first: str | None = None,
           forced: str | None = None) -> list[str]:
    states = params["states"]
    if forced is not None:
        return [forced] * n_days
    P = np.asarray(params["transition_matrix"])
    pi = np.asarray(params["stationary"])
    cur = states.index(first) if first else rng.choice(len(states), p=pi)
    out = [states[cur]]
    for _ in range(n_days - 1):
        cur = rng.choice(len(states), p=P[cur])
        out.append(states[cur])
    return out


def sample_independent(params: dict, n: int, rng: np.random.Generator, forced: str | None = None) -> np.ndarray:
    """Régime de n jours/scénarios indépendants tirés selon la loi stationnaire."""
    states = np.asarray(params["states"])
    if forced is not None:
        return np.full(n, forced, dtype=object)
    return states[rng.choice(len(states), size=n, p=np.asarray(params["stationary"]))]
