"""Tableaux de positionnement par rapport à la littérature (T_lit1 : générateurs de retards pour l'allocation
robuste ; T_lit2 : travaux utilisant le jeu BTS On-Time Performance).

Les cellules marquées « † » reprennent des caractéristiques citées dans le cahier des charges ou connues de
l'auteur et doivent être contrôlées sur le texte original avant soumission.
"""
from __future__ import annotations

import os

import pandas as pd

from delaygen.config import load_config
from delaygen.experiments.common import write_table

OUI, NON, PART = "oui", "non", "partiel"

LIT_GENERATORS = [
    # ref, aéroport/données, données publiques, marginales, corrélation entre vols, propagation A->D, régimes météo, validation, générateur ouvert, coût
    dict(ref="Yan & Tang (2007) EJOR", airport="CKS Taipei †", public=NON, marginals="lois ajustées sur historique †",
         correlation=NON, propagation=NON, regime=NON, validation="simulation des affectations", open_source=NON),
    dict(ref="Şeker & Noyan (2012) TRE", airport="scénarios de retards (grand aéroport US) †", public=NON,
         marginals="scénarios échantillonnés †", correlation=NON, propagation=NON, regime=NON,
         validation="programmation stochastique (objectif)", open_source=NON),
    dict(ref="Diepen et al. (2012) J. Sched.", airport="Amsterdam Schiphol", public=NON, marginals="aucune (robustesse par temps libre)",
         correlation=NON, propagation=NON, regime=NON, validation="rejeu sur retards réels †", open_source=NON),
    dict(ref="Castaing et al. (2016) COR", airport="hub US (données compagnie) †", public=NON,
         marginals="historique de retards échantillonné †", correlation=NON, propagation=NON, regime=NON,
         validation="blocages de portes simulés", open_source=NON),
    dict(ref="Xu et al. (2017) TRB", airport="cas d'étude (budget d'incertitude)", public=NON,
         marginals="intervalles bornés (pas de loi)", correlation="budget global", propagation=NON, regime=NON,
         validation="pire cas partiel", open_source=NON),
    dict(ref="Dorndorf et al. (2017) OR Spectrum", airport="hub européen (données privées) †", public=NON,
         marginals="arrivées/départs stochastiques †", correlation=NON, propagation=PART + " (recours) †", regime=NON,
         validation="simulation + stratégies de recours", open_source=NON),
    dict(ref="Dijk et al. (2019) OR Spectrum", airport="São Paulo–Guarulhos (GRU)", public=NON,
         marginals="loi par vol (normale, exp., gamma, Weibull)", correlation="signe de l'écart : région d'origine, fenêtre d'1 h",
         propagation=PART + " (départ à l'horaire sauf rotation minimale)", regime=NON, validation="30 scénarios, recours (attente, réaffectation, remorquage)",
         open_source=NON),
    dict(ref="Bagamanova & Mujica Mota (2020) JATM", airport="aéroport (simulation) †", public=NON,
         marginals="composante « delay-aware » (simulation) †", correlation=NON, propagation=PART + " †", regime=NON,
         validation="simulation", open_source=NON),
    dict(ref="Park & Ku (2026) Aerospace", airport="Gimpo (GMP)", public=NON, marginals="simulation fast-time des mouvements sol",
         correlation="implicite (simulation)", propagation="implicite (simulation)", regime=NON,
         validation="une journée simulée", open_source=NON),
    dict(ref="Cette étude (2026)", airport="Charlotte (CLT), BTS 2023–2024", public=OUI,
         marginals="quantiles empiriques par (heure, régime) [+ lois paramétriques, AIC]",
         correlation="copule gaussienne à facteurs : jour, heure, compagnie, région",
         propagation=OUI + " (MTT, slack, retard réactionnel)", regime="chaîne de Markov 2 états",
         validation="3 niveaux : statistique, structurel, opérationnel (conflits réels vs générés, 366 jours)",
         open_source=OUI + " (package + benchmark)"),
]

LIT_BTS = [
    dict(ref="Tu, Ball & Jank (2008) JASA", data="retards de départ, une compagnie à Denver †", objectif="loi de retard de départ (mélange, tendance saisonnière)",
         niveau="vol", usage_stands=NON),
    dict(ref="Deshpande & Arikan (2012) MSOM", data="BTS On-Time Performance", objectif="effet des horaires (block time) sur les retards",
         niveau="vol / compagnie", usage_stands=NON),
    dict(ref="Rebollo & Balakrishnan (2014) TR-C", data="BTS / ASPM, réseau US", objectif="prédiction des retards réseau (classification, régression)",
         niveau="réseau / paire OD", usage_stands=NON),
    dict(ref="Kafle & Zou (2016) TR-B", data="BTS On-Time Performance", objectif="propagation des retards (approche analytique-économétrique)",
         niveau="rotation / compagnie", usage_stands=NON),
    dict(ref="Sternberg et al. (2017) arXiv", data="revue (BTS majoritaire)", objectif="revue des méthodes de prédiction de retards",
         niveau="—", usage_stands=NON),
    dict(ref="Wu et al. (2024) TR-E", data="revue (BTS, Eurocontrol)", objectif="revue : propagation des retards, données et méthodes",
         niveau="—", usage_stands=NON),
    dict(ref="Cette étude (2026)", data="BTS On-Time Performance 2023–2024, hub CLT + registre FAA",
         objectif="générateur de scénarios (marginales, copule, propagation, régimes) validé sur les conflits de stands",
         niveau="rotation au hub (arrivée + départ)", usage_stands=OUI),
]


def main():
    cfg = load_config()
    out_dir = os.path.join(cfg["paths"]["results"], "tables")
    t1 = pd.DataFrame(LIT_GENERATORS).rename(columns={
        "ref": "Référence", "airport": "Aéroport / données", "public": "Données publiques", "marginals": "Marginales des retards",
        "correlation": "Corrélation entre vols", "propagation": "Propagation arrivée→départ", "regime": "Régimes météo",
        "validation": "Validation", "open_source": "Générateur ouvert"})
    write_table(t1, out_dir, "T_lit1_delay_generators_comparison", caption="Positionnement : générateurs de retards pour l'allocation robuste de stands", label="tab:lit1")
    t2 = pd.DataFrame(LIT_BTS).rename(columns={"ref": "Référence", "data": "Données", "objectif": "Objectif", "niveau": "Niveau d'analyse", "usage_stands": "Lien avec l'allocation de stands"})
    write_table(t2, out_dir, "T_lit2_bts_dataset_studies", caption="Travaux exploitant le jeu BTS On-Time Performance", label="tab:lit2")
    print(f"{len(t1)} lignes -> {out_dir}/T_lit1_*, {len(t2)} lignes -> T_lit2_*")


if __name__ == "__main__":
    main()
