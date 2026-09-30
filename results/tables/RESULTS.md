# Résultats — générateur de scénarios de retards, hub CLT

## T0 — Description du jeu de données

| Unnamed: 0              |   train (2023) |   test (2024) |    total |
|:------------------------|---------------:|--------------:|---------:|
| Vols (arr.+dép.)        |       383699   |      425685   | 809384   |
| Arrivées                |       191673   |      212676   | 404349   |
| Jours                   |          365   |         366   |    731   |
| Arrivées/jour           |          525.1 |         581.1 |    553.1 |
| Compagnies              |           12   |          12   |     12   |
| Immatriculations        |         3551   |        3584   |   3918   |
| Rotations appariées     |       161681   |      180330   | 342011   |
| Taux d'appariement (%)  |           84.4 |          84.8 |     84.6 |
| Retard arr. moyen (min) |            4.1 |           6.7 |      5.5 |
| Arrivées > 15 min (%)   |           18.1 |          21.2 |     19.7 |
| Q95 retard arr. (min)   |           77   |          90   |     84   |
| Jours dégradés          |           76   |          96   |    172   |

## Paramètres estimés (estimation 2023)

| régime   |   lambda_d |   lambda_h |   lambda_c |   lambda_r |   sigma_eps |   corr. même jour |   corr. jour+heure |   corr. jour+compagnie |   corr. jour+région |
|:---------|-----------:|-----------:|-----------:|-----------:|------------:|------------------:|-------------------:|-----------------------:|--------------------:|
| all      |      0.113 |      0.163 |      0.144 |      0.19  |       0.951 |             0.013 |              0.039 |                  0.033 |               0.049 |
| normal   |      0.118 |      0.113 |      0.145 |      0.188 |       0.958 |             0.014 |              0.027 |                  0.035 |               0.049 |
| degrade  |      0.103 |      0.27  |      0.155 |      0.196 |       0.924 |             0.011 |              0.084 |                  0.035 |               0.049 |

Temps minimaux de rotation (min) :

| catégorie   |   MTT programmé tendu (Q5, A≥30) |   temps sol réel Q5 |
|:------------|---------------------------------:|--------------------:|
| RJ          |                               44 |                  38 |
| NB          |                               47 |                  47 |
| WB          |                               60 |                  70 |

