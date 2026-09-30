# Résultats — générateur de scénarios de retards, hub CLT

## Paramètres estimés (estimation 2024)

| régime   |   lambda_d |   lambda_h |   lambda_c |   lambda_r |   sigma_eps |   corr. même jour |   corr. jour+heure |   corr. jour+compagnie |   corr. jour+région |
|:---------|-----------:|-----------:|-----------:|-----------:|------------:|------------------:|-------------------:|-----------------------:|--------------------:|
| all      |      0.163 |      0.171 |      0.118 |      0.199 |       0.944 |             0.027 |              0.056 |                   0.04 |               0.066 |
| normal   |      0.136 |      0.095 |      0.108 |      0.199 |       0.96  |             0.018 |              0.027 |                   0.03 |               0.058 |
| degrade  |      0.229 |      0.269 |      0.132 |      0.198 |       0.905 |             0.052 |              0.125 |                   0.07 |               0.091 |

Temps minimaux de rotation (min) :

| catégorie   |   MTT programmé tendu (Q5, A≥30) |   temps sol réel Q5 |
|:------------|---------------------------------:|--------------------:|
| RJ          |                               40 |                  36 |
| NB          |                               45 |                  47 |
| WB          |                               60 |                  80 |

AIC des lois paramétriques décalées pour A (comparaison, l'option quantile reste la référence) :

| régime   |   lognorm |   gamma |   weibull_min |    norm |   expon | meilleure   |
|:---------|----------:|--------:|--------------:|--------:|--------:|:------------|
| normal   |   1438567 | 1470704 |       1532996 | 1571565 | 1658118 | lognorm     |
| degrade  |    555503 |  565992 |        575780 |  602280 |  596267 | lognorm     |

Chaîne de Markov des régimes : états ['normal', 'degrade'], matrice [[0.86, 0.14], [0.388, 0.612]], loi stationnaire [0.734, 0.266].

## T1 — Fidélité statistique (E1)

| generator       | label                               | variable   | scope   |   ks_stat |   wasserstein |   share_gt15_real |   share_gt15_gen |   q95_real |   q95_gen |   q99_real |   q99_gen |   mean_real |   mean_gen |   std_real |   std_gen |
|:----------------|:------------------------------------|:-----------|:--------|----------:|--------------:|------------------:|-----------------:|-----------:|----------:|-----------:|----------:|------------:|-----------:|-----------:|----------:|
| independent     | Indépendant (marginales seules)     | A          | all     |     0.009 |         0.887 |             0.211 |            0.22  |         90 |    93.252 |     203.01 |   203.061 |       6.679 |      7.182 |     43.124 |    42.587 |
| independent     | Indépendant (marginales seules)     | A          | normal  |     0.004 |         0.408 |             0.16  |            0.163 |         58 |    58.136 |     163    |   162.691 |       1.01  |      0.721 |     35.487 |    33.448 |
| independent     | Indépendant (marginales seules)     | A          | degrade |     0.004 |         0.375 |             0.358 |            0.361 |        146 |   147.332 |     254    |   251.184 |      22.967 |     22.965 |     56.934 |    56.357 |
| independent     | Indépendant (marginales seules)     | D          | all     |     0.012 |         0.841 |             0.24  |            0.251 |         85 |    88.481 |     177    |   172.07  |      13.258 |     13.746 |     36.475 |    35.889 |
| hour_region     | Heure+région, sans propagation      | A          | all     |     0.01  |         0.832 |             0.211 |            0.22  |         90 |    92.744 |     203.01 |   201.185 |       6.679 |      7.097 |     43.124 |    42.339 |
| hour_region     | Heure+région, sans propagation      | A          | normal  |     0.005 |         0.405 |             0.16  |            0.162 |         58 |    58.176 |     163    |   163.7   |       1.01  |      0.728 |     35.487 |    33.506 |
| hour_region     | Heure+région, sans propagation      | A          | degrade |     0.005 |         0.347 |             0.358 |            0.36  |        146 |   146.456 |     254    |   249.891 |      22.967 |     22.786 |     56.934 |    56.13  |
| hour_region     | Heure+région, sans propagation      | D          | all     |     0.012 |         0.841 |             0.24  |            0.251 |         85 |    88.481 |     177    |   172.07  |      13.258 |     13.746 |     36.475 |    35.889 |
| proposed_noprop | Proposé sans propagation (ablation) | A          | all     |     0.009 |         0.775 |             0.211 |            0.22  |         90 |    92.239 |     203.01 |   200.334 |       6.679 |      7.021 |     43.124 |    42.23  |
| proposed_noprop | Proposé sans propagation (ablation) | A          | normal  |     0.005 |         0.415 |             0.16  |            0.163 |         58 |    57.625 |     163    |   163.608 |       1.01  |      0.694 |     35.487 |    33.453 |
| proposed_noprop | Proposé sans propagation (ablation) | A          | degrade |     0.006 |         0.472 |             0.358 |            0.358 |        146 |   145.745 |     254    |   248.528 |      22.967 |     22.567 |     56.934 |    55.858 |
| proposed_noprop | Proposé sans propagation (ablation) | D          | all     |     0.118 |         7.111 |             0.24  |            0.15  |         85 |    53.732 |     177    |   135.891 |      13.258 |      6.155 |     36.475 |    26.777 |
| proposed        | Proposé (complet)                   | A          | all     |     0.009 |         0.775 |             0.211 |            0.22  |         90 |    92.239 |     203.01 |   200.334 |       6.679 |      7.021 |     43.124 |    42.23  |
| proposed        | Proposé (complet)                   | A          | normal  |     0.005 |         0.415 |             0.16  |            0.163 |         58 |    57.625 |     163    |   163.608 |       1.01  |      0.694 |     35.487 |    33.453 |
| proposed        | Proposé (complet)                   | A          | degrade |     0.006 |         0.472 |             0.358 |            0.358 |        146 |   145.745 |     254    |   248.528 |      22.967 |     22.567 |     56.934 |    55.858 |
| proposed        | Proposé (complet)                   | D          | all     |     0.014 |         1.611 |             0.24  |            0.246 |         85 |    98.36  |     177    |   191.45  |      13.258 |     14.722 |     36.475 |    39.113 |

## T2 — Structure (E2)

| generator       | label                               |   corr_hour |   corr_carrier |   corr_region |   dispersion_index |   reactionary_share |
|:----------------|:------------------------------------|------------:|---------------:|--------------:|-------------------:|--------------------:|
| real            | Réel                                |       0.058 |          0.004 |         0.009 |              3.167 |               0.432 |
| independent     | Indépendant (marginales seules)     |       0.045 |         -0.002 |        -0.002 |              1.8   |               0     |
| hour_region     | Heure+région, sans propagation      |       0.062 |         -0.001 |         0.011 |              2.295 |               0     |
| proposed_noprop | Proposé sans propagation (ablation) |       0.065 |          0.002 |         0.011 |              2.696 |               0     |
| proposed        | Proposé (complet)                   |       0.065 |          0.002 |         0.011 |              2.696 |               0.553 |

## T2b — E[D | A] réel vs généré

| bin      | label                               |      n |   mean |   median |     q90 |   share_gt15 | generator       |
|:---------|:------------------------------------|-------:|-------:|---------:|--------:|-------------:|:----------------|
| A<=0     | Réel                                | 113845 |  4.604 |   -3     |  22     |        0.126 | real            |
| 0<A<=15  | Réel                                |  32001 | 10.302 |    1     |  34     |        0.205 | real            |
| 15<A<=45 | Réel                                |  19452 | 24.247 |   17     |  55     |        0.524 | real            |
| A>45     | Réel                                |  15032 | 70.878 |   59     | 153     |        0.809 | real            |
| A<=0     | Indépendant (marginales seules)     | 331890 | 11.02  |   -1     |  43.134 |        0.219 | independent     |
| 0<A<=15  | Indépendant (marginales seules)     |  94153 | 14.264 |   -1     |  53.341 |        0.258 | independent     |
| 15<A<=45 | Indépendant (marginales seules)     |  60359 | 18.391 |    1     |  66.872 |        0.302 | independent     |
| A>45     | Indépendant (marginales seules)     |  54588 | 24.102 |    3.855 |  82.229 |        0.365 | independent     |
| A<=0     | Heure+région, sans propagation      | 331929 | 11.004 |   -1     |  43.042 |        0.219 | hour_region     |
| 0<A<=15  | Heure+région, sans propagation      |  94354 | 14.313 |   -1     |  53.742 |        0.256 | hour_region     |
| 15<A<=45 | Heure+région, sans propagation      |  60267 | 18.454 |    1     |  66.627 |        0.305 | hour_region     |
| A>45     | Heure+région, sans propagation      |  54440 | 24.082 |    3.806 |  82.347 |        0.364 | hour_region     |
| A<=0     | Proposé sans propagation (ablation) | 332117 |  4.301 |   -3     |  21.454 |        0.128 | proposed_noprop |
| 0<A<=15  | Proposé sans propagation (ablation) |  94372 |  6.744 |   -2     |  28.817 |        0.157 | proposed_noprop |
| 15<A<=45 | Proposé sans propagation (ablation) |  60273 |  9.131 |   -2     |  36.281 |        0.186 | proposed_noprop |
| A>45     | Proposé sans propagation (ablation) |  54228 | 13.525 |   -1     |  51.592 |        0.234 | proposed_noprop |
| A<=0     | Proposé (complet)                   | 332117 |  4.33  |   -3     |  21.454 |        0.128 | proposed        |
| 0<A<=15  | Proposé (complet)                   |  94372 |  8.189 |    0     |  28.817 |        0.157 | proposed        |
| 15<A<=45 | Proposé (complet)                   |  60273 | 18.627 |   12.495 |  39.605 |        0.442 | proposed        |
| A>45     | Proposé (complet)                   |  54228 | 87.258 |   71.892 | 183.001 |        0.911 | proposed        |

## T3 — Impact opérationnel (E3)

| mode          | label                               |   buffer | generator       |   conflicts_per_day_real |   conflicts_per_day_gen |   bias_pct |   mae_daily |   corr_daily |   spearman_daily |   peak_auc |   overlap_real |   overlap_gen |   reassign_real |   reassign_gen |   waiting_real |   waiting_gen |   peak_days |   peak_detection_rate |   peak_false_alarm_rate |   coverage_real_in_scenarios |   real_above_all_scenarios | generator_label                     |
|:--------------|:------------------------------------|---------:|:----------------|-------------------------:|------------------------:|-----------:|------------:|-------------:|-----------------:|-----------:|---------------:|--------------:|----------------:|---------------:|---------------:|--------------:|------------:|----------------------:|------------------------:|-----------------------------:|---------------------------:|:------------------------------------|
| unconditional | Indépendant (marginales seules)     |        5 | independent     |                  143.197 |                 134.713 |     -5.925 |      17.467 |        0.612 |            0.592 |      0.67  |        5446.12 |       4225.89 |         356.885 |        356.509 |          6.811 |         4.881 |          12 |                     0 |                       0 |                        0.713 |                      0.098 | Indépendant (marginales seules)     |
| unconditional | Heure+région, sans propagation      |        5 | hour_region     |                  143.197 |                 134.624 |     -5.987 |      17.537 |        0.608 |            0.586 |      0.673 |        5446.12 |       4225.24 |         356.885 |        356.675 |          6.811 |         5.411 |          12 |                     0 |                       0 |                        0.795 |                      0.074 | Heure+région, sans propagation      |
| unconditional | Proposé sans propagation (ablation) |        5 | proposed_noprop |                  143.197 |                 107.55  |    -24.893 |      35.946 |        0.605 |            0.596 |      0.652 |        5446.12 |       2467.03 |         356.885 |        304.88  |          6.811 |         2.114 |          12 |                     0 |                       0 |                        0.328 |                      0.41  | Proposé sans propagation (ablation) |
| unconditional | Proposé (complet)                   |        5 | proposed        |                  143.197 |                 135.526 |     -5.357 |      17.558 |        0.595 |            0.574 |      0.661 |        5446.12 |       4403.55 |         356.885 |        347.18  |          6.811 |         3.257 |          12 |                     0 |                       0 |                        0.705 |                      0.09  | Proposé (complet)                   |
| unconditional | Indépendant (marginales seules)     |       15 | independent     |                   69.918 |                  61.681 |    -11.781 |      19.652 |        0.312 |            0.375 |      0.549 |        3595.08 |       2536.12 |         241.049 |        230.837 |          7.492 |         4.308 |          13 |                     0 |                       0 |                        0.746 |                      0.115 | Indépendant (marginales seules)     |
| unconditional | Heure+région, sans propagation      |       15 | hour_region     |                   69.918 |                  61.673 |    -11.792 |      19.638 |        0.311 |            0.375 |      0.553 |        3595.08 |       2535.74 |         241.049 |        231.97  |          7.492 |         4.518 |          13 |                     0 |                       0 |                        0.762 |                      0.066 | Heure+région, sans propagation      |
| unconditional | Proposé sans propagation (ablation) |       15 | proposed_noprop |                   69.918 |                  37.024 |    -47.046 |      33.454 |        0.341 |            0.406 |      0.6   |        3595.08 |       1259.79 |         241.049 |        169.528 |          7.492 |         1.796 |          13 |                     0 |                       0 |                        0.451 |                      0.27  | Proposé sans propagation (ablation) |
| unconditional | Proposé (complet)                   |       15 | proposed        |                   69.918 |                  60.896 |    -12.904 |      20.315 |        0.244 |            0.298 |      0.503 |        3595.08 |       2744.3  |         241.049 |        216.647 |          7.492 |         3.135 |          13 |                     0 |                       0 |                        0.82  |                      0.057 | Proposé (complet)                   |
| conditioned   | Indépendant (marginales seules)     |        5 | independent     |                  143.197 |                 134.071 |     -6.373 |      16.445 |        0.726 |            0.719 |      0.906 |        5446.12 |       4072.01 |         356.885 |        354.62  |          6.811 |         5.38  |          12 |                     0 |                       0 |                        0.541 |                      0.246 | Indépendant (marginales seules)     |
| conditioned   | Heure+région, sans propagation      |        5 | hour_region     |                  143.197 |                 134.087 |     -6.362 |      16.355 |        0.728 |            0.719 |      0.912 |        5446.12 |       4070.82 |         356.885 |        355.005 |          6.811 |         5.622 |          12 |                     0 |                       0 |                        0.713 |                      0.131 | Heure+région, sans propagation      |
| conditioned   | Proposé sans propagation (ablation) |        5 | proposed_noprop |                  143.197 |                 107.864 |    -24.674 |      35.758 |        0.583 |            0.579 |      0.641 |        5446.12 |       2401.87 |         356.885 |        306.129 |          6.811 |         2.967 |          12 |                     0 |                       0 |                        0.336 |                      0.484 | Proposé sans propagation (ablation) |
| conditioned   | Proposé (complet)                   |        5 | proposed        |                  143.197 |                 134.773 |     -5.883 |      16.305 |        0.701 |            0.697 |      0.842 |        5446.12 |       4225.85 |         356.885 |        346.745 |          6.811 |         4.636 |          12 |                     0 |                       0 |                        0.689 |                      0.115 | Proposé (complet)                   |
| conditioned   | Indépendant (marginales seules)     |       15 | independent     |                   69.918 |                  60.029 |    -14.144 |      16.585 |        0.734 |            0.68  |      0.95  |        3595.08 |       2398.49 |         241.049 |        227.739 |          7.492 |         4.132 |          13 |                     0 |                       0 |                        0.434 |                      0.27  | Indépendant (marginales seules)     |
| conditioned   | Heure+région, sans propagation      |       15 | hour_region     |                   69.918 |                  59.998 |    -14.189 |      16.553 |        0.735 |            0.679 |      0.949 |        3595.08 |       2397.5  |         241.049 |        228.775 |          7.492 |         4.744 |          13 |                     0 |                       0 |                        0.5   |                      0.23  | Heure+région, sans propagation      |
| conditioned   | Proposé sans propagation (ablation) |       15 | proposed_noprop |                   69.918 |                  36.347 |    -48.015 |      34.036 |        0.719 |            0.66  |      0.937 |        3595.08 |       1203.24 |         241.049 |        168.014 |          7.492 |         1.975 |          13 |                     0 |                       0 |                        0.254 |                      0.484 | Proposé sans propagation (ablation) |
| conditioned   | Proposé (complet)                   |       15 | proposed        |                   69.918 |                  59.145 |    -15.408 |      17.298 |        0.701 |            0.638 |      0.938 |        3595.08 |       2598.67 |         241.049 |        214.129 |          7.492 |         2.972 |          13 |                     0 |                       0 |                        0.762 |                      0.057 | Proposé (complet)                   |

## T3b — Avant / après (régime tiré par le générateur)

| Indicateur (b = 5 min, moyenne par jour)    |   Réel (BTS 2024) |   Avant : indépendant |   Avant : heure+région (≈ Dijk et al.) |   Après : proposé sans propagation |   Après : proposé complet |
|:--------------------------------------------|------------------:|----------------------:|-----------------------------------------:|-----------------------------------:|--------------------------:|
| Conflits de stands / jour                   |           143.197 |               134.713 |                                  134.624 |                            107.55  |                   135.526 |
| Écart au réel (%)                           |             0     |                -5.925 |                                   -5.987 |                            -24.893 |                    -5.357 |
| MAE journalière (conflits)                  |             0     |                17.467 |                                   17.537 |                             35.946 |                    17.558 |
| Corrélation jour à jour avec le réel        |             1     |                 0.612 |                                    0.608 |                              0.605 |                     0.595 |
| Spearman jour à jour                        |             1     |                 0.592 |                                    0.586 |                              0.596 |                     0.574 |
| AUC détection des jours de pointe (Q90)     |             1     |                 0.67  |                                    0.673 |                              0.652 |                     0.661 |
| Minutes de chevauchement / jour             |          5446.12  |              4225.89  |                                 4225.24  |                           2467.03  |                  4403.55  |
| Réaffectations / jour                       |           356.885 |               356.509 |                                  356.675 |                            304.88  |                   347.18  |
| Réel dans [Q5, Q95] des scénarios           |             1     |                 0.713 |                                    0.795 |                              0.328 |                     0.705 |
| Jours où le réel dépasse tous les scénarios |             0     |                 0.098 |                                    0.074 |                              0.41  |                     0.09  |

## T3b — Avant / après (régime réel du jour connu)

| Indicateur (b = 5 min, moyenne par jour)    |   Réel (BTS 2024) |   Avant : indépendant |   Avant : heure+région (≈ Dijk et al.) |   Après : proposé sans propagation |   Après : proposé complet |
|:--------------------------------------------|------------------:|----------------------:|-----------------------------------------:|-----------------------------------:|--------------------------:|
| Conflits de stands / jour                   |           143.197 |               134.071 |                                  134.087 |                            107.864 |                   134.773 |
| Écart au réel (%)                           |             0     |                -6.373 |                                   -6.362 |                            -24.674 |                    -5.883 |
| MAE journalière (conflits)                  |             0     |                16.445 |                                   16.355 |                             35.758 |                    16.305 |
| Corrélation jour à jour avec le réel        |             1     |                 0.726 |                                    0.728 |                              0.583 |                     0.701 |
| Spearman jour à jour                        |             1     |                 0.719 |                                    0.719 |                              0.579 |                     0.697 |
| AUC détection des jours de pointe (Q90)     |             1     |                 0.906 |                                    0.912 |                              0.641 |                     0.842 |
| Minutes de chevauchement / jour             |          5446.12  |              4072.01  |                                 4070.82  |                           2401.87  |                  4225.85  |
| Réaffectations / jour                       |           356.885 |               354.62  |                                  355.005 |                            306.129 |                   346.745 |
| Réel dans [Q5, Q95] des scénarios           |             1     |                 0.541 |                                    0.713 |                              0.336 |                     0.689 |
| Jours où le réel dépasse tous les scénarios |             0     |                 0.246 |                                    0.131 |                              0.484 |                     0.115 |

Temps de calcul (validation) : `{"generation_seconds_total": {"independent": 61.88495230674744, "hour_region": 61.11002802848816, "proposed_noprop": 63.73313355445862, "proposed": 64.41843867301941}, "n_days": 366, "n_scenarios": 100, "rotations_per_day_mean": 670.3688524590164}`

Temps de calcul (allocation) : `{"n_days": 122, "buffers": [5.0, 15.0], "n_scenarios": 100, "modes": ["unconditional", "conditioned"], "milp_runtime_mean": 8.907884456095148, "milp_status": {"GREEDY_FALLBACK": 244}, "milp_unassigned_mean": 1.2336065573770492, "stands_mean": 124.72950819672131, "rotations_mean": 670.311475409836}`
