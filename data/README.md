# Données — Générateur de scénarios de retards (DASA'26)

## data/raw/bts — BTS Reporting Carrier On-Time Performance (1987–present)

- Source : Bureau of Transportation Statistics, TranStats, archives pré-zippées
  `https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_<YYYY>_<M>.zip`
- Couverture téléchargée : janvier 2023 → décembre 2024 (24 fichiers mensuels).
  - 2023 = période d'estimation (train), 2024 = période de validation (test) — cahier des charges §3.5.
- Contenu d'une archive : un CSV (~240 Mo, ~540 000 vols domestiques US) + `readme.html` (dictionnaire des colonnes).
- Script : `download_bts.sh [YEAR_START] [YEAR_END] [OUT_DIR]` (reprise automatique, vérification zip).
- Licence : données publiques du DOT américain, citation `bts2025ontime` dans `references.bib`.

Colonnes clés (dictionnaire complet dans `readme.html` de chaque archive) :
`FlightDate, Reporting_Airline, Tail_Number, Flight_Number_Reporting_Airline, Origin, OriginState, Dest, DestState,
CRSDepTime, DepTime, DepDelay, TaxiOut, WheelsOff, WheelsOn, TaxiIn, CRSArrTime, ArrTime, ArrDelay,
Cancelled, Diverted, Distance, CarrierDelay, WeatherDelay, NASDelay, SecurityDelay, LateAircraftDelay`.

## data/processed — extraits par hub

Produits par `extract_hub_bts.py --hub <IATA> --years 2023 2024` :

- `bts_<HUB>_<YEAR>.parquet` : vols avec `Origin == HUB` ou `Dest == HUB`, 36 colonnes utiles (§3.1).
- `bts_<HUB>_extract_report.json` : nombre de lignes lues / retenues par mois.

Ordre de grandeur (janvier 2023) : CLT ≈ 30 000 vols/mois (≈ 490 arrivées/jour, AA + OH ≈ 86 %),
ATL ≈ 53 000 vols/mois (≈ 860 arrivées/jour, DL ≈ 64 %). `Tail_Number` manquant < 0,2 %.

## À télécharger ensuite (hors BTS)

- `data/raw/faa/` : registre FAA `ReleasableAircraft.zip` (tables MASTER, ACFTREF) → type d'avion par immatriculation (§3.3).
- `data/raw/metar/` : METAR horaires de la station du hub (KCLT / KATL), Iowa Environmental Mesonet ASOS archive (§3.4).
