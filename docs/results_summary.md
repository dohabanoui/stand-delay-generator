# Synthèse des résultats (28 septembre 2026) — hub CLT, estimation 2023, validation 2024

Fichiers : `results/tables/RESULTS.md` (hors-échantillon), `results_insample_2024/tables/RESULTS.md` (in-sample),
figures dans `results/eda/` et `results/figures/`, légendes proposées dans `figures_captions.md`.

## Données (T0)

809 384 vols BTS au hub (2023–2024), 404 349 arrivées, 342 011 rotations appariées (84,6 %), 12 compagnies,
3 918 immatriculations, catégorie d'avion FAA pour 99 % des vols. 2024 est plus perturbée que 2023 :
retard moyen d'arrivée 6,7 vs 4,1 min, 21,2 % vs 18,1 % d'arrivées > 15 min, 96 vs 76 jours dégradés.

## Paramètres estimés (2023)

- Copule à facteurs : λ_d 0,11 · λ_h 0,16 · λ_c 0,14 · λ_r 0,19 · σ_ε 0,95 ; en régime dégradé λ_h monte à 0,27.
- MTT : RJ 44, NB 47, WB 60 min (Q5 du temps au sol programmé des rotations arrivées ≥ 30 min en retard).
- LateAircraftDelay = 50 % des minutes de retard BTS ; part réactionnelle observée dans D = 43 %.
- Loi paramétrique la mieux classée par AIC : log-normale décalée (les quantiles empiriques restent la référence).

## E1 — Marginales (T1, F1, F1b) — 366 jours × 100 scénarios

| | KS(A) | W(A) | KS(D) | W(D) | Q95(D) gén. / réel 85 |
|---|---|---|---|---|---|
| Indépendant | 0,03 | 2,5 | 0,06 | 3,8 | 72 |
| Heure + région | 0,04 | 2,6 | 0,06 | 3,8 | 72 |
| Proposé sans propagation | 0,03 | 2,5 | 0,17 | 9,8 | 42 |
| **Proposé** | 0,03 | 2,5 | **0,05** | **1,9** | **84** |

Les marginales de A sont communes aux quatre générateurs (même M2) et sous-estiment 2024 (dérive : Q95 79 vs 90 min).
In-sample (paramètres 2024) : KS(A) = KS(D) = 0,01 pour le générateur proposé.

## E2 — Structure (T2, T2b, F3)

| | corr. intra-heure | indice de dispersion | part réactionnelle |
|---|---|---|---|
| Réel 2024 | 0,06 | 3,17 | 0,43 |
| Indépendant | 0,03 | 1,75 | 0 |
| Heure + région | 0,04 | 2,23 | 0 |
| **Proposé** | 0,05 | 2,47 | 0,58 |

Seul le générateur proposé reproduit la courbe E[D | A] (F3) ; il surestime E[D | A > 45] (85 vs 71 min) :
la compression des rotations par les compagnies n'est pas modélisée (limite à mentionner). La sur-dispersion réelle
des comptes horaires (3,2) n'est reproduite qu'aux deux tiers (copule gaussienne sans dépendance de queue).

## E3 — Impact opérationnel (T3, T3b, F2, F2b, F4) — 122 jours, b = 5 min, régime réel connu

| Indicateur (par jour) | Réel | Indépendant | Heure+région | Proposé sans prop. | **Proposé** |
|---|---|---|---|---|---|
| Conflits de stands | 143,2 | 125,7 (−12 %) | 125,6 (−12 %) | 102,2 (−29 %) | **130,2 (−9 %)** |
| MAE journalière | — | 21,2 | 21,2 | 41,2 | **18,5** |
| Corrélation jour à jour | — | 0,72 | 0,72 | 0,57 | 0,70 |
| AUC jours de pointe (Q90) | — | 0,89 | 0,90 | 0,62 | 0,83 |
| Réel dans [Q5, Q95] des scénarios | — | 41 % | 60 % | 23 % | **65 %** |
| Réel au-dessus de tous les scénarios | — | 38 % | 25 % | 56 % | **20 %** |

In-sample 2024 : biais −6,4 % (indépendant) et −5,9 % (proposé) ; couverture 54 % vs 69 % ; réel au-dessus de
tous les scénarios 25 % vs 11 %. Environ un tiers du biais hors-échantillon est donc de la dérive annuelle, le reste
est commun à tous les générateurs (instance de stands synthétique, rotations ouvertes, recours non modélisé).

**Lecture honnête pour l'article** : le gain du générateur proposé porte sur (i) la loi du retard de départ
(W 1,9 vs 3,8), (ii) la propagation (E[D|A], part réactionnelle), (iii) l'enveloppe des conflits : le réel sort
deux fois moins souvent de l'intervalle des scénarios. Le niveau moyen des conflits et le classement des jours
(corrélation, AUC) sont comparables à ceux du générateur indépendant, car ils dépendent surtout du programme
de vols et du régime du jour ; l'ablation « sans propagation » montre que la propagation est le composant
décisif (−29 % de conflits sans elle).

## E4 — Sensibilité (T4, F5) — 30 jours, b = 5 min

- `correlation_scale` 0 → 1,5 : moyenne des conflits stable (132 → 134) mais écart-type des scénarios 10,2 → 15,3
  et Q90 145 → 153 : la corrélation pilote la dispersion, pas le niveau.
- `propagation` off : −22 % de conflits (105 vs 134).
- `forced_regime` normal / dégradé : 131 / 146 conflits, A moyen 0 / 17 min.
- `peak_multiplier` 1 → 1,5 : +3 conflits/jour ; `n_scenarios` ≥ 30 suffisant (moyenne stable à ±1).

## Coût de calcul

Génération : 100 scénarios × 670 rotations ≈ 0,15 s (366 jours × 4 générateurs en 3,6 min). Allocation :
CP-SAT 20 s + repli glouton (90 % des jours), 125 stands en moyenne. E3 complet : 2 h 30 (122 jours, 2 buffers,
2 modes) ; E3 in-sample avec glouton seul : 50 min.

## Limites à écrire

Dérive temporelle (2023 → 2024) ; instance de stands synthétique ; 15 % de rotations non appariées ; copule
gaussienne (queues) ; régime journalier binaire estimé sans METAR ; compression des rotations non modélisée ;
allocation de banc d'essai (glouton + CP-SAT limité), pas de SAA (perspective).
