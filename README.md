# delaygen — Générateur de scénarios de retards pour l'allocation robuste de stands

Implémentation de Générateur de scénarios de retards pour l'allocation robuste de stands
aéroportuaires, calibrée et validée sur les données
publiques BTS (Reporting Carrier On-Time Performance) du hub de Charlotte (CLT), 2023 (estimation) / 2024 (validation).

## Structure du projet

```
stand-delay-generator/
├── delaygen/                     # package Python
│   ├── config/                   # default.yaml, regions.csv (état US -> région)
│   ├── data/                     # loaders (BTS, FAA, METAR), cleaning, aircraft (catégorie), rotations, weather (régime)
│   ├── models/                   # M1 regime, M2 marginals, M3 dependence (copule à facteurs), M4 propagation, M5 ground
│   ├── prepare.py                # BTS -> rotations_<HUB>.parquet, regime_<HUB>.parquet
│   ├── fit.py                    # rotations (train) -> params_<HUB>_train<YYYY>.json, fit_report_<HUB>_train<YYYY>.json
│   ├── generate.py               # programme d'une journée + params -> scénarios (vectorisé NumPy)
│   ├── baselines.py              # générateurs de référence : independent, hour_region (≈ Dijk et al.), proposed_noprop, proposed
│   ├── validation/               # statistical (KS, Wasserstein, quantiles), structural (corrélations, E[D|A]), operational (conflits)
│   ├── allocation/               # instance (stands synthétiques), milp (CP-SAT + glouton), replay (conflits, recours)
│   ├── analysis/eda.py           # analyse exploratoire : figures F_eda1..12, tableau T0
│   ├── experiments/              # run_validation (E1, E2), run_allocation (E3), run_sensitivity (E4), make_tables, literature_table
│   └── cli.py                    # delaygen prepare|fit|eda|validate|allocate|sensitivity|tables|literature
├── scripts/                      # download_bts.sh, extract_hub_bts.py, make_synthetic_data.py
├── data/
│   ├── raw/bts/                  # 24 archives mensuelles TranStats (2023-01 .. 2024-12), ~660 Mo
│   ├── raw/faa/                  # ReleasableAircraft.zip (registre FAA)
│   └── processed/                # extraits hub (parquet), rotations, régime, params, rapports JSON
├── results/
│   ├── eda/                      # figures et tableaux descriptifs (PNG + PDF + CSV/TeX)
│   ├── validation/               # T1, T2, T2b (E1, E2)
│   ├── allocation/               # T3, T3b avant/après, métriques journalières, log MILP (E3)
│   ├── sensitivity/              # T4 (E4)
│   ├── figures/                  # F1, F1b, F2, F2b, F3, F4, F5
│   └── tables/                   # tableaux finaux + RESULTS.md + tableaux de littérature
├── tests/                        # pytest (10 tests, cahier des charges §11)
├── docs/model.md                 # rappel des modèles M1–M5 et des choix d'implémentation
└── pyproject.toml
```

## Installation

```bash
pip install -e .          # ou : pip install numpy pandas scipy statsmodels pyarrow pyyaml ortools matplotlib seaborn tabulate pytest
```

## Données

1. `bash scripts/download_bts.sh 2023 2024 data/raw/bts` — archives mensuelles (~27 Mo zip / ~240 Mo CSV chacune).
2. `python scripts/extract_hub_bts.py --hub CLT --years 2023 2024` — extraits `data/processed/bts_CLT_<YEAR>.parquet`.
3. Registre FAA : `https://registry.faa.gov/database/ReleasableAircraft.zip` dans `data/raw/faa/`
   (le téléchargement exige un User-Agent de navigateur).
4. METAR (optionnel, `paths.metar`) : sans METAR, le régime journalier est estimé par repli BTS (§3.4 du cahier des charges).

## Pipeline complet

