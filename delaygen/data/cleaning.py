"""Filtres d'exclusion des vols BTS avec rapport par motif (cahier des charges §7.2)."""
from __future__ import annotations

import json
import logging

import pandas as pd

log = logging.getLogger(__name__)

KEY_COLS = ["FlightDate", "Reporting_Airline", "Origin", "Dest", "CRSDepTime_min", "CRSArrTime_min"]


def clean_flights(df: pd.DataFrame, max_delay: float = 360, report_path: str | None = None) -> pd.DataFrame:
    report = {"input": int(len(df))}
    n0 = len(df)
    m = df["Cancelled"].fillna(0) == 1
    report["cancelled"] = int(m.sum())
    df = df[~m]
    m = df["Diverted"].fillna(0) == 1
    report["diverted"] = int(m.sum())
    df = df[~m]
    m = df[KEY_COLS].isna().any(axis=1)
    report["missing_key"] = int(m.sum())
    df = df[~m]
    m = df["ArrDelay"].isna() | df["DepDelay"].isna()
    report["missing_delay"] = int(m.sum())
    df = df[~m]
    m = (df["ArrDelay"].abs() > max_delay) | (df["DepDelay"].abs() > max_delay)
    report["extreme_delay"] = int(m.sum())
    df = df[~m]
    report["missing_tail_kept"] = int(df["Tail_Number"].isna().sum())  # conservés mais non appariables
    report["output"] = int(len(df))
    report["excluded_share"] = round(1 - len(df) / n0, 4)
    log.info("Nettoyage : %s", report)
    if report_path:
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    return df.reset_index(drop=True)