AIC des lois paramétriques décalées pour A (comparaison, l'option quantile reste la référence) :

| régime   |   lognorm |   gamma |   weibull_min |    norm |   expon | meilleure   |
|:---------|----------:|--------:|--------------:|--------:|--------:|:------------|
| normal   |   1372530 | 1404723 |       1463989 | 1509459 | 1574755 | lognorm     |
| degrade  |    392635 |  400227 |        407893 |  426965 |  423360 | lognorm     |

Chaîne de Markov des régimes : états ['normal', 'degrade'], matrice [[0.859, 0.141], [0.526, 0.474]], loi stationnaire [0.788, 0.212].

## T1 — Fidélité statistique (E1)

| generator       | label                               | variable   | scope   |   ks_stat |   wasserstein |   share_gt15_real |   share_gt15_gen |   q95_real |   q95_gen |   q99_real |   q99_gen |   mean_real |   mean_gen |   std_real |   std_gen |
|:----------------|:------------------------------------|:-----------|:--------|----------:|--------------:|------------------:|-----------------:|-----------:|----------:|-----------:|----------:|------------:|-----------:|-----------:|----------:|
| independent     | Indépendant (marginales seules)     | A          | all     |     0.034 |         2.488 |             0.211 |            0.188 |         90 |    78.794 |     203.01 |   190.371 |       6.679 |      4.33  |     43.124 |    38.998 |
| independent     | Indépendant (marginales seules)     | A          | normal  |     0.029 |         1.477 |             0.16  |            0.145 |         58 |    54.071 |     163    |   161.388 |       1.01  |     -0.209 |     35.487 |    32.506 |
| independent     | Indépendant (marginales seules)     | A          | degrade |     0.032 |         3.547 |             0.358 |            0.335 |        146 |   133.516 |     254    |   240.141 |      22.967 |     19.461 |     56.934 |    52.665 |
| independent     | Indépendant (marginales seules)     | D          | all     |     0.061 |         3.756 |             0.24  |            0.202 |         85 |    71.796 |     177    |   151.195 |      13.258 |      9.524 |     36.475 |    30.751 |
| hour_region     | Heure+région, sans propagation      | A          | all     |     0.035 |         2.568 |             0.211 |            0.187 |         90 |    78.358 |     203.01 |   191.183 |       6.679 |      4.238 |     43.124 |    38.96  |
| hour_region     | Heure+région, sans propagation      | A          | normal  |     0.029 |         1.479 |             0.16  |            0.144 |         58 |    54.023 |     163    |   162.132 |       1.01  |     -0.218 |     35.487 |    32.532 |
| hour_region     | Heure+région, sans propagation      | A          | degrade |     0.035 |         3.941 |             0.358 |            0.331 |        146 |   132.298 |     254    |   241.55  |      22.967 |     19.041 |     56.934 |    52.394 |
| hour_region     | Heure+région, sans propagation      | D          | all     |     0.061 |         3.756 |             0.24  |            0.202 |         85 |    71.796 |     177    |   151.195 |      13.258 |      9.524 |     36.475 |    30.751 |
| proposed_noprop | Proposé sans propagation (ablation) | A          | all     |     0.034 |         2.464 |             0.211 |            0.187 |         90 |    78.976 |     203.01 |   193.177 |       6.679 |      4.357 |     43.124 |    39.094 |
| proposed_noprop | Proposé sans propagation (ablation) | A          | normal  |     0.028 |         1.471 |             0.16  |            0.144 |         58 |    54.35  |     163    |   162.435 |       1.01  |     -0.198 |     35.487 |    32.51  |
| proposed_noprop | Proposé sans propagation (ablation) | A          | degrade |     0.032 |         3.554 |             0.358 |            0.334 |        146 |   132.944 |     254    |   241.776 |      22.967 |     19.455 |     56.934 |    52.704 |
| proposed_noprop | Proposé sans propagation (ablation) | D          | all     |     0.167 |         9.797 |             0.24  |            0.119 |         85 |    41.849 |     177    |   109.677 |      13.258 |      3.479 |     36.475 |    22.121 |
| proposed        | Proposé (complet)                   | A          | all     |     0.034 |         2.464 |             0.211 |            0.187 |         90 |    78.976 |     203.01 |   193.177 |       6.679 |      4.357 |     43.124 |    39.094 |
| proposed        | Proposé (complet)                   | A          | normal  |     0.028 |         1.471 |             0.16  |            0.144 |         58 |    54.35  |     163    |   162.435 |       1.01  |     -0.198 |     35.487 |    32.51  |
| proposed        | Proposé (complet)                   | A          | degrade |     0.032 |         3.554 |             0.358 |            0.334 |        146 |   132.944 |     254    |   241.776 |      22.967 |     19.455 |     56.934 |    52.704 |
| proposed        | Proposé (complet)                   | D          | all     |     0.045 |         1.896 |             0.24  |            0.21  |         85 |    83.996 |     177    |   178.845 |      13.258 |     11.408 |     36.475 |    35.144 |

## T2 — Structure (E2)

| generator       | label                               |   corr_hour |   corr_carrier |   corr_region |   dispersion_index |   reactionary_share |
|:----------------|:------------------------------------|------------:|---------------:|--------------:|-------------------:|--------------------:|
| real            | Réel                                |       0.058 |          0.004 |         0.009 |              3.167 |               0.432 |
| independent     | Indépendant (marginales seules)     |       0.028 |         -0.002 |        -0.002 |              1.75  |               0     |
| hour_region     | Heure+région, sans propagation      |       0.044 |         -0.001 |         0.01  |              2.233 |               0     |
| proposed_noprop | Proposé sans propagation (ablation) |       0.045 |          0.004 |         0.01  |              2.467 |               0     |
| proposed        | Proposé (complet)                   |       0.045 |          0.004 |         0.01  |              2.467 |               0.583 |

## T2b — E[D | A] réel vs généré

| bin      | label                               |      n |   mean |   median |     q90 |   share_gt15 | generator       |
|:---------|:------------------------------------|-------:|-------:|---------:|--------:|-------------:|:----------------|
| A<=0     | Réel                                | 113845 |  4.604 |   -3     |  22     |        0.126 | real            |
| 0<A<=15  | Réel                                |  32001 | 10.302 |    1     |  34     |        0.205 | real            |
| 15<A<=45 | Réel                                |  19452 | 24.247 |   17     |  55     |        0.524 | real            |
| A>45     | Réel                                |  15032 | 70.878 |   59     | 153     |        0.809 | real            |
| A<=0     | Indépendant (marginales seules)     | 350618 |  7.885 |   -2     |  34.675 |        0.181 | independent     |
| 0<A<=15  | Indépendant (marginales seules)     |  92327 | 10.027 |   -2     |  41.584 |        0.207 | independent     |
| 15<A<=45 | Indépendant (marginales seules)     |  52978 | 13.308 |   -1     |  51.911 |        0.248 | independent     |
| A>45     | Indépendant (marginales seules)     |  45067 | 16.738 |    0     |  64.709 |        0.288 | independent     |
| A<=0     | Heure+région, sans propagation      | 351378 |  7.888 |   -2     |  34.687 |        0.181 | hour_region     |
| 0<A<=15  | Heure+région, sans propagation      |  92267 | 10.183 |   -2     |  42.045 |        0.209 | hour_region     |
| 15<A<=45 | Heure+région, sans propagation      |  52738 | 13.3   |   -1     |  52.503 |        0.248 | hour_region     |
| A>45     | Heure+région, sans propagation      |  44607 | 16.527 |    0     |  63.502 |        0.285 | hour_region     |
| A<=0     | Proposé sans propagation (ablation) | 350700 |  2.437 |   -3     |  16.135 |        0.105 | proposed_noprop |
| 0<A<=15  | Proposé sans propagation (ablation) |  92646 |  4.004 |   -3     |  21.195 |        0.125 | proposed_noprop |
| 15<A<=45 | Proposé sans propagation (ablation) |  52554 |  5.942 |   -3     |  27.093 |        0.148 | proposed_noprop |
| A>45     | Proposé sans propagation (ablation) |  45090 |  8.168 |   -2     |  35.449 |        0.179 | proposed_noprop |
| A<=0     | Proposé (complet)                   | 350700 |  2.496 |   -3     |  16.135 |        0.105 | proposed        |
| 0<A<=15  | Proposé (complet)                   |  92646 |  6.155 |    0     |  21.195 |        0.125 | proposed        |
| 15<A<=45 | Proposé (complet)                   |  52554 | 17.776 |   14     |  37.767 |        0.474 | proposed        |
| A>45     | Proposé (complet)                   |  45090 | 85.659 |   70.694 | 181.892 |        0.906 | proposed        |

## T3 — Impact opérationnel (E3)

| mode          | label                               |   buffer | generator       |   conflicts_per_day_real |   conflicts_per_day_gen |   bias_pct |   mae_daily |   corr_daily |   spearman_daily |   peak_auc |   overlap_real |   overlap_gen |   reassign_real |   reassign_gen |   waiting_real |   waiting_gen |   peak_days |   peak_detection_rate |   peak_false_alarm_rate |   coverage_real_in_scenarios |   real_above_all_scenarios | generator_label                     |
|:--------------|:------------------------------------|---------:|:----------------|-------------------------:|------------------------:|-----------:|------------:|-------------:|-----------------:|-----------:|---------------:|--------------:|----------------:|---------------:|---------------:|--------------:|------------:|----------------------:|------------------------:|-----------------------------:|---------------------------:|:------------------------------------|
| unconditional | Indépendant (marginales seules)     |        5 | independent     |                  143.197 |                 125.1   |    -12.637 |      21.762 |        0.615 |            0.603 |      0.667 |        5446.12 |      3471.38  |         356.885 |        340.938 |          6.811 |         5.679 |          12 |                     0 |                       0 |                        0.607 |                      0.23  | Indépendant (marginales seules)     |
| unconditional | Heure+région, sans propagation      |        5 | hour_region     |                  143.197 |                 125.076 |    -12.654 |      21.892 |        0.61  |            0.597 |      0.679 |        5446.12 |      3471.52  |         356.885 |        341.725 |          6.811 |         4.927 |          12 |                     0 |                       0 |                        0.697 |                      0.156 | Heure+région, sans propagation      |
| unconditional | Proposé sans propagation (ablation) |        5 | proposed_noprop |                  143.197 |                 102.006 |    -28.765 |      41.219 |        0.596 |            0.591 |      0.651 |        5446.12 |      2030.47  |         356.885 |        295.853 |          6.811 |         3.01  |          12 |                     0 |                       0 |                        0.23  |                      0.5   | Proposé sans propagation (ablation) |
| unconditional | Proposé (complet)                   |        5 | proposed        |                  143.197 |                 130.144 |     -9.115 |      19.247 |        0.594 |            0.581 |      0.652 |        5446.12 |      3865.63  |         356.885 |        341.273 |          6.811 |         3.935 |          12 |                     0 |                       0 |                        0.68  |                      0.131 | Proposé (complet)                   |
| unconditional | Indépendant (marginales seules)     |       15 | independent     |                   69.918 |                  51.921 |    -25.74  |      22.738 |        0.312 |            0.39  |      0.548 |        3595.08 |      1955.8   |         241.049 |        212.868 |          7.492 |         3.443 |          13 |                     0 |                       0 |                        0.746 |                      0.164 | Indépendant (marginales seules)     |
| unconditional | Heure+région, sans propagation      |       15 | hour_region     |                   69.918 |                  51.904 |    -25.765 |      22.745 |        0.31  |            0.386 |      0.535 |        3595.08 |      1956.92  |         241.049 |        213.853 |          7.492 |         2.995 |          13 |                     0 |                       0 |                        0.762 |                      0.148 | Heure+région, sans propagation      |
| unconditional | Proposé sans propagation (ablation) |       15 | proposed_noprop |                   69.918 |                  31.334 |    -55.185 |      38.798 |        0.315 |            0.382 |      0.567 |        3595.08 |       935.527 |         241.049 |        157.644 |          7.492 |         1.874 |          13 |                     0 |                       0 |                        0.336 |                      0.41  | Proposé sans propagation (ablation) |
| unconditional | Proposé (complet)                   |       15 | proposed        |                   69.918 |                  54.172 |    -22.521 |      22.065 |        0.237 |            0.296 |      0.469 |        3595.08 |      2312.78  |         241.049 |        208.311 |          7.492 |         3.07  |          13 |                     0 |                       0 |                        0.803 |                      0.09  | Proposé (complet)                   |
| conditioned   | Indépendant (marginales seules)     |        5 | independent     |                  143.197 |                 125.653 |    -12.251 |      21.202 |        0.722 |            0.711 |      0.895 |        5446.12 |      3529.34  |         356.885 |        340.532 |          6.811 |         4.576 |          12 |                     0 |                       0 |                        0.41  |                      0.377 | Indépendant (marginales seules)     |
| conditioned   | Heure+région, sans propagation      |        5 | hour_region     |                  143.197 |                 125.619 |    -12.276 |      21.171 |        0.723 |            0.715 |      0.903 |        5446.12 |      3528.26  |         356.885 |        341.515 |          6.811 |         4.772 |          12 |                     0 |                       0 |                        0.598 |                      0.246 | Heure+région, sans propagation      |
| conditioned   | Proposé sans propagation (ablation) |        5 | proposed_noprop |                  143.197 |                 102.158 |    -28.659 |      41.154 |        0.573 |            0.567 |      0.62  |        5446.12 |      2052.95  |         356.885 |        295.038 |          6.811 |         2.111 |          12 |                     0 |                       0 |                        0.23  |                      0.557 | Proposé sans propagation (ablation) |
| conditioned   | Proposé (complet)                   |        5 | proposed        |                  143.197 |                 130.205 |     -9.073 |      18.45  |        0.698 |            0.693 |      0.833 |        5446.12 |      3882.91  |         356.885 |        339.996 |          6.811 |         3.937 |          12 |                     0 |                       0 |                        0.648 |                      0.197 | Proposé (complet)                   |
| conditioned   | Indépendant (marginales seules)     |       15 | independent     |                   69.918 |                  52.531 |    -24.868 |      20.637 |        0.731 |            0.674 |      0.949 |        3595.08 |      2001.5   |         241.049 |        213.145 |          7.492 |         3.217 |          13 |                     0 |                       0 |                        0.336 |                      0.492 | Indépendant (marginales seules)     |
| conditioned   | Heure+région, sans propagation      |       15 | hour_region     |                   69.918 |                  52.508 |    -24.901 |      20.644 |        0.733 |            0.672 |      0.951 |        3595.08 |      2000.97  |         241.049 |        214.471 |          7.492 |         4.317 |          13 |                     0 |                       0 |                        0.344 |                      0.434 | Heure+région, sans propagation      |
| conditioned   | Proposé sans propagation (ablation) |       15 | proposed_noprop |                   69.918 |                  31.695 |    -54.669 |      38.425 |        0.722 |            0.665 |      0.935 |        3595.08 |       958.588 |         241.049 |        157.157 |          7.492 |         1.482 |          13 |                     0 |                       0 |                        0.123 |                      0.664 | Proposé sans propagation (ablation) |
| conditioned   | Proposé (complet)                   |       15 | proposed        |                   69.918 |                  54.541 |    -21.993 |      19.383 |        0.701 |            0.636 |      0.934 |        3595.08 |      2337.07  |         241.049 |        207.317 |          7.492 |         2.475 |          13 |                     0 |                       0 |                        0.623 |                      0.156 | Proposé (complet)                   |

## T3b — Avant / après (régime tiré par le générateur)

| Indicateur (b = 5 min, moyenne par jour)    |   Réel (BTS 2024) |   Avant : indépendant |   Avant : heure+région (≈ Dijk et al.) |   Après : proposé sans propagation |   Après : proposé complet |
|:--------------------------------------------|------------------:|----------------------:|-----------------------------------------:|-----------------------------------:|--------------------------:|
| Conflits de stands / jour                   |           143.197 |               125.1   |                                  125.076 |                            102.006 |                   130.144 |
| Écart au réel (%)                           |             0     |               -12.637 |                                  -12.654 |                            -28.765 |                    -9.115 |
| MAE journalière (conflits)                  |             0     |                21.762 |                                   21.892 |                             41.219 |                    19.247 |
| Corrélation jour à jour avec le réel        |             1     |                 0.615 |                                    0.61  |                              0.596 |                     0.594 |
| Spearman jour à jour                        |             1     |                 0.603 |                                    0.597 |                              0.591 |                     0.581 |
| AUC détection des jours de pointe (Q90)     |             1     |                 0.667 |                                    0.679 |                              0.651 |                     0.652 |
| Minutes de chevauchement / jour             |          5446.12  |              3471.38  |                                 3471.52  |                           2030.47  |                  3865.63  |
| Réaffectations / jour                       |           356.885 |               340.938 |                                  341.725 |                            295.853 |                   341.273 |
| Réel dans [Q5, Q95] des scénarios           |             1     |                 0.607 |                                    0.697 |                              0.23  |                     0.68  |
| Jours où le réel dépasse tous les scénarios |             0     |                 0.23  |                                    0.156 |                              0.5   |                     0.131 |

## T3b — Avant / après (régime réel du jour connu)

| Indicateur (b = 5 min, moyenne par jour)    |   Réel (BTS 2024) |   Avant : indépendant |   Avant : heure+région (≈ Dijk et al.) |   Après : proposé sans propagation |   Après : proposé complet |
|:--------------------------------------------|------------------:|----------------------:|-----------------------------------------:|-----------------------------------:|--------------------------:|
| Conflits de stands / jour                   |           143.197 |               125.653 |                                  125.619 |                            102.158 |                   130.205 |
| Écart au réel (%)                           |             0     |               -12.251 |                                  -12.276 |                            -28.659 |                    -9.073 |
| MAE journalière (conflits)                  |             0     |                21.202 |                                   21.171 |                             41.154 |                    18.45  |
| Corrélation jour à jour avec le réel        |             1     |                 0.722 |                                    0.723 |                              0.573 |                     0.698 |
| Spearman jour à jour                        |             1     |                 0.711 |                                    0.715 |                              0.567 |                     0.693 |
| AUC détection des jours de pointe (Q90)     |             1     |                 0.895 |                                    0.903 |                              0.62  |                     0.833 |
| Minutes de chevauchement / jour             |          5446.12  |              3529.34  |                                 3528.26  |                           2052.95  |                  3882.91  |
| Réaffectations / jour                       |           356.885 |               340.532 |                                  341.515 |                            295.038 |                   339.996 |
| Réel dans [Q5, Q95] des scénarios           |             1     |                 0.41  |                                    0.598 |                              0.23  |                     0.648 |
| Jours où le réel dépasse tous les scénarios |             0     |                 0.377 |                                    0.246 |                              0.557 |                     0.197 |

## T4 — Sensibilité (E4)

| parameter         | value   |   real_conflicts |   conflicts_mean |   conflicts_q90 |   conflicts_std |   A_mean |   A_gt15 |   D_mean |   bias_pct |
|:------------------|:--------|-----------------:|-----------------:|----------------:|----------------:|---------:|---------:|---------:|-----------:|
| correlation_scale | 0.0     |          141.933 |          131.651 |         145.453 |          10.235 |    3.416 |    0.16  |    8.414 |     -7.244 |
| correlation_scale | 0.5     |          141.933 |          134.083 |         151.463 |          13.6   |    3.402 |    0.16  |    8.948 |     -5.531 |
| correlation_scale | 1.0     |          141.933 |          133.85  |         151.27  |          13.636 |    3.384 |    0.16  |    8.916 |     -5.695 |
| correlation_scale | 1.5     |          141.933 |          133.501 |         153.307 |          15.258 |    3.361 |    0.16  |    8.882 |     -5.941 |
| peak_multiplier   | 1.0     |          141.933 |          133.85  |         151.27  |          13.636 |    3.384 |    0.16  |    8.916 |     -5.695 |
| peak_multiplier   | 1.25    |          141.933 |          135.466 |         152.983 |          13.629 |    5.009 |    0.171 |   10.043 |     -4.557 |
| peak_multiplier   | 1.5     |          141.933 |          136.913 |         154.75  |          13.64  |    6.635 |    0.18  |   11.206 |     -3.537 |
| forced_regime     | normal  |          141.933 |          130.62  |         145.213 |          11.509 |   -0.011 |    0.127 |    5.882 |     -7.971 |
| forced_regime     | degrade |          141.933 |          146.483 |         163.873 |          13.389 |   17.032 |    0.292 |   20.942 |      3.205 |
| propagation       | 0.0     |          141.933 |          104.812 |         123.563 |          14.725 |    3.384 |    0.16  |    2.488 |    -26.154 |
| propagation       | 1.0     |          141.933 |          133.85  |         151.27  |          13.636 |    3.384 |    0.16  |    8.916 |     -5.695 |
| n_scenarios       | 10      |          141.933 |          133.273 |         145.993 |          11.93  |    3.422 |    0.161 |    8.794 |     -6.101 |
| n_scenarios       | 30      |          141.933 |          134.213 |         149.397 |          12.442 |    3.208 |    0.158 |    8.787 |     -5.439 |
| n_scenarios       | 100     |          141.933 |          133.85  |         151.27  |          13.636 |    3.384 |    0.16  |    8.916 |     -5.695 |
| n_scenarios       | 300     |          141.933 |          133.67  |         151.49  |          13.594 |    3.498 |    0.161 |    8.956 |     -5.822 |

Temps de calcul (validation) : `{"generation_seconds_total": {"independent": 50.54895544052124, "hour_region": 50.655823707580566, "proposed_noprop": 54.36014795303345, "proposed": 54.6248095035553}, "n_days": 366, "n_scenarios": 100, "rotations_per_day_mean": 670.3688524590164}`

Temps de calcul (allocation) : `{"n_days": 122, "buffers": [5.0, 15.0], "n_scenarios": 100, "modes": ["unconditional", "conditioned"], "milp_runtime_mean": 29.845172525429334, "milp_status": {"GREEDY_FALLBACK": 220, "FEASIBLE": 24}, "milp_unassigned_mean": 1.2336065573770492, "stands_mean": 124.72950819672131, "rotations_mean": 670.311475409836}`

## T_lit1_delay_generators_comparison

| Référence                            | Aéroport / données                         | Données publiques   | Marginales des retards                                               | Corrélation entre vols                                        | Propagation arrivée→départ           | Régimes météo            | Validation                                                                               | Générateur ouvert         |
|:-------------------------------------|:-------------------------------------------|:--------------------|:---------------------------------------------------------------------|:--------------------------------------------------------------|:-------------------------------------|:-------------------------|:-----------------------------------------------------------------------------------------|:--------------------------|
| Yan & Tang (2007) EJOR               | CKS Taipei †                               | non                 | lois ajustées sur historique †                                       | non                                                           | non                                  | non                      | simulation des affectations                                                              | non                       |
| Şeker & Noyan (2012) TRE             | scénarios de retards (grand aéroport US) † | non                 | scénarios échantillonnés †                                           | non                                                           | non                                  | non                      | programmation stochastique (objectif)                                                    | non                       |
| Diepen et al. (2012) J. Sched.       | Amsterdam Schiphol                         | non                 | aucune (robustesse par temps libre)                                  | non                                                           | non                                  | non                      | rejeu sur retards réels †                                                                | non                       |
| Castaing et al. (2016) COR           | hub US (données compagnie) †               | non                 | historique de retards échantillonné †                                | non                                                           | non                                  | non                      | blocages de portes simulés                                                               | non                       |
| Xu et al. (2017) TRB                 | cas d'étude (budget d'incertitude)         | non                 | intervalles bornés (pas de loi)                                      | budget global                                                 | non                                  | non                      | pire cas partiel                                                                         | non                       |
| Dorndorf et al. (2017) OR Spectrum   | hub européen (données privées) †           | non                 | arrivées/départs stochastiques †                                     | non                                                           | partiel (recours) †                  | non                      | simulation + stratégies de recours                                                       | non                       |
| Dijk et al. (2019) OR Spectrum     | São Paulo–Guarulhos (GRU)                  | non                 | loi par vol (normale, exp., gamma, Weibull)                          | région d'origine × fenêtre horaire                            | non (départs fixés)                  | non                      | 30 scénarios, recours (attente, réaffectation, remorquage)                               | non                       |
| Bagamanova & Mujica Mota (2020) JATM | aéroport (simulation) †                    | non                 | composante « delay-aware » (simulation) †                            | non                                                           | partiel †                            | non                      | simulation                                                                               | non                       |
| Park & Ku (2026) Aerospace           | Gimpo (GMP)                                | non                 | simulation fast-time des mouvements sol                              | implicite (simulation)                                        | implicite (simulation)               | non                      | une journée simulée                                                                      | non                       |
| Cette étude (2026)                   | Charlotte (CLT), BTS 2023–2024             | oui                 | quantiles empiriques par (heure, régime) [+ lois paramétriques, AIC] | copule gaussienne à facteurs : jour, heure, compagnie, région | oui (MTT, slack, retard réactionnel) | chaîne de Markov 2 états | 3 niveaux : statistique, structurel, opérationnel (conflits réels vs générés, 366 jours) | oui (package + benchmark) |

