"""Analyse exploratoire du jeu BTS au hub : figures et tableaux descriptifs pour l'article.

Usage : python -m delaygen.analysis.eda [--hub CLT]
Sorties : results/eda/*.png, results/eda/*.csv, results/eda/eda_summary.json
"""
from __future__ import annotations

import json
import logging
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  
import numpy as np  
import pandas as pd  
import seaborn as sns  

from delaygen.config import load_config  

log = logging.getLogger(__name__)
sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
PALETTE = {"normal": "#2a9d8f", "degrade": "#e76f51", "A": "#264653", "D": "#e9c46a"}
CAUSES = ["CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"]
CAUSE_LABELS = {"CarrierDelay": "Compagnie", "WeatherDelay": "Météo (extrême)", "NASDelay": "NAS (ATC/météo)",
                "SecurityDelay": "Sûreté", "LateAircraftDelay": "Avion en retard (réactionnel)"}


def _save(fig, out_dir, name):
    p = os.path.join(out_dir, name)
    fig.savefig(p + ".png", dpi=200, bbox_inches="tight")
    fig.savefig(p + ".pdf", bbox_inches="tight")
    plt.close(fig)
    log.info("figure %s", p)


def descriptive_table(flights: pd.DataFrame, rot: pd.DataFrame, hub: str, prepare_report: dict) -> pd.DataFrame:
    rows = []
    for split, yrs in [("train (2023)", [2023]), ("test (2024)", [2024]), ("total", [2023, 2024])]:
        f = flights[flights.FlightDate.dt.year.isin(yrs)]
        r = rot[rot.date.dt.year.isin(yrs)]
        full = r[(~r.open_rotation) & (~r.first_departure)]
        rows.append({
            "Période": split, "Vols (arr.+dép.)": len(f), "Arrivées": int((f.Dest == hub).sum()),
            "Jours": f.FlightDate.nunique(), "Arrivées/jour": round((f.Dest == hub).sum() / f.FlightDate.nunique(), 1),
            "Compagnies": f.Reporting_Airline.nunique(), "Immatriculations": f.Tail_Number.nunique(),
            "Rotations appariées": len(full), "Taux d'appariement (%)": round(100 * len(full) / max((f.Dest == hub).sum(), 1), 1),
            "Retard arr. moyen (min)": round(f.loc[f.Dest == hub, "ArrDelay"].mean(), 1),
            "Arrivées > 15 min (%)": round(100 * (f.loc[f.Dest == hub, "ArrDelay"] > 15).mean(), 1),
            "Q95 retard arr. (min)": round(f.loc[f.Dest == hub, "ArrDelay"].quantile(0.95), 0),
            "Jours dégradés": int(r.groupby("date").regime.first().eq("degrade").sum()),
        })
    return pd.DataFrame(rows).set_index("Période").T


