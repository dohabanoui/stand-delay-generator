"""Rattachement immatriculation -> catégorie d'avion (FAA, puis imputation)."""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)

# Repli par compagnie (BTS Reporting_Airline) : compagnies régionales -> RJ, mainline -> NB
REGIONAL_CARRIERS = {"OH", "MQ", "9E", "OO", "YX", "PT", "YV", "EV", "ZW", "QX", "G7", "C5", "CP", "AX", "KS"}


def attach_category(flights: pd.DataFrame, registry: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    df = flights.copy()
    df["category"] = pd.Series(pd.NA, index=df.index, dtype="object")
    df["category_source"] = "default"
    if registry is not None:
        reg = registry.dropna(subset=["category"]).set_index("tail")["category"]
        cat = df["Tail_Number"].astype(object).map(reg)
        m = cat.notna()
        df.loc[m, "category"] = cat[m]
        df.loc[m, "category_source"] = "faa"
    # imputation 1 : (compagnie, numéro de vol) le plus fréquent
    known = df[df.category.notna()]
    if len(known):
        mode = (known.groupby(["Reporting_Airline", "Flight_Number_Reporting_Airline"])["category"]
                .agg(lambda s: s.value_counts().index[0]))
        idx = pd.MultiIndex.from_frame(df[["Reporting_Airline", "Flight_Number_Reporting_Airline"]])
        imp = pd.Series(mode.reindex(idx).to_numpy(), index=df.index)
        m = df.category.isna() & imp.notna()
        df.loc[m, "category"] = imp[m]
        df.loc[m, "category_source"] = "carrier_flight"
    # imputation 2 : compagnie régionale -> RJ, sinon NB
    m = df.category.isna() & df.Reporting_Airline.isin(REGIONAL_CARRIERS)
    df.loc[m, "category"] = "RJ"
    df.loc[m, "category_source"] = "carrier_default"
    m = df.category.isna()
    df.loc[m, "category"] = "NB"
    df["category"] = df["category"].astype(str)
    report = {k: int(v) for k, v in df.category_source.value_counts().items()}
    report["category_counts"] = {k: int(v) for k, v in df.category.value_counts().items()}
    log.info("Catégorie avion : %s", report)
    return df, report
