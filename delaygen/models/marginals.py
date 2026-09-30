"""M2 — Marginales de retard par classe (heure-bloc x régime) : quantiles empiriques ou lois paramétriques."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

log = logging.getLogger(__name__)

GRID_DEFAULT = np.linspace(0.005, 0.995, 199)


class QuantileTable:
    """Fonctions quantile empiriques par classe, avec fusion des classes pauvres.

    classes : dict[(hour_block, regime) -> np.ndarray quantiles sur `grid`]
    resolved : dict[classe demandée -> classe effectivement utilisée]
    """

    def __init__(self, grid: np.ndarray, classes: dict, resolved: dict, n_obs: dict, max_value: float):
        self.grid = grid
        self.classes = classes
        self.resolved = resolved
        self.n_obs = n_obs
        self.max_value = max_value

    def _resolve(self, key) -> np.ndarray:
        """Classe effective ; si (heure, régime) est hors de la table (heure absente du train), on prend
        l'heure la plus proche du même régime, sinon la classe globale."""
        key = (int(key[0]), str(key[1]))
        if key in self.resolved:
            return self.classes[self.resolved[key]]
        same = [k for k in self.resolved if k[1] == key[1]]
        if same:
            near = min(same, key=lambda k: abs(k[0] - key[0]))
            self.resolved[key] = self.resolved[near]
            return self.classes[self.resolved[key]]
        if (-1, "global") in self.classes:
            return self.classes[(-1, "global")]
        return next(iter(self.classes.values()))

    def inverse_cdf(self, key, u: np.ndarray) -> np.ndarray:
        q = self._resolve(key)
        return np.interp(u, self.grid, q, left=q[0], right=q[-1])

    def cdf(self, key, x: np.ndarray) -> np.ndarray:
        q = self._resolve(key)
        return np.interp(x, q, self.grid, left=0.0, right=1.0)

    def to_dict(self) -> dict:
        return {"grid": self.grid.tolist(), "max_value": self.max_value,
                "classes": {f"{k[0]}|{k[1]}": v.tolist() for k, v in self.classes.items()},
                "resolved": {f"{k[0]}|{k[1]}": f"{v[0]}|{v[1]}" for k, v in self.resolved.items()},
                "n_obs": {f"{k[0]}|{k[1]}": int(v) for k, v in self.n_obs.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "QuantileTable":
        def key(s):
            h, r = s.split("|")
            return (int(h), r)
        return cls(np.asarray(d["grid"]), {key(k): np.asarray(v) for k, v in d["classes"].items()},
                   {key(k): key(v) for k, v in d["resolved"].items()},
                   {key(k): v for k, v in d["n_obs"].items()}, d["max_value"])


def fit(df: pd.DataFrame, target: str = "A", hour_col: str = "hour_block_arr", regime_col: str = "regime",
        min_obs: int = 200, grid: np.ndarray = GRID_DEFAULT, max_value: float = 360.0,
        regimes: list[str] | None = None) -> QuantileTable:
    """Estime F_k^{-1} pour k = (heure-bloc, régime). Fusion : heure voisine (±1, ±2, ...) du même régime,
    puis même heure tous régimes, puis globale."""
    d = df[[hour_col, regime_col, target]].dropna()
    d = d[d[target].abs() <= max_value]
    regimes = regimes or sorted(d[regime_col].unique())
    hours = sorted(d[hour_col].unique())
    groups = {k: g[target].to_numpy() for k, g in d.groupby([hour_col, regime_col])}
    classes, resolved, n_obs = {}, {}, {}
    glob = np.quantile(d[target].to_numpy(), grid)
    classes[(-1, "global")] = glob
    for h in range(int(min(hours)), int(max(hours)) + 1):
        for r in regimes:
            key = (h, r)
            n_obs[key] = len(groups.get(key, []))
            pool = groups.get(key, np.empty(0))
            used = key
            if len(pool) < min_obs:
                # fusion progressive avec les heures voisines du même régime
                merged = [pool]
                for w in range(1, 6):
                    for hh in (h - w, h + w):
                        merged.append(groups.get((hh, r), np.empty(0)))
                    pool = np.concatenate(merged)
                    if len(pool) >= min_obs:
                        used = (h, f"{r}~merged{w}")
                        break
                if len(pool) < min_obs:
                    pool = np.concatenate([groups.get((h, rr), np.empty(0)) for rr in regimes])
                    used = (h, "all")
                if len(pool) < min_obs:
                    pool = d[target].to_numpy()
                    used = (-1, "global")
            classes[used] = np.quantile(pool, grid) if len(pool) else glob
            resolved[key] = used
    n_merged = sum(1 for k, v in resolved.items() if k != v)
    log.info("Marginales %s : %d classes, %d fusionnées (min_obs=%d)", target, len(resolved), n_merged, min_obs)
    return QuantileTable(grid, classes, resolved, n_obs, max_value)


# ------------------------------------------------------------------ option paramétrique (comparaison)
PARAMETRIC_FAMILIES = {"lognorm": stats.lognorm, "gamma": stats.gamma, "weibull_min": stats.weibull_min,
                       "norm": stats.norm, "expon": stats.expon}


def fit_parametric(x: np.ndarray, families: dict | None = None) -> dict:
    """Ajuste des lois décalées sur x + shift (shift = -min(x) + 1) et sélectionne par AIC."""
    families = families or PARAMETRIC_FAMILIES
    x = np.asarray(x, dtype=float)
    shift = -x.min() + 1.0
    y = x + shift
    out = {}
    for name, dist in families.items():
        try:
            if name in ("norm",):
                params = dist.fit(y)
            else:
                params = dist.fit(y, floc=0)
            ll = dist.logpdf(y, *params).sum()
            k = len(params)
            out[name] = {"params": [float(p) for p in params], "aic": float(2 * k - 2 * ll), "shift": float(shift)}
        except Exception as e:  # noqa: BLE001
            out[name] = {"error": str(e)}
    ok = {k: v for k, v in out.items() if "aic" in v}
    best = min(ok, key=lambda k: ok[k]["aic"]) if ok else None
    return {"fits": out, "best": best}


def sample_parametric(fit_result: dict, n: int, rng: np.random.Generator) -> np.ndarray:
    best = fit_result["best"]
    p = fit_result["fits"][best]
    return PARAMETRIC_FAMILIES[best].rvs(*p["params"], size=n, random_state=rng) - p["shift"]
