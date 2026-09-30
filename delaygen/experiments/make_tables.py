"""Assemble les tableaux finaux (T0..T4, T_lit) et un résumé Markdown des résultats dans results/tables/.

Usage : python -m delaygen.experiments.make_tables
"""
from __future__ import annotations

import json
import os
import shutil

import pandas as pd

from delaygen import baselines
from delaygen.config import load_config
from delaygen.experiments.common import write_table


def _read(path):
    return pd.read_csv(path) if os.path.exists(path) else None


def main(cfg_path=None):
    cfg = load_config(cfg_path)
    res = cfg["paths"]["results"]
    out = os.path.join(res, "tables")
    os.makedirs(out, exist_ok=True)
    hub = cfg["hub"]
    md = [f"# Résultats — générateur de scénarios de retards, hub {hub}\n"]

    # T0 (EDA)
    for f in ["T0_dataset_description.csv", "T0_dataset_description.tex"]:
        p = os.path.join(res, "eda", f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(out, f))
    t0 = _read(os.path.join(res, "eda", "T0_dataset_description.csv"))
    if t0 is not None:
        md.append("## T0 — Description du jeu de données\n\n" + t0.to_markdown(index=False) + "\n")

    # paramètres estimés
    y = str(cfg["train_period"]["start"])[:4]
    fr = os.path.join(cfg["paths"]["processed"], f"fit_report_{hub}_train{y}.json")
    if os.path.exists(fr):
        with open(fr, encoding="utf-8") as fh:
            rep = json.load(fh)
        rows = []
        for k, v in rep["dependence"].items():
            rows.append({"régime": k, **{x: round(v[x], 3) for x in ["lambda_d", "lambda_h", "lambda_c", "lambda_r", "sigma_eps"]},
                         "corr. même jour": round(v["lambda_d"] ** 2, 3),
                         "corr. jour+heure": round(v["lambda_d"] ** 2 + v["lambda_h"] ** 2, 3),
                         "corr. jour+compagnie": round(v["lambda_d"] ** 2 + v["lambda_c"] ** 2, 3),
                         "corr. jour+région": round(v["lambda_d"] ** 2 + v["lambda_r"] ** 2, 3)})
        tp = pd.DataFrame(rows)
        write_table(tp, out, "T_params_dependence", "%.3f", caption="Coefficients de la copule à facteurs (période train)", label="tab:params")
        md.append(f"## Paramètres estimés (estimation {y})\n\n" + tp.to_markdown(index=False) + "\n")
        mtt = pd.DataFrame([{"catégorie": k, "MTT programmé tendu (Q5, A≥30)": v, "temps sol réel Q5": rep["mtt"]["real_ground_q05"][k]} for k, v in rep["mtt"]["scheduled_tight"].items()])
        write_table(mtt, out, "T_params_mtt", "%.0f")
        md.append("Temps minimaux de rotation (min) :\n\n" + mtt.to_markdown(index=False) + "\n")
        pm = pd.DataFrame([{"régime": r, **{f: round(v["aic"]) for f, v in rep["parametric_A"][r]["fits"].items() if "aic" in v}, "meilleure": rep["parametric_A"][r]["best"]} for r in rep["parametric_A"]])
        write_table(pm, out, "T_params_parametric_aic", "%.0f")
        md.append("AIC des lois paramétriques décalées pour A (comparaison, l'option quantile reste la référence) :\n\n" + pm.to_markdown(index=False) + "\n")
        reg = rep["regime"]
        md.append(f"Chaîne de Markov des régimes : états {reg['states']}, matrice {[[round(x, 3) for x in r] for r in reg['transition_matrix']]}, "
                  f"loi stationnaire {[round(x, 3) for x in reg['stationary']]}.\n")

    # T1..T4
    for name, sub, title in [("T1_statistical_fidelity", "validation", "T1 — Fidélité statistique (E1)"),
                             ("T2_structure", "validation", "T2 — Structure (E2)"),
                             ("T2b_conditional_departure", "validation", "T2b — E[D | A] réel vs généré"),
                             ("T3_operational_impact", "allocation", "T3 — Impact opérationnel (E3)"),
                             ("T3b_before_after_unconditional", "allocation", "T3b — Avant / après (régime tiré par le générateur)"),
                             ("T3b_before_after_conditioned", "allocation", "T3b — Avant / après (régime réel du jour connu)"),
                             ("T4_sensitivity", "sensitivity", "T4 — Sensibilité (E4)")]:
        df = _read(os.path.join(res, sub, name + ".csv"))
        if df is None:
            continue
        if "generator" in df:
            df.insert(1, "label", df.generator.map({**baselines.LABELS, "real": "Réel"}))
        for ext in [".csv", ".tex", ".md"]:
            p = os.path.join(res, sub, name + ext)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(out, name + ext))
        md.append(f"## {title}\n\n" + df.round(3).to_markdown(index=False) + "\n")

    # runtime
    for sub in ["validation", "allocation"]:
        p = os.path.join(res, sub, "runtime.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                md.append(f"Temps de calcul ({sub}) : `{json.dumps(json.load(fh))}`\n")

    # littérature
    for name in ["T_lit1_delay_generators_comparison", "T_lit2_bts_dataset_studies"]:
        df = _read(os.path.join(out, name + ".csv"))
        if df is not None:
            md.append(f"## {name}\n\n" + df.to_markdown(index=False) + "\n")

    with open(os.path.join(out, "RESULTS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    print(f"-> {os.path.join(out, 'RESULTS.md')} ({len(md)} sections)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--config", default=None)
    main(ap.parse_args().config)