def run(cfg: dict | None = None, hub: str | None = None) -> dict:
    cfg = cfg or load_config()
    hub = hub or cfg["hub"]
    proc = cfg["paths"]["processed"]
    out_dir = os.path.join(cfg["paths"]["results"], "eda")
    os.makedirs(out_dir, exist_ok=True)
    flights = pd.read_parquet(os.path.join(proc, f"flights_clean_{hub}.parquet"))
    rot = pd.read_parquet(os.path.join(proc, f"rotations_{hub}.parquet"))
    regime = pd.read_parquet(os.path.join(proc, f"regime_{hub}.parquet"))
    with open(os.path.join(proc, f"prepare_report_{hub}.json"), encoding="utf-8") as fh:
        prep = json.load(fh)
    arr = flights[flights.Dest == hub].copy()
    dep = flights[flights.Origin == hub].copy()
    arr["hour"] = (arr.CRSArrTime_min // 60).clip(0, 23).astype(int)
    dep["hour"] = (dep.CRSDepTime_min // 60).clip(0, 23).astype(int)
    arr = arr.merge(regime[["date", "regime"]], left_on="FlightDate", right_on="date", how="left")
    full = rot[(~rot.open_rotation) & (~rot.first_departure)].copy()
    summary = {"hub": hub}

    # T0 — tableau descriptif
    t0 = descriptive_table(flights, rot, hub, prep)
    t0.to_csv(os.path.join(out_dir, "T0_dataset_description.csv"))
    t0.to_latex(os.path.join(out_dir, "T0_dataset_description.tex"), escape=True)

    # F-EDA1 — distributions de A et D (queue lourde)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    for ax, col, lab, c in [(axes[0], arr.ArrDelay, "Retard d'arrivée A (min)", PALETTE["A"]),
                            (axes[1], dep.DepDelay, "Retard de départ D (min)", PALETTE["D"])]:
        x = col.clip(-60, 240)
        ax.hist(x, bins=150, color=c, alpha=0.85, density=True)
        ax.axvline(15, color="k", ls="--", lw=1)
        ax.set_yscale("log")
        ax.set_xlabel(lab); ax.set_ylabel("densité (log)")
        ax.set_title(f"moyenne {col.mean():.1f} min · médiane {col.median():.0f} · > 15 min : {100*(col>15).mean():.1f} % · Q95 {col.quantile(.95):.0f}", fontsize=9)
    _save(fig, out_dir, "F_eda1_delay_distributions")
    summary["A"] = {"mean": float(arr.ArrDelay.mean()), "median": float(arr.ArrDelay.median()), "std": float(arr.ArrDelay.std()),
                    "share_gt15": float((arr.ArrDelay > 15).mean()), "q95": float(arr.ArrDelay.quantile(.95)), "q99": float(arr.ArrDelay.quantile(.99)),
                    "share_early": float((arr.ArrDelay < 0).mean())}
    summary["D"] = {"mean": float(dep.DepDelay.mean()), "median": float(dep.DepDelay.median()), "std": float(dep.DepDelay.std()),
                    "share_gt15": float((dep.DepDelay > 15).mean()), "q95": float(dep.DepDelay.quantile(.95))}

    # F-EDA2 — profil horaire : trafic programmé (banques) + retard moyen par heure
    ha = arr.groupby("hour").agg(n=("ArrDelay", "size"), meanA=("ArrDelay", "mean"), q90=("ArrDelay", lambda s: s.quantile(.9)))
    hd = dep.groupby("hour").agg(n=("DepDelay", "size"), meanD=("DepDelay", "mean"))
    ndays = arr.FlightDate.nunique()
    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.bar(ha.index - 0.2, ha.n / ndays, width=0.4, color=PALETTE["A"], alpha=.8, label="arrivées / jour")
    ax1.bar(hd.index + 0.2, hd.n / ndays, width=0.4, color=PALETTE["D"], alpha=.8, label="départs / jour")
    ax1.set_xlabel("heure programmée (locale)"); ax1.set_ylabel("mouvements par jour")
    ax2 = ax1.twinx()
    ax2.plot(ha.index, ha.meanA, "o-", color="#e76f51", label="retard moyen arrivée")
    ax2.plot(hd.index, hd.meanD, "s--", color="#9b2226", label="retard moyen départ")
    ax2.set_ylabel("retard moyen (min)")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    ax1.set_xticks(range(0, 24, 2))
    _save(fig, out_dir, "F_eda2_hourly_profile")
    ha.join(hd, lsuffix="_arr", rsuffix="_dep").to_csv(os.path.join(out_dir, "hourly_profile.csv"))

    # F-EDA3 — saisonnalité mensuelle et jours dégradés
    arr["month"] = arr.FlightDate.dt.to_period("M").astype(str)
    mo = arr.groupby("month").agg(meanA=("ArrDelay", "mean"), gt15=("ArrDelay", lambda s: 100 * (s > 15).mean()))
    reg_m = regime.assign(month=regime.date.dt.to_period("M").astype(str)).groupby("month").regime.apply(lambda s: (s == "degrade").sum())
    fig, ax = plt.subplots(figsize=(11, 3.8))
    ax.bar(mo.index, reg_m.reindex(mo.index).fillna(0), color=PALETTE["degrade"], alpha=.5, label="jours en régime dégradé")
    ax.set_ylabel("jours dégradés / mois")
    ax2 = ax.twinx()
    ax2.plot(mo.index, mo.meanA, "o-", color=PALETTE["A"], label="retard moyen d'arrivée")
    ax2.plot(mo.index, mo.gt15, "s--", color="#9b2226", label="% arrivées > 15 min")
    ax2.set_ylabel("min  /  %")
    ax.tick_params(axis="x", rotation=60, labelsize=8)
    ax.axvline(11.5, color="k", lw=1); ax.text(11.6, ax.get_ylim()[1] * .92, "train | test", fontsize=8)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    _save(fig, out_dir, "F_eda3_monthly_seasonality")

    # F-EDA4 — décomposition des causes de retard (part des minutes) : motive la propagation
    late = arr[arr.ArrDelay >= 15]
    shares = late[CAUSES].fillna(0).sum()
    shares = shares / shares.sum() * 100
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.barh([CAUSE_LABELS[c] for c in CAUSES], shares.values, color=["#8ecae6", "#219ebc", "#023047", "#ffb703", "#fb8500"])
    for i, v in enumerate(shares.values):
        ax.text(v + 0.5, i, f"{v:.1f} %", va="center", fontsize=9)
    ax.set_xlabel("part des minutes de retard (arrivées ≥ 15 min)")
    ax.set_xlim(0, max(shares.values) * 1.2)
    _save(fig, out_dir, "F_eda4_delay_causes")
    summary["cause_shares_pct"] = {k: float(v) for k, v in shares.items()}

    # F-EDA5 — propagation : E[D | A] et densité conjointe
    bins = [-np.inf, -15, 0, 15, 30, 45, 60, 90, 120, np.inf]
    labels = ["<-15", "-15–0", "0–15", "15–30", "30–45", "45–60", "60–90", "90–120", ">120"]
    full["A_bin"] = pd.cut(full.A, bins, labels=labels)
    ed = full.groupby("A_bin", observed=True).agg(n=("D", "size"), mean_D=("D", "mean"), median_D=("D", "median"),
                                                  q90_D=("D", lambda s: s.quantile(.9)), share_D_gt15=("D", lambda s: (s > 15).mean()))
    ed.to_csv(os.path.join(out_dir, "T_eda_conditional_departure.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    sub = full.sample(min(60000, len(full)), random_state=0)
    axes[0].hexbin(sub.A.clip(-40, 180), sub.D.clip(-20, 200), gridsize=60, bins="log", cmap="viridis")
    axes[0].plot([0, 180], [0, 180], "w--", lw=1)
    axes[0].set_xlabel("retard d'arrivée A (min)"); axes[0].set_ylabel("retard de départ D (min)")
    axes[0].set_title("densité conjointe (log), rotations appariées")
    axes[1].plot(labels, ed.mean_D, "o-", label="E[D | A]")
    axes[1].plot(labels, ed.median_D, "s--", label="médiane D | A")
    axes[1].plot(labels, ed.q90_D, "^:", label="Q90 D | A")
    axes[1].set_xlabel("classe de retard d'arrivée A (min)"); axes[1].set_ylabel("retard de départ D (min)")
    axes[1].tick_params(axis="x", rotation=45); axes[1].legend(fontsize=8)
    _save(fig, out_dir, "F_eda5_propagation_E_D_given_A")
    summary["E_D_given_A"] = ed.reset_index().astype(str).to_dict(orient="records")

    # F-EDA6 — temps au sol programmé par catégorie (MTT) et slack
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for cat, c in [("RJ", "#8ecae6"), ("NB", "#219ebc"), ("WB", "#fb8500")]:
        g = full.loc[full.category == cat, "ground_sched"].clip(0, 400)
        if len(g) > 100:
            sns.kdeplot(g, ax=ax, label=f"{cat} (n={len(g):,}, Q5={np.quantile(g, .05):.0f} min)", color=c, fill=True, alpha=.25)
            tight = full.loc[(full.category == cat) & (full.A >= 30), "ground_sched"]
            if len(tight) > 50:
                ax.axvline(np.quantile(tight, .05), color=c, ls="--", lw=1.2)
    ax.set_xlabel("temps au sol programmé d_i − a_i (min) ; tirets : MTT = Q5 sur rotations avec A ≥ 30")
    ax.set_xlim(0, 400); ax.legend(fontsize=8)
    _save(fig, out_dir, "F_eda6_ground_time_by_category")

    # F-EDA7 — retards par régime météo (repli BTS) : boxplot A par régime et par heure
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1, 2.2]})
    sns.boxplot(data=arr, x="regime", y=arr.ArrDelay.clip(-30, 150), hue="regime", palette=PALETTE, ax=axes[0], showfliers=False, legend=False)
    axes[0].set_xlabel("régime journalier"); axes[0].set_ylabel("retard d'arrivée A (min)")
    hr = arr.groupby(["regime", "hour"]).ArrDelay.mean().unstack(0)
    for r in hr.columns:
        axes[1].plot(hr.index, hr[r], "o-", color=PALETTE.get(r, "k"), label=r)
    axes[1].set_xlabel("heure programmée"); axes[1].set_ylabel("retard moyen d'arrivée (min)"); axes[1].legend(title="régime")
    _save(fig, out_dir, "F_eda7_regime_effect")
    summary["A_by_regime"] = arr.groupby("regime").ArrDelay.agg(["mean", "median", lambda s: (s > 15).mean(), "size"]).rename(columns={"<lambda_0>": "share_gt15"}).to_dict()

    # F-EDA8 — heatmap heure x mois du retard moyen
    hm = arr.pivot_table(index="hour", columns="month", values="ArrDelay", aggfunc="mean")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(hm, cmap="RdYlGn_r", center=10, ax=ax, cbar_kws={"label": "retard moyen d'arrivée (min)"})
    ax.set_xlabel("mois"); ax.set_ylabel("heure programmée")
    _save(fig, out_dir, "F_eda8_heatmap_hour_month")

    # F-EDA9 — sur-dispersion du nombre de retards (>15) par heure : observé vs binomiale indépendante
    late_h = arr.assign(late=arr.ArrDelay > 15).groupby(["FlightDate", "hour"]).agg(n=("late", "size"), k=("late", "sum"))
    p = late_h.k.sum() / late_h.n.sum()
    late_h["var_binom"] = late_h.n * p * (1 - p)
    obs_var = late_h.groupby("hour").k.var(); exp_var = late_h.groupby("hour").var_binom.mean()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(obs_var.index, obs_var, "o-", label="variance observée du nb de retards/heure")
    ax.plot(exp_var.index, exp_var, "s--", label="variance sous indépendance (binomiale)")
    ax.set_xlabel("heure programmée"); ax.set_ylabel("variance"); ax.legend(fontsize=8)
    ax.set_title(f"indice de dispersion moyen = {float((obs_var / exp_var).mean()):.1f} (1 = indépendance)", fontsize=9)
    _save(fig, out_dir, "F_eda9_overdispersion")
    summary["dispersion_index_hourly_late_counts"] = float((obs_var / exp_var).mean())

    # F-EDA10 — corrélation journalière : part de jours, distribution du retard moyen journalier
    dm = arr.groupby("FlightDate").ArrDelay.mean()
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.hist(dm, bins=50, color=PALETTE["A"], alpha=.85)
    ax.axvline(prep.get("regime_thresholds", {}).get("mean_delay_q", dm.quantile(.8)), color=PALETTE["degrade"], ls="--", label="seuil régime dégradé (Q80 train)")
    ax.set_xlabel("retard moyen d'arrivée du jour (min)"); ax.set_ylabel("jours"); ax.legend(fontsize=8)
    _save(fig, out_dir, "F_eda10_daily_mean_delay")
    summary["daily_mean_delay"] = {"std": float(dm.std()), "q80": float(dm.quantile(.8)), "max": float(dm.max()),
                                   "lag1_autocorr": float(dm.autocorr(1))}

    # F-EDA11 — parts compagnie et catégorie ; parts région d'origine
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    arr.Reporting_Airline.value_counts(normalize=True).head(8).mul(100).plot.bar(ax=axes[0], color="#219ebc")
    axes[0].set_ylabel("% des arrivées"); axes[0].set_xlabel("compagnie (code IATA)")
    rot.category.value_counts(normalize=True).mul(100).plot.bar(ax=axes[1], color="#fb8500")
    axes[1].set_ylabel("% des rotations"); axes[1].set_xlabel("catégorie d'avion (FAA)")
    rot.origin_region.value_counts(normalize=True).mul(100).plot.bar(ax=axes[2], color="#2a9d8f")
    axes[2].set_ylabel("% des arrivées"); axes[2].set_xlabel("région d'origine")
    for ax in axes:
        ax.tick_params(axis="x", rotation=45)
    _save(fig, out_dir, "F_eda11_carrier_category_region")
    summary["carrier_share"] = arr.Reporting_Airline.value_counts(normalize=True).head(8).round(4).to_dict()
    summary["category_share"] = rot.category.value_counts(normalize=True).round(4).to_dict()

    # F-EDA12 — part du retard réactionnel (LateAircraftDelay) dans le retard de départ, par heure
    dep_l = dep[dep.DepDelay >= 15]
    sh = dep_l.groupby("hour")[CAUSES].sum()
    sh = sh.div(sh.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(9, 3.8))
    sh.rename(columns=CAUSE_LABELS).plot.area(ax=ax, alpha=.85, color=["#8ecae6", "#219ebc", "#023047", "#ffb703", "#fb8500"])
    ax.set_xlabel("heure de départ programmée"); ax.set_ylabel("% des minutes de retard de départ"); ax.legend(fontsize=7, loc="lower left")
    ax.set_ylim(0, 100)
    _save(fig, out_dir, "F_eda12_causes_by_hour")

    summary["prepare_report"] = prep
    with open(os.path.join(out_dir, "eda_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    log.info("EDA terminée -> %s", out_dir)
    return summary


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default=None)
    a = ap.parse_args()
    run(hub=a.hub)
