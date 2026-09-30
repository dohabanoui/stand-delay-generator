"""Validation opérationnelle (niveau 3) : conflits de stands réels vs générés, détection des jours de pointe."""
from __future__ import annotations

import numpy as np
import pandas as pd


def summarize_day(real_metrics: pd.DataFrame, gen_metrics: dict[str, pd.DataFrame]) -> dict:
    """real_metrics : 1 ligne (rejeu sur horaires réels) ; gen_metrics : générateur -> DataFrame (scénarios)."""
    row = {"real_conflicts": float(real_metrics["conflicts"].iloc[0]),
           "real_overlap": float(real_metrics["overlap_minutes"].iloc[0]),
           "real_reassignments": float(real_metrics["reassignments"].iloc[0]),
           "real_waiting_minutes": float(real_metrics["waiting_minutes"].iloc[0])}
    for g, m in gen_metrics.items():
        row[f"{g}_conflicts_mean"] = float(m["conflicts"].mean())
        row[f"{g}_conflicts_median"] = float(m["conflicts"].median())
        row[f"{g}_conflicts_q90"] = float(m["conflicts"].quantile(.9))
        row[f"{g}_overlap_mean"] = float(m["overlap_minutes"].mean())
        row[f"{g}_reassignments_mean"] = float(m["reassignments"].mean())
        row[f"{g}_waiting_minutes_mean"] = float(m["waiting_minutes"].mean())
        # probabilité que le scénario dépasse le réel (calibration)
        row[f"{g}_p_ge_real"] = float((m["conflicts"] >= row["real_conflicts"]).mean())
    return row


def aggregate(days: pd.DataFrame, generators: list[str], peak_quantile: float = 0.9) -> pd.DataFrame:
    """Tableau T3 : par générateur, conflits/jour moyens, écart au réel (%), chevauchement, réaffectations,
    attente, taux de détection des jours de pointe (jour réel avec conflits > Q90 ; détecté si la médiane
    des scénarios dépasse le seuil), corrélation jour à jour, couverture de l'intervalle [Q5, Q95]."""
    from scipy import stats
    thr = days["real_conflicts"].quantile(peak_quantile)
    peak = days["real_conflicts"] > thr
    rows = []
    real_mean = days["real_conflicts"].mean()
    for g in generators:
        cm = days[f"{g}_conflicts_mean"]
        med = days[f"{g}_conflicts_median"]
        # AUC : capacité du score « médiane des scénarios » à classer les jours de pointe (seuil Q90 réel)
        auc = np.nan
        if peak.any() and (~peak).any() and med.std() > 0:
            auc = float(stats.mannwhitneyu(med[peak], med[~peak]).statistic / (peak.sum() * (~peak).sum()))
        rows.append({
            "generator": g,
            "conflicts_per_day_real": real_mean,
            "conflicts_per_day_gen": cm.mean(),
            "bias_pct": 100 * (cm.mean() - real_mean) / real_mean if real_mean else np.nan,
            "mae_daily": (cm - days["real_conflicts"]).abs().mean(),
            "corr_daily": float(np.corrcoef(cm, days["real_conflicts"])[0, 1]) if cm.std() > 0 else np.nan,
            "spearman_daily": float(stats.spearmanr(cm, days["real_conflicts"]).statistic) if cm.std() > 0 else np.nan,
            "peak_auc": auc,
            "overlap_real": days["real_overlap"].mean(), "overlap_gen": days[f"{g}_overlap_mean"].mean(),
            "reassign_real": days["real_reassignments"].mean(), "reassign_gen": days[f"{g}_reassignments_mean"].mean(),
            "waiting_real": days["real_waiting_minutes"].mean(), "waiting_gen": days[f"{g}_waiting_minutes_mean"].mean(),
            "peak_days": int(peak.sum()),
            "peak_detection_rate": float((days.loc[peak, f"{g}_conflicts_median"] > thr).mean()) if peak.any() else np.nan,
            "peak_false_alarm_rate": float((days.loc[~peak, f"{g}_conflicts_median"] > thr).mean()),
            "coverage_real_in_scenarios": float(days[f"{g}_p_ge_real"].between(0.05, 0.95).mean()),
            "real_above_all_scenarios": float((days[f"{g}_p_ge_real"] == 0).mean()),
        })
    return pd.DataFrame(rows)
