"""Rejeu d'une allocation sur des horaires réalisés (réels ou générés) — cahier des charges §5.3.

Vectorisé sur les scénarios : a_real, d_real de forme (S, n) ; les métriques de conflit / chevauchement sont
calculées pour chaque scénario ; la heuristique de recours (réaffectations, attente) est évaluée pour
`n_recourse` scénarios au plus (boucle Python).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from delaygen.allocation.instance import CAT_RANK


def _stand_sequences(schedule: pd.DataFrame, allocation: dict) -> list[np.ndarray]:
    """Pour chaque stand : indices (positions dans schedule) des rotations affectées, triés par a_sched."""
    st = schedule["rot_id"].map(allocation)
    seqs = []
    for _, g in schedule.assign(_st=st).dropna(subset=["_st"]).groupby("_st", sort=False):
        idx = g.sort_values("a_sched").index.to_numpy()
        if len(idx) > 1:
            seqs.append(idx)
    return seqs


def conflicts(schedule: pd.DataFrame, allocation: dict, a_real: np.ndarray, d_real: np.ndarray, b_ops: float = 5.0) -> dict:
    """Conflits entre rotations consécutives sur un même stand : arr_reel_j < dep_reel_i + b_ops."""
    A = np.atleast_2d(a_real); D = np.atleast_2d(d_real)
    S = A.shape[0]
    pos = {rid: p for p, rid in enumerate(schedule["rot_id"].to_numpy())}
    seqs = _stand_sequences(schedule.reset_index(drop=True), allocation)
    n_conf = np.zeros(S); overlap = np.zeros(S)
    pair_conf = []
    for idx in seqs:
        i, j = idx[:-1], idx[1:]
        gap = A[:, j] - (D[:, i] + b_ops)          # (S, m)  négatif => conflit
        c = gap < 0
        n_conf += c.sum(axis=1)
        overlap += np.where(c, -gap, 0).sum(axis=1)
        pair_conf.append(c.mean(axis=0))
    return {"conflicts": n_conf, "overlap_minutes": overlap,
            "pair_conflict_prob": np.concatenate(pair_conf) if pair_conf else np.empty(0)}


def greedy_recourse(schedule: pd.DataFrame, stands: pd.DataFrame, allocation: dict, a_real: np.ndarray,
                    d_real: np.ndarray, b_ops: float = 5.0) -> dict:
    """Heuristique gloutonne : parcours des rotations par arrivée réelle ; si le stand prévu est occupé, on
    prend le stand compatible libre le plus proche (distance), sinon la rotation attend la libération."""
    sch = schedule.reset_index(drop=True)
    n = len(sch)
    stand_idx = {s: k for k, s in enumerate(stands["stand"])}
    rank = stands["cat_rank"].to_numpy(); dist = stands["dist"].to_numpy()
    planned = np.array([stand_idx.get(allocation.get(int(r)), -1) for r in sch["rot_id"]])
    cat = sch["category"].astype(str).map(CAT_RANK).fillna(1).to_numpy()
    free_at = np.full(len(stands), -1e9)
    order = np.argsort(a_real, kind="stable")
    n_reassign, n_wait, wait_total = 0, 0, 0.0
    for i in order:
        arr, dep = a_real[i], d_real[i]
        k = planned[i]
        if k >= 0 and free_at[k] + b_ops <= arr:
            free_at[k] = dep; continue
        # stands compatibles libres
        ok = (rank >= cat[i]) & (free_at + b_ops <= arr)
        if ok.any():
            cand = np.where(ok)[0]
            kk = cand[np.argmin(dist[cand])]
            free_at[kk] = dep; n_reassign += 1
        else:
            comp = np.where(rank >= cat[i])[0]
            kk = comp[np.argmin(free_at[comp])]
            w = free_at[kk] + b_ops - arr
            wait_total += w; n_wait += 1
            free_at[kk] = dep + w
            if k != kk:
                n_reassign += 1
    return {"reassignments": n_reassign, "waiting_rotations": n_wait, "waiting_minutes": wait_total}


def evaluate(schedule: pd.DataFrame, stands: pd.DataFrame, allocation: dict, a_real: np.ndarray, d_real: np.ndarray,
             b_ops: float = 5.0, n_recourse: int = 20) -> pd.DataFrame:
    """Métriques par scénario (lignes) : conflicts, overlap_minutes, reassignments, waiting_*."""
    A = np.atleast_2d(np.asarray(a_real, dtype=float)); D = np.atleast_2d(np.asarray(d_real, dtype=float))
    c = conflicts(schedule, allocation, A, D, b_ops)
    out = pd.DataFrame({"scenario": np.arange(A.shape[0]), "conflicts": c["conflicts"], "overlap_minutes": c["overlap_minutes"]})
    rec = {"reassignments": np.nan, "waiting_rotations": np.nan, "waiting_minutes": np.nan}
    for k in rec:
        out[k] = np.nan
    for s in range(min(n_recourse, A.shape[0])):
        r = greedy_recourse(schedule, stands, allocation, A[s], D[s], b_ops)
        for k, v in r.items():
            out.loc[s, k] = v
    return out