## T_lit2_bts_dataset_studies

| Référence                          | Données                                                   | Objectif                                                                                             | Niveau d'analyse                   | Lien avec l'allocation de stands   |
|:-----------------------------------|:----------------------------------------------------------|:-----------------------------------------------------------------------------------------------------|:-----------------------------------|:-----------------------------------|
| Tu, Ball & Jank (2008) JASA        | retards de départ, une compagnie à Denver †               | loi de retard de départ (mélange, tendance saisonnière)                                              | vol                                | non                                |
| Deshpande & Arikan (2012) MSOM     | BTS On-Time Performance                                   | effet des horaires (block time) sur les retards                                                      | vol / compagnie                    | non                                |
| Rebollo & Balakrishnan (2014) TR-C | BTS / ASPM, réseau US                                     | prédiction des retards réseau (classification, régression)                                           | réseau / paire OD                  | non                                |
| Kafle & Zou (2016) TR-B            | BTS On-Time Performance                                   | propagation des retards (approche analytique-économétrique)                                          | rotation / compagnie               | non                                |
| Sternberg et al. (2017) arXiv      | revue (BTS majoritaire)                                   | revue des méthodes de prédiction de retards                                                          | —                                  | non                                |
| Wu et al. (2024) TR-E              | revue (BTS, Eurocontrol)                                  | revue : propagation des retards, données et méthodes                                                 | —                                  | non                                |
| Cette étude (2026)                 | BTS On-Time Performance 2023–2024, hub CLT + registre FAA | générateur de scénarios (marginales, copule, propagation, régimes) validé sur les conflits de stands | rotation au hub (arrivée + départ) | oui                                |