```bash
python -m delaygen.prepare                       # nettoyage, catégorie avion, rotations, régime   (~3 min)
python -m delaygen.fit                           # M1..M5 -> params_CLT_train2023.json                   (~10 s)
python -m delaygen.analysis.eda                  # figures exploratoires                            (~1 min)
python -m delaygen.experiments.run_validation    # E1, E2 : 366 jours x 100 scénarios x 4 générateurs (~10 min)
python -m delaygen.experiments.run_allocation --every 3 --buffers 5 15   # E3 : MILP + rejeu        (~1.5 h)
python -m delaygen.experiments.run_sensitivity --max-days 30             # E4                       (~15 min)
python -m delaygen.experiments.literature_table  # tableaux de positionnement
python -m delaygen.experiments.make_tables       # results/tables/RESULTS.md
python -m pytest
```

## Exécution dans Visual Studio Code

Ouvrir le dossier `stand-delay-generator` dans VS Code (`code .`). Le dossier `.vscode/` fournit :

- **Exécuter et déboguer** (F5) : configurations `1. prepare` → `7. tableaux finaux` et `Tests (pytest)` ; les
  configurations 4–6 utilisent des sous-ensembles de jours (30 / 5 / 5) pour un essai rapide (< 5 min).
- **Terminal → Exécuter la tâche** : tâches complètes (`exp: allocation E3 (complet, ~1h45)`, etc.) et la tâche
  `TOUT` (Ctrl+Shift+B) qui enchaîne prepare → fit → eda → E1..E4 → tables.
- Tests : Ctrl+Shift+P → *Run Test Task*, ou l'onglet « Tests » (pytest activé dans `settings.json`).

Variante « in-sample 2024 » (estimation et validation sur 2024, pour isoler la dérive temporelle 2023→2024) :

```bash
python -m delaygen.fit --config delaygen/config/insample_2024.yaml
python -m delaygen.experiments.run_validation --config delaygen/config/insample_2024.yaml
python -m delaygen.experiments.run_allocation --config delaygen/config/insample_2024.yaml --every 3 --buffers 5 15 --time-limit 1
python -m delaygen.experiments.make_tables --config delaygen/config/insample_2024.yaml   # -> results_insample_2024/
```

## Choix d'implémentation notables (écarts documentés par rapport au cahier des charges)

- **Régime météo** : sans METAR, repli BTS (part WeatherDelay+NASDelay et retard moyen journalier > Q80 des jours
  d'estimation) ; seuils estimés sur 2023 et appliqués à 2024.
- **Catégorie d'avion** : registre FAA (99 % des vols rattachés) ; E-jets / CRJ / ERJ classés `RJ` (siège ≤ 100),
  737/A320 `NB`, 767+ `WB`.
- **Parts de stands** : `{WB 0.03, NB 0.67, RJ 0.30}` au lieu de `{0.15, 0.70, 0.15}` : le trafic BTS de CLT est
  domestique (0,4 % de gros-porteurs).
- **Allocation** : CP-SAT (formulation par cliques d'intervalles) avec indice glouton et limite 20 s ; si aucune
  solution n'est prouvée dans le délai, la solution gloutonne (faisable) est utilisée (`status = GREEDY_FALLBACK`).
- **Buffers** : `b = 5` (marge opérationnelle minimale, allocation « nominale ») et `b = 15` ; avec `b = 0`, les
  rotations programmées bord à bord produisent des conflits même sans retard (`b_ops = 5`).
- **Deux modes d'évaluation opérationnelle** : régime tiré par le générateur (*unconditional*) et régime forcé au
  régime réel du jour (*conditioned*, équivalent d'une prévision météo J-1).
- **Composition du retard de départ** : `D = max(A − slack, G)` (chemin critique du turnaround) au lieu de
  `D = D_react + G` ; départs anticipés autorisés (`G < 0`). Justification et effet dans `docs/model.md`.
- **Résultats** : `results/tables/RESULTS.md` (estimation 2023 → validation 2024) et
  `results_insample_2024/tables/RESULTS.md` (in-sample) ; liste des figures avec légendes dans `docs/figures_captions.md`.
