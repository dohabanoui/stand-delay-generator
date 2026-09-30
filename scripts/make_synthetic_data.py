"""Fabrique un extrait BTS-like synthétique (parquet) pour exécuter le pipeline sans télécharger TranStats.

Usage : python scripts/make_synthetic_data.py --hub SYN --months 3 --rotations-per-day 300 --out data/processed
Produit data/processed/bts_SYN_2023.parquet (train) et bts_SYN_2024.parquet (test, 1 mois) avec les colonnes
utilisées par delaygen.data.loaders.load_bts_hub.
"""
import argparse
import os

import numpy as np
import pandas as pd

CARRIERS = {"AA": .55, "OH": .25, "PT": .10, "DL": .05, "UA": .05}
ORIGINS = {"JFK": "NY", "BOS": "MA", "ORD": "IL", "DFW": "TX", "MIA": "FL", "DEN": "CO", "LAX": "CA", "ATL": "GA", "PHL": "PA", "IAH": "TX"}
PEAKS = [(8 * 60, 40), (11 * 60, 35), (14 * 60, 35), (17 * 60, 40), (20 * 60, 35)]


def _hhmm(m):
    m = np.mod(m, 1440)
    return (m // 60) * 100 + m % 60


def make(hub, start, n_days, per_day, rng):
    rows = []
    tails = [f"N{100 + i}SY" for i in range(int(per_day * 0.6))]
    for day in range(n_days):
        date = pd.Timestamp(start) + pd.Timedelta(days=day)
        degraded = rng.random() < 0.2
        Z_d = rng.standard_normal()
        used = 0
        for pk, sd in PEAKS:
            n = per_day // len(PEAKS)
            Z_h = rng.standard_normal()
            for _ in range(n):
                tail = tails[used % len(tails)]; used += 1
                carrier = rng.choice(list(CARRIERS), p=list(CARRIERS.values()))
                origin = rng.choice(list(ORIGINS))
                a_sched = int(np.clip(rng.normal(pk, sd), 300, 1380))
                ground = int(rng.choice([45, 55, 70, 90, 120, 180]))
                d_sched = a_sched + ground
                S = 0.35 * Z_d + 0.3 * Z_h + np.sqrt(1 - .35 ** 2 - .3 ** 2) * rng.standard_normal()
                A = float(np.round(np.exp(2.9 + (0.6 if degraded else 0) + 0.9 * S) - 22))
                slack = max(0, ground - 45)
                D = float(max(0, A - slack) + max(0, rng.exponential(8) - 4))
                late_ac = max(0, A - slack) if D >= 15 else 0
                rows.append(dict(FlightDate=date, Reporting_Airline=carrier, Tail_Number=tail, Flight_Number_Reporting_Airline=1000 + used,
                                 Origin=origin, OriginState=ORIGINS[origin], Dest=hub, DestState="ZZ",
                                 CRSDepTime=_hhmm(a_sched - 120), DepTime=_hhmm(a_sched - 120 + A), DepDelay=A, TaxiOut=15, WheelsOff=0, WheelsOn=0, TaxiIn=8,
                                 CRSArrTime=_hhmm(a_sched), ArrTime=_hhmm(a_sched + A), ArrDelay=A, Cancelled=0, Diverted=0, Distance=600,
                                 CarrierDelay=0, WeatherDelay=(A if degraded and A >= 15 else 0), NASDelay=0, SecurityDelay=0, LateAircraftDelay=0))
                rows.append(dict(FlightDate=date, Reporting_Airline=carrier, Tail_Number=tail, Flight_Number_Reporting_Airline=2000 + used,
                                 Origin=hub, OriginState="ZZ", Dest=origin, DestState=ORIGINS[origin],
                                 CRSDepTime=_hhmm(d_sched), DepTime=_hhmm(d_sched + D), DepDelay=D, TaxiOut=15, WheelsOff=0, WheelsOn=0, TaxiIn=8,
                                 CRSArrTime=_hhmm(d_sched + 120), ArrTime=_hhmm(d_sched + 120 + D), ArrDelay=D, Cancelled=0, Diverted=0, Distance=600,
                                 CarrierDelay=0, WeatherDelay=0, NASDelay=0, SecurityDelay=0, LateAircraftDelay=late_ac))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default="SYN")
    ap.add_argument("--months", type=int, default=3)
    ap.add_argument("--rotations-per-day", type=int, default=300)
    ap.add_argument("--out", default="data/processed")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)
    make(a.hub, "2023-01-01", 30 * a.months, a.rotations_per_day, rng).to_parquet(os.path.join(a.out, f"bts_{a.hub}_2023.parquet"), index=False)
    make(a.hub, "2024-01-01", 30, a.rotations_per_day, rng).to_parquet(os.path.join(a.out, f"bts_{a.hub}_2024.parquet"), index=False)
    print(f"-> {a.out}/bts_{a.hub}_2023.parquet, bts_{a.hub}_2024.parquet (catégorie imputée par compagnie : lancer prepare avec --hub {a.hub})")


if __name__ == "__main__":
    main()
