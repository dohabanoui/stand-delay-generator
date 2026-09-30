# Modèle génératif — rappel et correspondance avec le code

Notation : rotation `i` du jour `d`, arrivée programmée `a_i`, départ programmé `d_i`, catégorie `t_i`,
compagnie `c_i`, région d'origine `r_i`, heure-bloc d'arrivée `h_i`, régime `w_d`.

| Module | Modèle | Code | Estimation (train 2023, CLT) |
|---|---|---|---|
| M1 | Chaîne de Markov des régimes `P(w_{d+1} | w_d)`, lissage +1 | `models/regime.py` | 2 états (`normal`, `degrade`), 76 jours dégradés / 365 |
| M2 | Marginales `F_k^{-1}` par classe `k = (h, w)`, quantiles 0,5 %–99,5 % (199 points), fusion si `n_k < 200` | `models/marginals.py` | 48 classes, 9 fusionnées ; option paramétrique (log-normale retenue par AIC) |
| M3 | `S_i = λ_d Z_d + λ_h Z_h + λ_c Z_c + λ_r Z_r + σ_ε ε_i`, estimation par moments (régression de `S_i S_j` sur les indicatrices) | `models/dependence.py` | `λ_d ≈ 0,11`, `λ_h ≈ 0,16`, `λ_c ≈ 0,14`, `λ_r ≈ 0,19` (voir `results/tables/T_params_dependence`) |
| M4 | `MTT(t) = Q_{0,05}(d_i − a_i | A_i ≥ 30)`, `slack_i = max(0, d_i − a_i − MTT)`, `D_i^{react} = max(0, A_i − slack_i)` | `models/propagation.py` | `MTT = {RJ 44, NB 47, WB 60}` min |
| M5 | Retard sol `G_i = F_{G,(h', w)}^{-1}(Φ(S_i^G))`, `S_i^G = ρ_G · commun + √(1−ρ_G²) η_i`, `ρ_G = 0,3` ; `G_i` peut être négatif (départ anticipé, `allow_early_departure`) | `models/ground.py` | 38 classes, estimé sur `A_i ≤ 0` |
| — | **Composition « max »** : `dep_i = max(arr_i + MTT, d_i + G_i)` soit `D_i = max(A_i − slack_i, G_i)` (défaut, `ground.composition: max`) ; variante additive du cahier des charges `D_i = D_i^{react} + G_i` (`additive`) | `generate.py` | 100 scénarios × 700 rotations : ≈ 0,15 s |

**Pourquoi la composition « max »** : avec la forme additive et une troncature de `G` à 0, la loi de `D` générée
n'avait aucune masse négative alors que 50 % des départs BTS sont anticipés (KS = 0,52 sur `D`), et `E[D | A > 45]`
était surestimée (retard réactionnel et retard sol s'additionnaient). La composition « max » correspond au chemin
critique d'une rotation (l'avion part quand il est prêt **et** que son propre retard sol est résorbé) ; KS sur `D`
≈ 0,05 après changement. La surestimation résiduelle de `E[D | A > 45]` (≈ 85 vs 64 min) traduit l'absence de
modélisation de la compression des rotations par les compagnies (limite à mentionner).

## Générateurs comparés (`baselines.py`)

| Nom | Marginales | Corrélation | Propagation | Rôle |
|---|---|---|---|---|
| `independent` | M2 (A), marginale globale de D par (heure, régime) | aucune | non | « avant » : Monte-Carlo indépendant |
| `hour_region` | idem | `λ_h`, `λ_r` seulement | non | « avant » : inspiré de Dijk et al. (2018) |
| `proposed_noprop` | M2 + M5 | M3 complet | non | ablation |
| `proposed` | M2 + M5 | M3 complet | M4 | générateur proposé |

Tous partagent la même chaîne de régimes (M1), donc les mêmes marginales conditionnelles : les différences
mesurées portent uniquement sur la structure de dépendance et la propagation.

## Validation à trois niveaux

1. **Statistique** (`validation/statistical.py`, T1, F1) : KS, Wasserstein, part > 15 min, Q95/Q99 de `A` et `D`,
   globalement et par régime, sur les 366 jours de 2024.
2. **Structurelle** (`validation/structural.py`, T2, T2b, F3) : corrélation intra-heure / compagnie / région,
   indice de dispersion des comptes horaires de retards, `E[D | A]`, part réactionnelle vs `LateAircraftDelay` BTS.
3. **Opérationnelle** (`validation/operational.py`, `allocation/*`, T3, T3b, F2, F2b, F4) : pour chaque jour test,
   instance synthétique (occupation de pointe 88 %), allocation (b = 5 et 15), rejeu sur horaires réels et sur
   100 scénarios de chaque générateur : conflits, minutes de chevauchement, réaffectations (heuristique gloutonne),
   détection des jours de pointe (Q90 réel), couverture du réel par l'intervalle [Q5, Q95] des scénarios.

## Leviers paramétrables (`generation:` dans `config/default.yaml`, E4 / T4 / F5)

`correlation_scale`, `peak_multiplier`, `weather_shift`, `forced_regime`, `propagation`, `n_scenarios`, `seed`.
