"""Modèle d'allocation déterministe (banc d'essai) résolu avec OR-Tools CP-SAT (cahier des charges §5.2).

min  sum_i sum_k p_i dist(k) x_ik + M sum_i y_i
s.c. sum_k x_ik + y_i = 1 ; x_ik = 0 si incompatible ;
     pour chaque stand k et chaque clique d'intervalles [a_i - b, d_i + b] : sum_{i in clique} x_ik <= 1
(les cliques maximales d'un graphe d'intervalles sont énumérées aux instants d'arrivée : formulation compacte
équivalente aux contraintes de paires x_ik + x_jk <= 1).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

from delaygen.allocation.instance import compatible


def interval_cliques(a: np.ndarray, d: np.ndarray) -> list[np.ndarray]:
    """Cliques maximales du graphe d'intervalles [a_i, d_i) : ensemble des intervalles actifs à chaque a_i."""
    order = np.argsort(a, kind="stable")
    cliques = []
    for t in a[order]:
        active = np.where((a <= t) & (d > t))[0]
        if len(active) > 1:
            cliques.append(active)
    # suppression des cliques incluses dans une autre (réduction simple)
    cliques.sort(key=len, reverse=True)
    kept, seen = [], []
    for c in cliques:
        s = frozenset(c.tolist())
        if any(s <= k for k in seen):
            continue
        seen.append(s); kept.append(c)
    return kept


def greedy_first_fit(a: np.ndarray, d: np.ndarray, pax: np.ndarray, comp: np.ndarray, dist: np.ndarray) -> np.ndarray:
    """Heuristique de départ : rotations par ordre de pax décroissant puis arrivée, stand compatible libre le
    plus proche. Retourne un tableau d'indices de stand (-1 si aucun)."""
    n, K = comp.shape
    order = np.lexsort((a, -pax))
    busy = [[] for _ in range(K)]  # intervalles occupés par stand
    assign = np.full(n, -1)
    for i in order:
        for k in np.argsort(dist):
            if not comp[i, k]:
                continue
            if all(d[i] <= s or a[i] >= e for s, e in busy[k]):
                busy[k].append((a[i], d[i])); assign[i] = k; break
    return assign


def solve(schedule: pd.DataFrame, stands: pd.DataFrame, buffer_b: float = 0.0, time_limit_s: float = 60.0,
          big_m: float | None = None, workers: int = 8, seed: int = 0, hint: bool = True) -> dict:
    """Retourne {allocation: dict rot_id -> stand|None, objective, status, runtime, n_unassigned}."""
    t0 = time.time()
    n, K = len(schedule), len(stands)
    a = schedule["a_sched"].to_numpy(dtype=float) - buffer_b
    d = schedule["d_sched"].to_numpy(dtype=float) + buffer_b
    pax = schedule["pax"].to_numpy(dtype=float) if "pax" in schedule else np.full(n, 140.0)
    dist = stands["dist"].to_numpy(dtype=float)
    comp = compatible(schedule, stands)
    if big_m is None:
        big_m = 10 * pax.max() * dist.max()  # non-affectation toujours plus chère que le pire stand

    m = cp_model.CpModel()
    x = {}
    for i in range(n):
        for k in range(K):
            if comp[i, k]:
                x[i, k] = m.NewBoolVar(f"x_{i}_{k}")
    y = [m.NewBoolVar(f"y_{i}") for i in range(n)]
    for i in range(n):
        m.Add(sum(x[i, k] for k in range(K) if (i, k) in x) + y[i] == 1)
    cliques = interval_cliques(a, d)
    for k in range(K):
        for c in cliques:
            vars_ = [x[i, k] for i in c if (i, k) in x]
            if len(vars_) > 1:
                m.AddAtMostOne(vars_)
    cost = [int(round(pax[i] * dist[k])) * x[i, k] for (i, k) in x] + [int(big_m) * y[i] for i in range(n)]
    m.Minimize(sum(cost))
    if hint:
        g = greedy_first_fit(a, d, pax, comp, dist)
        for i in range(n):
            m.AddHint(y[i], int(g[i] < 0))
            for k in range(K):
                if (i, k) in x:
                    m.AddHint(x[i, k], int(g[i] == k))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    status = solver.Solve(m)
    alloc, objective, status_name = {}, None, solver.StatusName(status)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i in range(n):
            alloc[int(schedule["rot_id"].iloc[i])] = None
            for k in range(K):
                if (i, k) in x and solver.Value(x[i, k]):
                    alloc[int(schedule["rot_id"].iloc[i])] = stands["stand"].iloc[k]
        objective = float(solver.ObjectiveValue())
    elif hint:
        # repli : la solution gloutonne (faisable par construction) est retournée
        g = greedy_first_fit(a, d, pax, comp, dist)
        alloc = {int(schedule["rot_id"].iloc[i]): (stands["stand"].iloc[g[i]] if g[i] >= 0 else None) for i in range(n)}
        objective = float(sum(pax[i] * dist[g[i]] for i in range(n) if g[i] >= 0) + big_m * (g < 0).sum())
        status_name = "GREEDY_FALLBACK"
    n_un = sum(v is None for v in alloc.values())
    return {"allocation": alloc, "objective": objective, "status": status_name, "runtime": time.time() - t0,
            "n_unassigned": int(n_un), "n_cliques": len(cliques), "n_stands": K, "buffer": buffer_b}
