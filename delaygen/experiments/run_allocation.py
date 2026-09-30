"""E3 — Impact opérationnel : allocation MILP (buffers 0 / 15), rejeu réel vs scénarios (T3, T3b, F2, F2b, F4).

Deux modes de génération sont évalués pour chaque jour test :
  - unconditional : le régime météo est tiré par le générateur (loi stationnaire) ;
  - conditioned   : le régime est forcé au régime réel du jour (équivalent d'une prévision météo J-1 connue).

Usage : python -m delaygen.experiments.run_allocation [--every 3] [--n-scenarios 100] [--buffers 0 15]
"""
from __future__ import annotations

import argparse
import logging
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from delaygen import baselines  # noqa: E402
from delaygen.allocation import instance, milp, replay  # noqa: E402
from delaygen.experiments.common import day_schedule, dump_json, load_all, real_times, setup_logging, test_days, write_table  # noqa: E402
from delaygen.validation import operational  # noqa: E402

log = logging.getLogger(__name__)
GENS = baselines.GENERATORS
MODES = ["unconditional", "conditioned"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--hub", default=None)
    ap.add_argument("--n-scenarios", type=int, default=100)
    ap.add_argument("--n-recourse", type=int, default=20)
    ap.add_argument("--every", type=int, default=3)
    ap.add_argument("--max-days", type=int, default=None)
    ap.add_argument("--buffers", type=float, nargs="+", default=[0, 15])
    ap.add_argument("--time-limit", type=float, default=None)
    ap.add_argument("--gantt-date", default=None)
    ap.add_argument("--reaggregate", action="store_true", help="recalcule T3/T3b/F2 depuis daily_operational_metrics.csv sans relancer")
    a = ap.parse_args()
    setup_logging()
    cfg, hub, rot, params = load_all(a.config, a.hub)
    al = cfg["allocation"]
    tl = a.time_limit or al["time_limit_s"]
    out_dir = os.path.join(cfg["paths"]["results"], "allocation")
    fig_dir = os.path.join(cfg["paths"]["results"], "figures")
    os.makedirs(out_dir, exist_ok=True); os.makedirs(fig_dir, exist_ok=True)
    days = test_days(rot, a.every, a.max_days, cfg=cfg)
    seed0 = cfg["generation"]["seed"]
    if a.reaggregate:
        days_df = pd.read_csv(os.path.join(out_dir, "daily_operational_metrics.csv"), parse_dates=["date"])
        a.buffers = sorted(days_df.buffer.unique())
        _tables_and_figures(days_df, a, out_dir, fig_dir, {}, rot, params, cfg, seed0, tl, days, [])
        return
    log.info("%d jours, buffers %s, %d scénarios, modes %s", len(days), a.buffers, a.n_scenarios, MODES)

    rows, solve_rows = [], []
    scen_cache = {}
    for di, date in enumerate(days):
        day = day_schedule(rot, date)
        regime_real = str(day.regime.iloc[0])
        stands = instance.build(day, None, al["target_peak_occupancy"], al["stand_shares"], seed=di)
        a_r, d_r = real_times(day)
        gens_out = {"unconditional": {g: baselines.run(g, day, params, a.n_scenarios, seed0 + di) for g in GENS},
                    "conditioned": {g: baselines.run(g, day, params, a.n_scenarios, seed0 + di, forced_regime=regime_real) for g in GENS}}
        for b in a.buffers:
            sol = milp.solve(day, stands, b, tl, seed=di)
            solve_rows.append({"date": date, "buffer": b, "status": sol["status"], "runtime": sol["runtime"],
                               "n_stands": sol["n_stands"], "n_rotations": len(day), "n_unassigned": sol["n_unassigned"],
                               "objective": sol["objective"]})
            if not sol["allocation"]:
                log.warning("%s b=%s : pas de solution (%s)", date, b, sol["status"]); continue
            real_m = replay.evaluate(day, stands, sol["allocation"], a_r, d_r, al["b_ops"], n_recourse=1)
            for mode in MODES:
                gen_m = {g: replay.evaluate(day, stands, sol["allocation"], o["a_real"], o["d_real"], al["b_ops"], a.n_recourse)
                         for g, o in gens_out[mode].items()}
                row = operational.summarize_day(real_m, gen_m)
                row.update(date=date, buffer=b, mode=mode, n_stands=len(stands), n_rotations=len(day), regime=regime_real,
                           peak_occupancy=instance.peak_occupancy(day), n_unassigned=sol["n_unassigned"])
                rows.append(row)
                if b == a.buffers[0]:
                    scen_cache[(date, mode)] = {g: gen_m[g]["conflicts"].to_numpy() for g in GENS}
        if di % 10 == 0:
            r = [x for x in rows if x["date"] == date and x["buffer"] == a.buffers[0] and x["mode"] == "conditioned"]
            if r:
                log.info("jour %d/%d (%s, %s) : réel %.0f | proposé %.1f | indépendant %.1f | MILP %.1fs",
                         di + 1, len(days), pd.Timestamp(date).date(), regime_real, r[0]["real_conflicts"],
                         r[0]["proposed_conflicts_mean"], r[0]["independent_conflicts_mean"], solve_rows[-len(a.buffers)]["runtime"])

    days_df = pd.DataFrame(rows)
    days_df.to_csv(os.path.join(out_dir, "daily_operational_metrics.csv"), index=False)
    pd.DataFrame(solve_rows).to_csv(os.path.join(out_dir, "milp_solve_log.csv"), index=False)
    _tables_and_figures(days_df, a, out_dir, fig_dir, scen_cache, rot, params, cfg, seed0, tl, days, solve_rows)


def _tables_and_figures(days_df, a, out_dir, fig_dir, scen_cache, rot, params, cfg, seed0, tl, days, solve_rows):
    # ---------------- T3 par (mode, buffer)
    t3_all = []
    for mode in MODES:
        for b in a.buffers:
            sub = days_df[(days_df.buffer == b) & (days_df["mode"] == mode)]
            if sub.empty:
                continue
            t3 = operational.aggregate(sub, GENS)
            t3.insert(0, "buffer", b); t3.insert(0, "mode", mode); t3_all.append(t3)
    t3_all = pd.concat(t3_all, ignore_index=True)
    t3_all["generator_label"] = t3_all.generator.map(baselines.LABELS)
    write_table(t3_all, out_dir, "T3_operational_impact", "%.2f",
                caption="E3 — Impact opérationnel : conflits de stands réels vs générés (période test)", label="tab:T3")

    # ---------------- T3b : tableau « avant / après » (buffer 0), un bloc par mode
    for mode in MODES:
        b0 = t3_all[(t3_all.buffer == a.buffers[0]) & (t3_all["mode"] == mode)].set_index("generator")
        if b0.empty:
            continue
        real_row = b0.iloc[0]
        ba = pd.DataFrame({
            f"Indicateur (b = {a.buffers[0]:g} min, moyenne par jour)": ["Conflits de stands / jour", "Écart au réel (%)", "MAE journalière (conflits)",
                                                     "Corrélation jour à jour avec le réel", "Spearman jour à jour",
                                                     "AUC détection des jours de pointe (Q90)", "Minutes de chevauchement / jour",
                                                     "Réaffectations / jour", "Réel dans [Q5, Q95] des scénarios",
                                                     "Jours où le réel dépasse tous les scénarios"],
            "Réel (BTS 2024)": [real_row.conflicts_per_day_real, 0, 0, 1, 1, 1, real_row.overlap_real, real_row.reassign_real, 1, 0],
            "Avant : indépendant": _col(b0.loc["independent"]),
            "Avant : heure+région (≈ Dijk et al.)": _col(b0.loc["hour_region"]),
            "Après : proposé sans propagation": _col(b0.loc["proposed_noprop"]),
            "Après : proposé complet": _col(b0.loc["proposed"]),
        })
        write_table(ba, out_dir, f"T3b_before_after_{mode}", "%.2f",
                    caption=f"Avant / après — impact opérationnel (mode {mode}, b = {a.buffers[0]:g} min)", label=f"tab:T3b_{mode}")

    # ---------------- F2 : conflits par jour, réel vs générateurs (b = 0), deux modes
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for r_, mode in enumerate(MODES):
        d0 = days_df[(days_df.buffer == a.buffers[0]) & (days_df["mode"] == mode)]
        if d0.empty:
            continue
        hi = max(d0.real_conflicts.max(), d0[[f"{g}_conflicts_mean" for g in GENS]].max().max())
        bins = np.arange(0, hi + 3, max(1, int(hi // 30)))
        ax = axes[r_, 0]
        ax.hist(d0.real_conflicts, bins=bins, histtype="stepfilled", alpha=.35, color="k", label="Réel")
        for g in GENS:
            ax.hist(d0[f"{g}_conflicts_mean"], bins=bins, histtype="step", lw=1.6, label=baselines.LABELS[g])
        ax.set_xlabel(f"conflits de stands par jour (b = {a.buffers[0]:g} min)"); ax.set_ylabel("jours"); ax.set_title(f"mode : {mode}", fontsize=10)
        ax.legend(fontsize=7)
        ax = axes[r_, 1]
        for g, mk in zip(GENS, ["x", "+", "^", "o"]):
            ax.plot(d0.real_conflicts, d0[f"{g}_conflicts_mean"], mk, ms=4, alpha=.7, label=baselines.LABELS[g])
        lim = [0, d0.real_conflicts.max() * 1.05]
        ax.plot(lim, lim, "k--", lw=1); ax.set_xlabel("conflits réels / jour"); ax.set_ylabel("conflits générés (moyenne des scénarios)")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "F2_conflicts_per_day.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    # ---------------- F2b : jours de pointe réels, distribution des scénarios (mode conditionné)
    d0 = days_df[(days_df.buffer == a.buffers[0]) & (days_df["mode"] == "conditioned")]
    peak_thr = d0.real_conflicts.quantile(.9)
    peaks = d0[d0.real_conflicts > peak_thr].sort_values("real_conflicts", ascending=False).head(12)
    if len(peaks) and not scen_cache:
        # ré-agrégation : on recalcule les scénarios des seuls jours de pointe (allocation + génération conditionnée)
        al = cfg["allocation"]
        for d in peaks.date:
            di = [pd.Timestamp(x) for x in days].index(pd.Timestamp(d))
            day = day_schedule(rot, pd.Timestamp(d))
            stands = instance.build(day, None, al["target_peak_occupancy"], al["stand_shares"], seed=di)
            sol = milp.solve(day, stands, a.buffers[0], tl, seed=di)
            scen_cache[(d, "conditioned")] = {
                g: replay.conflicts(day, sol["allocation"], *[baselines.run(g, day, params, a.n_scenarios, seed0 + di,
                                    forced_regime=str(day.regime.iloc[0]))[k] for k in ("a_real", "d_real")], al["b_ops"])["conflicts"]
                for g in GENS}
    if len(peaks) and scen_cache:
        fig, ax = plt.subplots(figsize=(12, 4))
        pos = np.arange(len(peaks)); w = 0.18
        for k, g in enumerate(GENS):
            data = [scen_cache[(d, "conditioned")][g] for d in peaks.date]
            ax.boxplot(data, positions=pos + (k - 1.5) * w, widths=w * .9, showfliers=False, patch_artist=True,
                       boxprops=dict(facecolor=f"C{k}", alpha=.5), medianprops=dict(color="k"))
        ax.plot(pos, peaks.real_conflicts, "k*", ms=11, label="réel")
        ax.set_xticks(pos); ax.set_xticklabels([pd.Timestamp(d).strftime("%Y-%m-%d") for d in peaks.date], rotation=45, fontsize=8)
        ax.set_ylabel(f"conflits de stands (b = {a.buffers[0]:g} min)")
        ax.set_title("Jours de pointe réels — scénarios (régime conditionné) : " + ", ".join(f"C{k}={g}" for k, g in enumerate(GENS)), fontsize=9)
        ax.legend()
        fig.savefig(os.path.join(fig_dir, "F2b_peak_days_scenarios.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    # ---------------- F4 : Gantt d'une journée
    gd = pd.Timestamp(a.gantt_date) if a.gantt_date else (peaks.date.iloc[0] if len(peaks) else days[0])
    try:
        _gantt(rot, gd, params, cfg, fig_dir, seed0, tl, a.buffers[0])
    except Exception as e:  # noqa: BLE001
        log.warning("Gantt non produit : %s", e)
    if not solve_rows:  # ré-agrégation : F2b (scénarios) non recalculée
        log.info("T3/T3b/F2/F4 recalculés -> %s", out_dir)
        return
    sl = pd.DataFrame(solve_rows)
    dump_json({"n_days": len(days), "buffers": a.buffers, "n_scenarios": a.n_scenarios, "modes": MODES,
               "milp_runtime_mean": float(sl.runtime.mean()), "milp_status": sl.status.value_counts().to_dict(),
               "milp_unassigned_mean": float(sl.n_unassigned.mean()), "stands_mean": float(sl.n_stands.mean()),
               "rotations_mean": float(sl.n_rotations.mean())}, os.path.join(out_dir, "runtime.json"))
    log.info("E3 terminée -> %s", out_dir)


def _col(r):
    return [r.conflicts_per_day_gen, r.bias_pct, r.mae_daily, r.corr_daily, r.spearman_daily, r.peak_auc,
            r.overlap_gen, r.reassign_gen, r.coverage_real_in_scenarios, r.real_above_all_scenarios]


def _gantt(rot, date, params, cfg, fig_dir, seed, tl, buffer_b=5.0):
    al = cfg["allocation"]
    day = day_schedule(rot, date)
    stands = instance.build(day, None, al["target_peak_occupancy"], al["stand_shares"], seed=0)
    sol = milp.solve(day, stands, buffer_b, tl)
    if not sol["allocation"]:
        return
    out = baselines.run("proposed", day, params, 50, seed, forced_regime="degrade")
    s = int(np.argmax(out["D"].sum(axis=1)))
    a_r, d_r = real_times(day)
    sel = stands.stand.iloc[:: max(1, len(stands) // 18)].tolist()[:18]
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    for ax, (title, A, D) in zip(axes, [("Programmé (BTS CRS)", day.a_sched.to_numpy(float), day.d_sched.to_numpy(float)),
                                        ("Réalisé réel (BTS)", a_r, d_r),
                                        ("Scénario généré (régime dégradé, pire des 50)", out["a_real"][s], out["d_real"][s])]):
        for yi, st in enumerate(sel):
            idx = [i for i, r in enumerate(day.rot_id) if sol["allocation"].get(int(r)) == st]
            idx = sorted(idx, key=lambda i: A[i])
            for j, i in enumerate(idx):
                conflict = j > 0 and A[i] < D[idx[j - 1]] + al["b_ops"]
                ax.barh(yi, max(D[i] - A[i], 1), left=A[i], height=.7, color="#e76f51" if conflict else "#2a9d8f", alpha=.85, edgecolor="k", lw=.3)
        ax.set_yticks(range(len(sel))); ax.set_yticklabels(sel, fontsize=7); ax.set_title(title, fontsize=10)
    axes[-1].set_xlabel("minutes depuis minuit (rouge : conflit avec la rotation précédente sur le stand)")
    axes[-1].set_xlim(300, 1500)
    fig.suptitle(f"{cfg['hub']} — {pd.Timestamp(date).date()} — allocation nominale (b = {buffer_b:g} min), {len(sel)} stands sur {len(stands)}", fontsize=10)
    fig.savefig(os.path.join(fig_dir, "F4_gantt_example.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    main()
