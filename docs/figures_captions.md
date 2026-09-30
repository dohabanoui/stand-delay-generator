# Figures et tableaux disponibles pour l'article (avec légendes proposées)

Tous les fichiers PNG (200 dpi) ont un équivalent PDF vectoriel dans `results/eda/` ; les figures d'expériences
sont dans `results/figures/`. Les tableaux existent en CSV, LaTeX (`.tex`) et Markdown (`.md`) dans `results/tables/`.

## Section « Données » (analyse exploratoire, `results/eda/`)

| Fichier | Légende proposée | Usage dans l'article |
|---|---|---|
| `T0_dataset_description` | Description du jeu BTS au hub CLT : vols, arrivées/jour, rotations appariées, retards, jours dégradés (train 2023 / test 2024). | Tableau 1 (données) |
| `F_eda1_delay_distributions` | Distributions empiriques des retards d'arrivée A et de départ D (échelle log) : forte asymétrie, 61 % d'arrivées en avance, queue lourde (Q99 ≈ 200 min). | Motive les marginales par quantiles (M2) |
| `F_eda2_hourly_profile` | Profil horaire : banques d'arrivées/départs du hub et retard moyen par heure (dérive croissante dans la journée). | Motive la classe (heure, régime) et le facteur horaire |
| `F_eda3_monthly_seasonality` | Saisonnalité mensuelle et nombre de jours en régime dégradé (été 2023, mai–juillet 2024). | Motive la chaîne de régimes (M1) et la séparation train/test |
| `F_eda4_delay_causes` | Décomposition BTS des minutes de retard : l'avion en retard (réactionnel) représente ~50 %. | Motive la propagation (M4) |
| `F_eda5_propagation_E_D_given_A` | Densité conjointe (A, D) et E[D \| A] : la propagation est quasi linéaire au-delà d'un slack de ~30 min. | Motive et valide M4 |
| `F_eda6_ground_time_by_category` | Temps au sol programmé par catégorie d'avion et temps minimal de rotation (Q5 des rotations très retardées). | Justifie MTT |
| `F_eda7_regime_effect` | Retard d'arrivée par régime journalier (boîtes) et profil horaire par régime. | Justifie le régime binaire |
| `F_eda8_heatmap_hour_month` | Carte heure × mois du retard moyen d'arrivée. | Illustration |
| `F_eda9_overdispersion` | Variance observée du nombre de retards par heure vs variance sous indépendance : indice de dispersion ≈ 3,9. | Preuve empirique de la corrélation entre vols |
| `F_eda10_daily_mean_delay` | Distribution du retard moyen journalier et seuil du régime dégradé. | Justifie le repli BTS |
| `F_eda11_carrier_category_region` | Parts des compagnies, des catégories d'avion (FAA) et des régions d'origine. | Décrit les facteurs de la copule |
| `F_eda12_causes_by_hour` | Part des causes de retard de départ par heure : le réactionnel domine en soirée. | Complément de F_eda4 |

## Section « Résultats » (`results/figures/`, `results/tables/`)

| Fichier | Légende proposée | Expérience |
|---|---|---|
| `T_params_dependence`, `T_params_mtt`, `T_params_parametric_aic` | Paramètres estimés (λ par régime, MTT, AIC des lois). | Estimation |
| `F1_qq_arrival_delay` | QQ-plots de A réel (2024) vs généré, par régime, pour les quatre générateurs. | E1 |
| `F1b_departure_delay_density` | Densité de D réel vs généré (log). | E1 |
| `T1_statistical_fidelity` | KS, Wasserstein, % > 15, Q95/Q99 pour A et D. | E1 |
| `T2_structure`, `T2b_conditional_departure`, `F3_conditional_departure` | Corrélations intra-groupe, indice de dispersion, part réactionnelle, E[D \| A] réel vs généré. | E2 |
| `T3_operational_impact` | Conflits/jour, biais, MAE, corrélation, réaffectations, détection des jours de pointe, par générateur, buffer et mode. | E3 |
| `T3b_before_after_{unconditional,conditioned}` | Tableau « avant / après » compact. | E3 |
| `F2_conflicts_per_day` | Distribution des conflits par jour (réel vs générateurs) et nuage réel/généré, deux modes. | E3 |
| `F2b_peak_days_scenarios` | Jours de pointe réels : boîtes des scénarios par générateur vs réel. | E3 |
| `F4_gantt_example` | Diagramme de Gantt stands × temps : programmé, réel, scénario dégradé. | E3 |
| `T4_sensitivity`, `F5_sensitivity` | Effet de `correlation_scale`, `peak_multiplier`, `forced_regime`, `n_scenarios`. | E4 |
| `T_lit1_delay_generators_comparison` | Positionnement vs générateurs de la littérature (cellules † à vérifier). | Related work |
| `T_lit2_bts_dataset_studies` | Travaux exploitant le jeu BTS. | Related work |
