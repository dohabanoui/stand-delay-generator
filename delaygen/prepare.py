"""Orchestration données : BTS hub -> nettoyage -> catégorie avion -> rotations -> régime.

Sorties (dans paths.processed) :
  rotations_<HUB>.parquet, regime_<HUB>.parquet, cleaning_report_<HUB>.json, prepare_report_<HUB>.json
"""
from __future__ import annotations

import json
import logging
import os

import pandas as pd

from delaygen.config import load_config, load_regions
from delaygen.data.aircraft import attach_category
from delaygen.data.cleaning import clean_flights
from delaygen.data.loaders import load_bts_hub, load_faa_registry, load_metar
from delaygen.data.rotations import build_rotations
from delaygen.data.weather import regime_fallback_bts, regime_from_metar

log = logging.getLogger(__name__)


def _years(cfg: dict) -> list[int]:
    y0 = int(str(cfg["train_period"]["start"])[:4])
    y1 = int(str(cfg["test_period"]["end"])[:4])
    return list(range(y0, y1 + 1))


def run(cfg: dict | None = None, hub: str | None = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    hub = hub or cfg["hub"]
    out_dir = cfg["paths"]["processed"]
    os.makedirs(out_dir, exist_ok=True)
    report = {"hub": hub}

    flights = load_bts_hub(cfg["paths"]["bts_hub"], hub, _years(cfg))
    report["raw_rows"] = int(len(flights))
    flights = clean_flights(flights, cfg["cleaning"]["max_delay"],
                            os.path.join(out_dir, f"cleaning_report_{hub}.json"))

    registry = None
    faa = cfg["paths"].get("faa_registry")
    if faa and os.path.exists(faa):
        registry = load_faa_registry(faa)
    else:
        log.warning("Registre FAA absent : catégorie imputée par compagnie")
    flights, report["aircraft_category"] = attach_category(flights, registry)

    # régime météo
    tr = cfg["train_period"]
    is_train = (flights.FlightDate >= pd.Timestamp(tr["start"])) & (flights.FlightDate <= pd.Timestamp(tr["end"]))
    metar_path = cfg["paths"].get("metar")
    if metar_path and os.path.exists(metar_path):
        regime = regime_from_metar(load_metar(metar_path), cfg["regime"]["ifr_hours_threshold"],
                                   cfg["regime"]["wind_kt_threshold"])
        report["regime_source"] = "metar"
    else:
        reg_tr, thr = regime_fallback_bts(flights[is_train], hub, cfg["regime"]["fallback_weather_share"],
                                          cfg["regime"]["fallback_mean_delay_quantile"])
        reg_te, _ = regime_fallback_bts(flights[~is_train], hub, thresholds=thr)
        regime = pd.concat([reg_tr, reg_te], ignore_index=True)
        report["regime_source"] = "bts_fallback"
        report["regime_thresholds"] = thr
    report["regime_counts"] = {k: int(v) for k, v in regime.regime.value_counts().items()}

    rotations, rot_report = build_rotations(
        flights, hub, load_regions(), cfg["cleaning"]["max_turnaround"], cfg["cleaning"]["overnight_stay"],
        cfg["propagation"]["mtt_default"], cfg["marginals"]["hour_block_size"])
    report["rotations"] = rot_report
    rotations = rotations.merge(regime[["date", "regime"]], on="date", how="left")
    rotations["regime"] = rotations["regime"].fillna("normal").astype("string")
    rotations["split"] = "train"
    rotations.loc[(rotations.date > pd.Timestamp(tr["end"])), "split"] = "test"
    rotations["pax"] = rotations["category"].map(cfg.get("pax_by_category", {})).fillna(140).astype(float)

    rotations.to_parquet(os.path.join(out_dir, f"rotations_{hub}.parquet"), index=False)
    regime.to_parquet(os.path.join(out_dir, f"regime_{hub}.parquet"), index=False)
    flights.to_parquet(os.path.join(out_dir, f"flights_clean_{hub}.parquet"), index=False)
    with open(os.path.join(out_dir, f"prepare_report_{hub}.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    log.info("prepare terminé : %d rotations", len(rotations))
    return rotations


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--hub", default=None)
    a = ap.parse_args()
    run(load_config(a.config), a.hub)
