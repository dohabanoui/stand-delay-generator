"""Lecture des sources brutes : BTS (extraits hub), registre FAA, METAR (optionnel)."""
from __future__ import annotations

import logging
import os
import re
import zipfile

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

BTS_COLUMNS = [
    "FlightDate", "Reporting_Airline", "Tail_Number", "Flight_Number_Reporting_Airline",
    "Origin", "OriginState", "Dest", "DestState",
    "CRSDepTime", "DepTime", "DepDelay", "TaxiOut", "WheelsOff", "WheelsOn", "TaxiIn",
    "CRSArrTime", "ArrTime", "ArrDelay", "Cancelled", "Diverted", "Distance",
    "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay",
]


def hhmm_to_minutes(x: pd.Series) -> pd.Series:
    """Convertit une heure locale hhmm (float/str) en minutes depuis minuit ; 2400 -> 1440."""
    v = pd.to_numeric(x, errors="coerce").astype(float)
    h = np.floor(v / 100)
    m = v - 100 * h
    out = h * 60 + m
    return out.where(v != 2400, 1440.0)


def load_bts_hub(hub_dir: str, hub: str, years: list[int]) -> pd.DataFrame:
    """Charge les extraits `bts_<HUB>_<YEAR>.parquet` produits par scripts/extract_hub_bts.py."""
    frames = []
    for y in years:
        p = os.path.join(hub_dir, f"bts_{hub}_{y}.parquet")
        if not os.path.exists(p):
            raise FileNotFoundError(f"Extrait manquant : {p} (lancer scripts/extract_hub_bts.py)")
        frames.append(pd.read_parquet(p))
        log.info("BTS %s %d : %d lignes", hub, y, len(frames[-1]))
    df = pd.concat(frames, ignore_index=True)
    return _typify_bts(df)


def load_bts_zip(paths: list[str], hub: str) -> pd.DataFrame:
    """Lecture directe des zips mensuels TranStats (lent ; préférer les extraits parquet)."""
    frames = []
    for p in paths:
        with zipfile.ZipFile(p) as z:
            name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
            with z.open(name) as fh:
                for chunk in pd.read_csv(fh, usecols=BTS_COLUMNS, low_memory=False, chunksize=200_000):
                    frames.append(chunk[(chunk.Origin == hub) | (chunk.Dest == hub)])
    return _typify_bts(pd.concat(frames, ignore_index=True))


def _typify_bts(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["FlightDate"] = pd.to_datetime(df["FlightDate"])
    for c in ["CRSDepTime", "DepTime", "CRSArrTime", "ArrTime", "WheelsOff", "WheelsOn"]:
        if c in df:
            df[c + "_min"] = hhmm_to_minutes(df[c])
    num = ["DepDelay", "ArrDelay", "TaxiOut", "TaxiIn", "Distance", "Cancelled", "Diverted",
           "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"]
    for c in num:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    tail = df["Tail_Number"].astype("string").str.strip().str.upper()
    tail = tail.mask(tail.isin(["", "UNKNOW", "UNKNOWN", "0", "NKNO"]))
    df["Tail_Number"] = tail
    return df


# ------------------------------------------------------------------ FAA registry
_WB = re.compile(r"(747|767|777|787|A-?3[3458]0|MD-?11|DC-?10|L-?1011)")
_NB = re.compile(r"(737|757|727|717|A-?3(18|19|20|21)|MD-?8\d|MD-?90|DC-?9|BD-500|A220)")
_RJ = re.compile(r"(CRJ|CL-?600|ERJ|EMB-?1[34]5|EMB-?17\d|EMB-?19\d|E-?17\d|E-?19\d|DHC-?8|DASH|ATR|SAAB|CL-?65)")


def category_from_model(mfr: str, model: str, seats: float | None) -> str | None:
    """Catégorie de taille : WB (gros-porteur), NB (moyen-courrier), RJ (régional)."""
    s = f"{mfr} {model}".upper()
    if _WB.search(s):
        return "WB"
    if _RJ.search(s):
        return "RJ"
    if _NB.search(s):
        return "NB"
    if seats is not None and not np.isnan(seats):
        if seats >= 250:
            return "WB"
        if seats >= 100:
            return "NB"
        if seats >= 30:
            return "RJ"
    return None


def load_faa_registry(zip_path: str) -> pd.DataFrame:
    """Jointure MASTER x ACFTREF -> DataFrame[tail, mfr, model, seats, category]."""
    with zipfile.ZipFile(zip_path) as z:
        master = pd.read_csv(z.open("MASTER.txt"), usecols=["N-NUMBER", "MFR MDL CODE"],
                             dtype=str, encoding="utf-8-sig")
        ref = pd.read_csv(z.open("ACFTREF.txt"), usecols=["CODE", "MFR", "MODEL", "NO-SEATS"],
                          dtype=str, encoding="utf-8-sig")
    master.columns = ["nnumber", "code"]
    ref.columns = ["code", "mfr", "model", "seats"]
    for d in (master, ref):
        for c in d.columns:
            d[c] = d[c].str.strip()
    ref["seats"] = pd.to_numeric(ref["seats"], errors="coerce")
    df = master.merge(ref, on="code", how="left")
    df["tail"] = "N" + df["nnumber"]
    df["category"] = [category_from_model(m, mo, s)
                      for m, mo, s in zip(df.mfr.fillna(""), df.model.fillna(""), df.seats)]
    log.info("FAA registry : %d immatriculations, %d avec catégorie", len(df), df.category.notna().sum())
    return df[["tail", "mfr", "model", "seats", "category"]].drop_duplicates("tail")


def load_metar(path: str) -> pd.DataFrame:
    """METAR horaires (export IEM ASOS : station,valid,vsby,skyc*,skyl*,sknt,wxcodes)."""
    df = pd.read_csv(path, na_values=["M"])
    df["valid"] = pd.to_datetime(df["valid"])
    return df
