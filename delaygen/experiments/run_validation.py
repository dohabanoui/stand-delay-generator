"""E1 (fidélité statistique, T1, F1) et E2 (structure, T2, F3) sur la période test.

Usage : python -m delaygen.experiments.run_validation [--n-scenarios 100] [--every 1] [--max-days N]
"""
from __future__ import annotations

import argparse
import logging
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from delaygen import baselines  # noqa: E402
from delaygen.experiments.common import day_schedule, dump_json, load_all, setup_logging, test_days, write_table  # noqa: E402
from delaygen.validation import statistical, structural  # noqa: E402

log = logging.getLogger(__name__)
GENS = baselines.GENERATORS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--hub", default=None)
    ap.add_argument("--n-scenarios", type=int, default=100)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--max-days", type=int, default=None)
    ap.add_argument("--keep-scenarios", type=int, default=3, help="scénarios conservés par jour pour les QQ-plots")
    a = ap.parse_args()
    setup_logging()
    cfg, hub, rot, params = load_all(a.config, a.hub)
    out_dir = os.path.join(cfg["paths"]["results"], "validation")
    fig_dir = os.path.join(cfg["paths"]["results"], "figures")
    os.makedirs(out_dir, exist_ok=True); os.makedirs(fig_dir, exist_ok=True)
    days = test_days(rot, a.every, a.max_days, cfg=cfg)
    seed0 = cfg["generation"]["seed"]
    log.info("%d jours test, %d scénarios, générateurs %s", len(days), a.n_scenarios, GENS)

    # accumulateurs
    real_A, real_D, real_regime, real_A_full, real_D_full = [], [], [], [], []
    gen_A = {g: [] for g in GENS}; gen_D = {g: [] for g in GENS}; gen_reg = {g: [] for g in GENS}
    gen_A_full = {g: [] for g in GENS}; gen_D_full = {g: [] for g in GENS}; gen_Dreact = {g: [] for g in GENS}
    corr_rows = []; disp_rows = []
    t_gen = {g: 0.0 for g in GENS}
    for di, date in enumerate(days):
        day = day_schedule(rot, date)
        m_arr = (~day.first_departure).to_numpy()            # A observé
        m_full = ((~day.first_departure) & (~day.open_rotation)).to_numpy()  # A et D observés
        A_r = day["A"].to_numpy(dtype=float); D_r = day["D"].to_numpy(dtype=float)
        real_A.append(A_r[m_arr]); real_D.append(D_r[m_full]); real_regime.append(np.full(m_arr.sum(), day.regime.iloc[0]))
        real_A_full.append(A_r[m_full]); real_D_full.append(D_r[m_full])
        # structure réelle (une journée = une réalisation)
        row = {"date": date, "generator": "real"}
        for name, col in [("hour", "hour_block_arr"), ("carrier", "carrier"), ("region", "origin_region")]:
            row[f"corr_{name}"] = structural.intra_group_corr(A_r[m_arr], day.loc[m_arr, col].to_numpy())
        corr_rows.append(row)
        disp_rows.append({"date": date, "generator": "real", **{"late": (A_r[m_arr] > 15).astype(float)}, "hours": day.loc[m_arr, "hour_block_arr"].to_numpy()})
        for g in GENS:
            t0 = time.time()
            out = baselines.run(g, day, params, a.n_scenarios, seed0 + di)
            t_gen[g] += time.time() - t0
            keep = slice(0, a.keep_scenarios)
            gen_A[g].append(out["A"][keep][:, m_arr].ravel()); gen_D[g].append(out["D"][keep][:, m_full].ravel())
            gen_reg[g].append(np.repeat(out["regime"][keep].astype(str), m_arr.sum()))
            gen_A_full[g].append(out["A"][keep][:, m_full].ravel()); gen_D_full[g].append(out["D"][keep][:, m_full].ravel())
            gen_Dreact[g].append(out["D_react"][keep][:, m_full].ravel())
            row = {"date": date, "generator": g}
            for name, col in [("hour", "hour_block_arr"), ("carrier", "carrier"), ("region", "origin_region")]:
                row[f"corr_{name}"] = structural.intra_group_corr(out["A"][:, m_arr], day.loc[m_arr, col].to_numpy())
            # dispersion des comptes horaires de retards (sur les scénarios d'une même journée)
            dd = structural.late_count_dispersion(out["A"][:, m_arr] > 15, day.loc[m_arr, "hour_block_arr"].to_numpy())
            row["dispersion_index"] = dd["index_of_dispersion"]
            corr_rows.append(row)
        if di % 30 == 0:
            log.info("jour %d/%d (%s)", di + 1, len(days), pd.Timestamp(date).date())

    real_A = np.concatenate(real_A); real_D = np.concatenate(real_D); real_regime = np.concatenate(real_regime)
    real_A_full = np.concatenate(real_A_full); real_D_full = np.concatenate(real_D_full)

    # ---------------- T1 : fidélité statistique
    t1 = []
    for g in GENS:
        gA = np.concatenate(gen_A[g]); gD = np.concatenate(gen_D[g]); gR = np.concatenate(gen_reg[g])
        for scope, mr, mg in [("all", np.ones(len(real_A), bool), np.ones(len(gA), bool)),
                              ("normal", real_regime == "normal", gR == "normal"),
                              ("degrade", real_regime == "degrade", gR == "degrade")]:
            r = statistical.compare(real_A[mr], gA[mg]); r.update(generator=g, variable="A", scope=scope); t1.append(r)
        r = statistical.compare(real_D, gD); r.update(generator=g, variable="D", scope="all"); t1.append(r)
    t1 = pd.DataFrame(t1)
    cols = ["generator", "variable", "scope", "ks_stat", "wasserstein", "share_gt15_real", "share_gt15_gen",
            "q95_real", "q95_gen", "q99_real", "q99_gen", "mean_real", "mean_gen", "std_real", "std_gen"]
    write_table(t1[cols], out_dir, "T1_statistical_fidelity", "%.3f",
                caption="E1 — Fidélité statistique des marginales (période test)", label="tab:T1")

    # ---------------- T2 : structure
    corr = pd.DataFrame(corr_rows)
    t2 = corr.groupby("generator")[["corr_hour", "corr_carrier", "corr_region", "dispersion_index"]].mean().reindex(["real"] + GENS)
    # dispersion réelle : sur les jours (chaque jour = une réalisation) -> même définition var/moyenne des comptes horaires
    # (calculée sur les comptes par (jour, heure) autour de la moyenne horaire)
    real_disp = _real_dispersion(rot[rot.split == "test"])
    t2.loc["real", "dispersion_index"] = real_disp
    # part réactionnelle et E[D|A]
    ed_rows = []
    bts_share = _bts_late_share(rot[rot.split == "test"])
    t2["reactionary_share"] = np.nan
    t2.loc["real", "reactionary_share"] = bts_share
    ed_real = structural.conditional_departure(real_A_full, real_D_full); ed_real["generator"] = "real"; ed_rows.append(ed_real.reset_index())
    for g in GENS:
        gA = np.concatenate(gen_A_full[g]); gD = np.concatenate(gen_D_full[g]); gR = np.concatenate(gen_Dreact[g])
        t2.loc[g, "reactionary_share"] = structural.reactionary_share(gR, gD)
        ed = structural.conditional_departure(gA, gD); ed["generator"] = g; ed_rows.append(ed.reset_index())
    t2 = t2.reset_index()
    write_table(t2, out_dir, "T2_structure", "%.3f", caption="E2 — Structure de dépendance et propagation", label="tab:T2")
    ed_all = pd.concat(ed_rows, ignore_index=True)
    write_table(ed_all, out_dir, "T2b_conditional_departure", "%.2f")
    corr.to_csv(os.path.join(out_dir, "daily_structure.csv"), index=False)
    dump_json({"generation_seconds_total": t_gen, "n_days": len(days), "n_scenarios": a.n_scenarios,
               "rotations_per_day_mean": float(rot[rot.split == "test"].groupby("date").size().mean())},
              os.path.join(out_dir, "runtime.json"))

    # ---------------- F1 : QQ-plots A par régime ; F3 : E[D|A]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, scope in zip(axes, ["all", "normal", "degrade"]):
        mr = np.ones(len(real_A), bool) if scope == "all" else real_regime == scope
        for g, mk in zip(GENS, ["x", "+", "^", "o"]):
            gA = np.concatenate(gen_A[g]); gR = np.concatenate(gen_reg[g])
            mg = np.ones(len(gA), bool) if scope == "all" else gR == scope
            qr, qg = statistical.qq_points(real_A[mr], gA[mg])
            ax.plot(qr, qg, mk, ms=4, label=baselines.LABELS[g], alpha=.8)
        lim = [min(real_A[mr].min(), -40), np.quantile(real_A[mr], .995)]
        ax.plot(lim, lim, "k--", lw=1); ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_title(f"A — régime : {scope}"); ax.set_xlabel("quantiles réels (min)"); ax.set_ylabel("quantiles générés (min)")
    axes[0].legend(fontsize=7)
    fig.savefig(os.path.join(fig_dir, "F1_qq_arrival_delay.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    for g, mk in zip(["real"] + GENS, ["s", "x", "+", "^", "o"]):
        e = ed_all[ed_all.generator == g]
        ax.plot(e["bin"].astype(str), e["mean"], f"-{mk}", label=("Réel (BTS 2024)" if g == "real" else baselines.LABELS[g]),
                lw=2.2 if g == "real" else 1.2, color="k" if g == "real" else None)
    ax.set_xlabel("classe de retard d'arrivée A"); ax.set_ylabel("E[D | A] (min)"); ax.legend(fontsize=8)
    fig.savefig(os.path.join(fig_dir, "F3_conditional_departure.png"), dpi=200, bbox_inches="tight"); plt.close(fig)

    # F1b : distribution de D réel vs généré
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.linspace(-20, 200, 111)
    ax.hist(np.clip(real_D, -20, 200), bins=bins, density=True, histtype="step", color="k", lw=2, label="Réel")
    for g in GENS:
        ax.hist(np.clip(np.concatenate(gen_D[g]), -20, 200), bins=bins, density=True, histtype="step", label=baselines.LABELS[g])
    ax.set_yscale("log"); ax.set_xlabel("retard de départ D (min)"); ax.set_ylabel("densité (log)"); ax.legend(fontsize=7)
    fig.savefig(os.path.join(fig_dir, "F1b_departure_delay_density.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    log.info("E1/E2 terminées -> %s", out_dir)


def _real_dispersion(rot_test: pd.DataFrame) -> float:
    d = rot_test[~rot_test.first_departure].dropna(subset=["A"])
    c = d.assign(late=d.A > 15).groupby(["date", "hour_block_arr"]).late.sum().unstack(fill_value=0)
    m = c.mean(axis=0); v = c.var(axis=0); ok = m > 0.5
    return float((v[ok] / m[ok]).mean())


def _bts_late_share(rot_test: pd.DataFrame) -> float:
    full = rot_test[(~rot_test.open_rotation) & (~rot_test.first_departure)]
    return float(full.late_aircraft_delay.fillna(0).sum() / full.D.clip(lower=0).sum())


if __name__ == "__main__":
    main()
