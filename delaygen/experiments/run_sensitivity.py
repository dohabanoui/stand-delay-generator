"""E4 — Sensibilité : correlation_scale, peak_multiplier, forced_regime, n_scenarios (T4, F5).

Usage : python -m delaygen.experiments.run_sensitivity [--max-days 30]
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

from delaygen import generate  # noqa: E402
from delaygen.allocation import instance, milp, replay  # noqa: E402
from delaygen.experiments.common import day_schedule, load_all, real_times, setup_logging, test_days, write_table  # noqa: E402

log = logging.getLogger(__name__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--hub", default=None)
    ap.add_argument("--max-days", type=int, default=30)
    ap.add_argument("--n-scenarios", type=int, default=100)
    a = ap.parse_args()
    setup_logging()
    cfg, hub, rot, params = load_all(a.config, a.hub)
    al = cfg["allocation"]
    out_dir = os.path.join(cfg["paths"]["results"], "sensitivity")
    fig_dir = os.path.join(cfg["paths"]["results"], "figures")
    os.makedirs(out_dir, exist_ok=True)
    days = test_days(rot, 1, a.max_days, seed=1, cfg=cfg)
    seed0 = cfg["generation"]["seed"]

    settings = ([("correlation_scale", v) for v in [0.0, 0.5, 1.0, 1.5]] + [("peak_multiplier", v) for v in [1.0, 1.25, 1.5]]
                + [("forced_regime", v) for v in ["normal", "degrade"]] + [("propagation", v) for v in [False, True]])
    rows = []
    for di, date in enumerate(days):
        day = day_schedule(rot, date)
        stands = instance.build(day, None, al["target_peak_occupancy"], al["stand_shares"], seed=di)
        b0 = float(al.get("buffer_minutes", [5])[0])
        sol = milp.solve(day, stands, b0, al["time_limit_s"], seed=di)
        if not sol["allocation"]:
            continue
        a_r, d_r = real_times(day)
        real_c = replay.conflicts(day, sol["allocation"], a_r, d_r, al["b_ops"])["conflicts"][0]
        for name, val in settings:
            kw = {}
            if name == "correlation_scale":
                kw["correlation_scale"] = val
            elif name == "peak_multiplier":
                kw["peak_multiplier"] = val
            elif name == "forced_regime":
                kw["forced_regime"] = val
            elif name == "propagation":
                kw["propagation_on"] = val
            out = generate.generate_day(day, params, a.n_scenarios, seed0 + di, **kw)
            c = replay.conflicts(day, sol["allocation"], out["a_real"], out["d_real"], al["b_ops"])["conflicts"]
            rows.append({"date": date, "parameter": name, "value": val, "real_conflicts": real_c,
                         "conflicts_mean": c.mean(), "conflicts_q90": np.quantile(c, .9), "conflicts_std": c.std(),
                         "A_mean": out["A"].mean(), "A_gt15": (out["A"] > 15).mean(), "D_mean": out["D"].mean()})
        # stabilité selon n_scenarios
        for n in [10, 30, 100, 300]:
            out = generate.generate_day(day, params, n, seed0 + di)
            c = replay.conflicts(day, sol["allocation"], out["a_real"], out["d_real"], al["b_ops"])["conflicts"]
            rows.append({"date": date, "parameter": "n_scenarios", "value": n, "real_conflicts": real_c,
                         "conflicts_mean": c.mean(), "conflicts_q90": np.quantile(c, .9), "conflicts_std": c.std(),
                         "A_mean": out["A"].mean(), "A_gt15": (out["A"] > 15).mean(), "D_mean": out["D"].mean()})
        if di % 10 == 0:
            log.info("jour %d/%d", di + 1, len(days))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "daily_sensitivity.csv"), index=False)
    t4 = df.groupby(["parameter", "value"], sort=False).agg(
        real_conflicts=("real_conflicts", "mean"), conflicts_mean=("conflicts_mean", "mean"),
        conflicts_q90=("conflicts_q90", "mean"), conflicts_std=("conflicts_std", "mean"),
        A_mean=("A_mean", "mean"), A_gt15=("A_gt15", "mean"), D_mean=("D_mean", "mean")).reset_index()
    t4["bias_pct"] = 100 * (t4.conflicts_mean - t4.real_conflicts) / t4.real_conflicts
    write_table(t4, out_dir, "T4_sensitivity", "%.2f", caption="E4 — Sensibilité aux leviers du générateur", label="tab:T4")

    fig, axes = plt.subplots(1, 4, figsize=(15, 3.6))
    for ax, p in zip(axes, ["correlation_scale", "peak_multiplier", "forced_regime", "n_scenarios"]):
        t = t4[t4.parameter == p]
        x = t.value.astype(str)
        ax.errorbar(x, t.conflicts_mean, yerr=t.conflicts_std, fmt="o-", capsize=3, label="scénarios (moy ± sd)")
        ax.plot(x, t.conflicts_q90, "^:", label="Q90 scénarios")
        ax.axhline(t.real_conflicts.iloc[0], color="k", ls="--", label="réel (moy. des jours)")
        ax.set_title(p); ax.set_xlabel("valeur"); ax.set_ylabel(f"conflits / jour (b = {al.get('buffer_minutes', [5])[0]:g} min)")
    axes[0].legend(fontsize=7)
    fig.savefig(os.path.join(fig_dir, "F5_sensitivity.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    log.info("E4 terminée -> %s", out_dir)


if __name__ == "__main__":
    main()
