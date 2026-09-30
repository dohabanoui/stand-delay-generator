"""Reconstruction des rotations (arrivée -> départ du même avion) au hub. Cahier des charges §7.3."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def _fix_after_midnight(real: pd.Series, sched: pd.Series) -> pd.Series:
    """Horaire réel après minuit d'un vol programmé la veille : +1440 si real < sched - 720."""
    return real.where(~(real < sched - 720), real + 1440)


def _match_pairs(arr_t: pd.DataFrame, dep_t: pd.DataFrame, max_turnaround: int) -> pd.DataFrame:
    """Pour chaque (tail, date) : chaque arrivée est appariée au premier départ programmé
    postérieur non encore utilisé, avec 0 < d - a <= max_turnaround."""
    pairs = []
    dep_groups = {k: g for k, g in dep_t.groupby("key", sort=False)}
    for k, ga in arr_t.groupby("key", sort=False):
        gd = dep_groups.get(k)
        if gd is None:
            continue
        d_sched = gd["d_sched"].to_numpy()
        d_idx = gd.index.to_numpy()
        taken = np.zeros(len(gd), dtype=bool)
        for ai, a in zip(ga.index, ga["a_sched"].to_numpy()):
            cand = np.where((d_sched > a) & (d_sched - a <= max_turnaround) & ~taken)[0]
            if len(cand):
                j = cand[0]
                taken[j] = True
                pairs.append((ai, d_idx[j]))
    return pd.DataFrame(pairs, columns=["arr_idx", "dep_idx"])


def build_rotations(flights: pd.DataFrame, hub: str, regions: dict, max_turnaround: int = 720,
                    overnight_stay: int = 480, mtt_default: dict | None = None,
                    hour_block_size: int = 1) -> tuple[pd.DataFrame, dict]:
    mtt_default = mtt_default or {"RJ": 25, "NB": 35, "WB": 60}
    arr = flights[flights.Dest == hub].copy()
    dep = flights[flights.Origin == hub].copy()

    arr["a_sched"] = arr["CRSArrTime_min"]
    arr["a_real"] = _fix_after_midnight(arr["ArrTime_min"], arr["a_sched"])
    dep["d_sched"] = dep["CRSDepTime_min"]
    dep["d_real"] = _fix_after_midnight(dep["DepTime_min"], dep["d_sched"])

    arr_t = arr[arr.Tail_Number.notna()].sort_values(["Tail_Number", "FlightDate", "a_sched"]).copy()
    dep_t = dep[dep.Tail_Number.notna()].sort_values(["Tail_Number", "FlightDate", "d_sched"]).copy()
    arr_t["key"] = arr_t.Tail_Number.astype(str) + "_" + arr_t.FlightDate.dt.strftime("%Y%m%d")
    dep_t["key"] = dep_t.Tail_Number.astype(str) + "_" + dep_t.FlightDate.dt.strftime("%Y%m%d")
    pairs = _match_pairs(arr_t, dep_t, max_turnaround)

    a = arr.loc[pairs.arr_idx].reset_index(drop=True)
    d = dep.loc[pairs.dep_idx].reset_index(drop=True)
    rot = pd.DataFrame({
        "date": a.FlightDate, "tail": a.Tail_Number, "category": a.category,
        "carrier": a.Reporting_Airline, "origin": a.Origin, "origin_state": a.OriginState,
        "dest": d.Dest, "dest_carrier": d.Reporting_Airline,
        "a_sched": a.a_sched, "d_sched": d.d_sched, "a_real": a.a_real, "d_real": d.d_real,
        "A": a.ArrDelay, "D": d.DepDelay,
        "late_aircraft_delay": d.LateAircraftDelay, "carrier_delay_dep": d.CarrierDelay,
        "weather_delay_arr": a.WeatherDelay, "nas_delay_arr": a.NASDelay,
        "taxi_in": a.TaxiIn, "taxi_out": d.TaxiOut, "distance_in": a.Distance,
        "open_rotation": False, "first_departure": False,
    })

    # arrivées non appariées : départ fictif (nuitée / tail manquant)
    ua = arr.drop(index=pairs.arr_idx)
    ro = pd.DataFrame({
        "date": ua.FlightDate, "tail": ua.Tail_Number, "category": ua.category,
        "carrier": ua.Reporting_Airline, "origin": ua.Origin, "origin_state": ua.OriginState,
        "dest": pd.NA, "dest_carrier": pd.NA,
        "a_sched": ua.a_sched, "d_sched": ua.a_sched + overnight_stay, "a_real": ua.a_real, "d_real": np.nan,
        "A": ua.ArrDelay, "D": np.nan,
        "late_aircraft_delay": np.nan, "carrier_delay_dep": np.nan,
        "weather_delay_arr": ua.WeatherDelay, "nas_delay_arr": ua.NASDelay,
        "taxi_in": ua.TaxiIn, "taxi_out": np.nan, "distance_in": ua.Distance,
        "open_rotation": True, "first_departure": False,
    })
    # départs non appariés : arrivée fictive (premier vol du jour)
    ud = dep.drop(index=pairs.dep_idx)
    mtt = ud.category.map(mtt_default).fillna(35).astype(float)
    rf = pd.DataFrame({
        "date": ud.FlightDate, "tail": ud.Tail_Number, "category": ud.category,
        "carrier": ud.Reporting_Airline, "origin": pd.NA, "origin_state": pd.NA,
        "dest": ud.Dest, "dest_carrier": ud.Reporting_Airline,
        "a_sched": ud.d_sched - mtt, "d_sched": ud.d_sched, "a_real": np.nan, "d_real": ud.d_real,
        "A": np.nan, "D": ud.DepDelay,
        "late_aircraft_delay": ud.LateAircraftDelay, "carrier_delay_dep": ud.CarrierDelay,
        "weather_delay_arr": np.nan, "nas_delay_arr": np.nan,
        "taxi_in": np.nan, "taxi_out": ud.TaxiOut, "distance_in": np.nan,
        "open_rotation": False, "first_departure": True,
    })
    out = pd.concat([rot, ro, rf], ignore_index=True)
    out["origin_region"] = out["origin_state"].map(regions).fillna("Unknown")
    out["hour_block_arr"] = (np.clip(out["a_sched"], 0, 1439) // (60 * hour_block_size)).astype(int)
    out["hour_block_dep"] = (np.clip(out["d_sched"], 0, 1439) // (60 * hour_block_size)).astype(int)
    out["ground_sched"] = out["d_sched"] - out["a_sched"]
    out["ground_real"] = out["d_real"] - out["a_real"]
    out = out.sort_values(["date", "a_sched"]).reset_index(drop=True)
    out["rot_id"] = np.arange(len(out))
    for c in ["tail", "carrier", "origin", "origin_state", "dest", "dest_carrier", "category", "origin_region"]:
        out[c] = out[c].astype("string")

    report = {
        "arrivals": int(len(arr)), "departures": int(len(dep)), "matched_pairs": int(len(pairs)),
        "match_rate_arrivals": round(len(pairs) / max(len(arr), 1), 4),
        "match_rate_departures": round(len(pairs) / max(len(dep), 1), 4),
        "open_rotations": int(len(ro)), "first_departures": int(len(rf)),
        "arrivals_without_tail": int(arr.Tail_Number.isna().sum()),
        "rotations_total": int(len(out)),
    }
    log.info("Rotations : %s", report)
    return out, report
