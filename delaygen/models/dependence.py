"""M3 — Copule gaussienne à facteurs : scores normaux, estimation des lambda par la méthode des moments,
tirage des scores pour une journée."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

log = logging.getLogger(__name__)

FACTORS = ["d", "h", "c", "r"]  # jour, heure-bloc, compagnie, région


def normal_scores(df: pd.DataFrame, class_cols: list[str], target: str) -> pd.Series:
    """S_i = Phi^{-1}((rang_i - 0.5) / n_k) au sein de chaque classe k."""
    d = df[class_cols + [target]].dropna()
    rank = d.groupby(class_cols)[target].rank(method="average")
    n = d.groupby(class_cols)[target].transform("size")
    s = stats.norm.ppf((rank - 0.5) / n)
    return pd.Series(s, index=d.index, name="S")


def _pairs_for_day(idx: np.ndarray, rng: np.random.Generator, max_pairs: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(idx)
    total = n * (n - 1) // 2
    if total <= max_pairs:
        iu = np.triu_indices(n, k=1)
        return idx[iu[0]], idx[iu[1]]
    i = rng.integers(0, n, size=max_pairs)
    j = rng.integers(0, n, size=max_pairs)
    m = i != j
    return idx[i[m]], idx[j[m]]


def fit_moments(df: pd.DataFrame, S: pd.Series, date_col: str = "date", hour_col: str = "hour_block_arr",
                carrier_col: str = "carrier", region_col: str = "origin_region", max_pairs_per_day: int = 20000,
                seed: int = 0) -> dict:
    """Régression de S_i*S_j sur les indicatrices 'même heure', 'même compagnie', 'même région'
    (paires du même jour). Constante -> lambda_d^2 ; coefficients -> lambda_h^2, lambda_c^2, lambda_r^2."""
    rng = np.random.default_rng(seed)
    d = df.loc[S.index, [date_col, hour_col, carrier_col, region_col]].copy()
    d["S"] = S.to_numpy()
    X_parts, y_parts = [], []
    for _, g in d.groupby(date_col, sort=False):
        if len(g) < 2:
            continue
        idx = np.arange(len(g))
        i, j = _pairs_for_day(idx, rng, max_pairs_per_day)
        s = g["S"].to_numpy()
        h = g[hour_col].to_numpy()
        c = g[carrier_col].to_numpy().astype(str)
        r = g[region_col].to_numpy().astype(str)
        y_parts.append(s[i] * s[j])
        X_parts.append(np.column_stack([np.ones(len(i)), h[i] == h[j], c[i] == c[j], r[i] == r[j]]).astype(float))
    X = np.vstack(X_parts)
    y = np.concatenate(y_parts)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    lam2 = np.clip(beta, 0, None)
    total = lam2.sum()
    if total > 0.95:  # garde une part idiosyncratique minimale
        lam2 = lam2 * 0.95 / total
    lam = np.sqrt(lam2)
    sigma_eps = float(np.sqrt(max(1.0 - lam2.sum(), 0.0)))
    out = {"lambda_d": float(lam[0]), "lambda_h": float(lam[1]), "lambda_c": float(lam[2]), "lambda_r": float(lam[3]),
           "sigma_eps": sigma_eps, "n_pairs": int(len(y)), "raw_beta": beta.tolist()}
    log.info("Copule facteurs : %s", {k: round(v, 3) for k, v in out.items() if isinstance(v, float)})
    return out


def fit_mixedlm(df: pd.DataFrame, S: pd.Series, date_col="date", hour_col="hour_block_arr",
                carrier_col="carrier", region_col="origin_region") -> dict:
    """Contrôle : modèle mixte à effets aléatoires croisés (variance components) via statsmodels."""
    import statsmodels.formula.api as smf
    d = df.loc[S.index, [date_col, hour_col, carrier_col, region_col]].copy()
    d["S"] = S.to_numpy()
    d["day"] = d[date_col].astype(str)
    d["dh"] = d["day"] + "_" + d[hour_col].astype(str)
    d["dc"] = d["day"] + "_" + d[carrier_col].astype(str)
    d["dr"] = d["day"] + "_" + d[region_col].astype(str)
    md = smf.mixedlm("S ~ 1", d, groups="day", re_formula="1", vc_formula={"dh": "0 + C(dh)", "dc": "0 + C(dc)", "dr": "0 + C(dr)"})
    res = md.fit(reml=True, method="lbfgs", maxiter=200)
    vd = float(res.cov_re.iloc[0, 0])
    vc = {k: float(v) for k, v in res.vcomp_names and zip(res.vcomp_names, res.vcomp)} if hasattr(res, "vcomp") else {}
    tot = vd + sum(vc.values()) + float(res.scale)
    return {"lambda_d": np.sqrt(vd / tot), "lambda_h": np.sqrt(vc.get("dh", 0) / tot),
            "lambda_c": np.sqrt(vc.get("dc", 0) / tot), "lambda_r": np.sqrt(vc.get("dr", 0) / tot),
            "sigma_eps": np.sqrt(res.scale / tot)}


def scale_lambdas(params: dict, correlation_scale: float) -> dict:
    """Multiplie les lambda par un facteur et renormalise (correlation_scale = 0 -> indépendance)."""
    lam = np.array([params["lambda_d"], params["lambda_h"], params["lambda_c"], params["lambda_r"]]) * correlation_scale
    lam2 = lam ** 2
    if lam2.sum() > 0.99:
        lam = lam * np.sqrt(0.99 / lam2.sum())
        lam2 = lam ** 2
    return {"lambda_d": float(lam[0]), "lambda_h": float(lam[1]), "lambda_c": float(lam[2]), "lambda_r": float(lam[3]),
            "sigma_eps": float(np.sqrt(1 - lam2.sum()))}


def sample_scores(day: pd.DataFrame, params: dict, rng: np.random.Generator, n_scenarios: int,
                  hour_col: str = "hour_block_arr", carrier_col: str = "carrier",
                  region_col: str = "origin_region") -> tuple[np.ndarray, dict]:
    """Scores S (n_scenarios x n_rotations) pour une journée programmée. Retourne aussi les facteurs
    partagés (Z_d, Z_h par heure) réutilisés par M5."""
    n = len(day)
    h_codes, h_idx = np.unique(day[hour_col].to_numpy(), return_inverse=True)
    c_codes, c_idx = np.unique(day[carrier_col].astype(str).to_numpy(), return_inverse=True)
    r_codes, r_idx = np.unique(day[region_col].astype(str).to_numpy(), return_inverse=True)
    Z_d = rng.standard_normal((n_scenarios, 1))
    Z_h = rng.standard_normal((n_scenarios, len(h_codes)))
    Z_c = rng.standard_normal((n_scenarios, len(c_codes)))
    Z_r = rng.standard_normal((n_scenarios, len(r_codes)))
    eps = rng.standard_normal((n_scenarios, n))
    S = (params["lambda_d"] * Z_d + params["lambda_h"] * Z_h[:, h_idx] + params["lambda_c"] * Z_c[:, c_idx]
         + params["lambda_r"] * Z_r[:, r_idx] + params["sigma_eps"] * eps)
    return S, {"Z_d": Z_d, "Z_h": Z_h, "h_codes": h_codes}
