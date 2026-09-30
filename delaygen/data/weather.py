"""Régime météo journalier : METAR si disponible, sinon repli BTS (cahier des charges §3.4)."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def regime_from_metar(metar: pd.DataFrame, ifr_hours_threshold: int = 3, wind_kt_threshold: float = 25,
                      day_start: int = 6, day_end: int = 23) -> pd.DataFrame:
    """Régime par jour à partir d'observations METAR horaires (export IEM ASOS)."""
    m = metar.copy()
    m["date"] = m["valid"].dt.normalize()
    m["hour"] = m["valid"].dt.hour
    m = m[(m.hour >= day_start) & (m.hour <= day_end)]
    vis = pd.to_numeric(m.get("vsby"), errors="coerce")
    ceil = pd.Series(np.nan, index=m.index)
    for c, l in [("skyc1", "skyl1"), ("skyc2", "skyl2"), ("skyc3", "skyl3"), ("skyc4", "skyl4")]:
        if c in m and l in m:
            brk = m[c].isin(["BKN", "OVC", "VV"])
            ceil = ceil.where(~(brk & ceil.isna()), pd.to_numeric(m[l], errors="coerce"))
    m["ifr"] = (vis < 3) | (ceil < 1000)
    m["ts"] = m["wxcodes"].fillna("").str.contains("TS") if "wxcodes" in m else False
    m["wind"] = pd.to_numeric(m.get("sknt"), errors="coerce")
    hourly = m.groupby(["date", "hour"]).agg(ifr=("ifr", "any"), ts=("ts", "any"), wind=("wind", "max")).reset_index()
    g = hourly.groupby("date").agg(n_ifr_hours=("ifr", "sum"), thunderstorm=("ts", "any"), max_wind=("wind", "max"))
    g["regime"] = np.where((g.n_ifr_hours >= ifr_hours_threshold) | g.thunderstorm | (g.max_wind > wind_kt_threshold),
                           "degrade", "normal")
    g["regime_source"] = "metar"
    return g.reset_index()


def daily_delay_summary(flights: pd.DataFrame, hub: str) -> pd.DataFrame:
    arr = flights[flights.Dest == hub]
    g = arr.groupby("FlightDate").agg(
        mean_arr_delay=("ArrDelay", "mean"),
        share_gt15=("ArrDelay", lambda s: float((s > 15).mean())),
        weather=("WeatherDelay", "sum"), nas=("NASDelay", "sum"),
        carrier=("CarrierDelay", "sum"), late=("LateAircraftDelay", "sum"), sec=("SecurityDelay", "sum"),
        n_flights=("ArrDelay", "size"))
    tot = g[["weather", "nas", "carrier", "late", "sec"]].sum(axis=1).replace(0, np.nan)
    g["weather_nas_share"] = ((g.weather + g.nas) / tot).fillna(0)
    return g.reset_index().rename(columns={"FlightDate": "date"})


def regime_fallback_bts(flights: pd.DataFrame, hub: str, weather_share_threshold: float = 0.35,
                        mean_delay_quantile: float = 0.80,
                        thresholds: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Repli sans METAR : jour `degrade` si (part WeatherDelay+NASDelay > seuil ET retard moyen > médiane)
    OU retard moyen d'arrivée du jour > quantile `mean_delay_quantile`. Les seuils sont calculés sur les
    données fournies, ou repris de `thresholds` (estimés sur la période train) pour la période test."""
    g = daily_delay_summary(flights, hub)
    if thresholds is None:
        thresholds = {"mean_delay_q": float(g["mean_arr_delay"].quantile(mean_delay_quantile)),
                      "mean_delay_median": float(g["mean_arr_delay"].median()),
                      "weather_share_threshold": weather_share_threshold}
    cond_w = (g.weather_nas_share > thresholds["weather_share_threshold"]) & (g.mean_arr_delay > thresholds["mean_delay_median"])
    cond_q = g.mean_arr_delay > thresholds["mean_delay_q"]
    g["regime"] = np.where(cond_w | cond_q, "degrade", "normal")
    g["regime_source"] = "bts_fallback"
    log.info("Régime (repli BTS) : %s", g.regime.value_counts().to_dict())
    return g, thresholds
