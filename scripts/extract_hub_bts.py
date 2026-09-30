"""
extract_hub_bts.py — Extraction des vols d'un hub depuis les archives BTS mensuelles.

Lit les zips "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_YYYY_M.zip"
(data/raw/bts), ne garde que les colonnes utiles au projet (cahier des charges §3.1)
et les vols avec Origin == HUB ou Dest == HUB, puis ecrit :
  data/processed/bts_<HUB>_<YEAR>.parquet   (un fichier par annee)
  data/processed/bts_<HUB>_extract_report.json

Usage : python extract_hub_bts.py --hub CLT --years 2023 2024
"""
import argparse, glob, json, os, re, sys, zipfile, time
import pandas as pd

COLUMNS = [
    "Year", "Month", "DayofMonth", "DayOfWeek", "FlightDate",
    "Reporting_Airline", "Tail_Number", "Flight_Number_Reporting_Airline",
    "Origin", "OriginState", "Dest", "DestState",
    "CRSDepTime", "DepTime", "DepDelay", "DepDelayMinutes",
    "TaxiOut", "WheelsOff", "WheelsOn", "TaxiIn",
    "CRSArrTime", "ArrTime", "ArrDelay", "ArrDelayMinutes",
    "Cancelled", "CancellationCode", "Diverted",
    "CRSElapsedTime", "ActualElapsedTime", "AirTime", "Distance",
    "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay",
]
DTYPES = {c: "string" for c in ["FlightDate", "Reporting_Airline", "Tail_Number", "Origin",
                                "OriginState", "Dest", "DestState", "CancellationCode"]}

def month_key(path):
    m = re.search(r"_(\d{4})_(\d{1,2})\.zip$", path)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

def read_zip(path, hub):
    with zipfile.ZipFile(path) as z:
        csv_name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(csv_name) as fh:
            header = pd.read_csv(fh, nrows=0).columns.tolist()
        usecols = [c for c in COLUMNS if c in header]
        missing = [c for c in COLUMNS if c not in header]
        parts, n_total = [], 0
        with z.open(csv_name) as fh:
            for chunk in pd.read_csv(fh, usecols=usecols, dtype=DTYPES, low_memory=False, chunksize=200_000):
                n_total += len(chunk)
                parts.append(chunk[(chunk["Origin"] == hub) | (chunk["Dest"] == hub)])
    df = pd.concat(parts, ignore_index=True)
    return df, n_total, missing

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default="CLT")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--raw", default="data/raw/bts")
    ap.add_argument("--out", default="data/processed")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report = {"hub": a.hub, "months": []}
    for year in a.years:
        files = sorted(glob.glob(os.path.join(a.raw, f"*_{year}_*.zip")), key=month_key)
        frames = []
        for f in files:
            t0 = time.time()
            df, n_total, missing = read_zip(f, a.hub)
            frames.append(df)
            info = {"file": os.path.basename(f), "rows_total": n_total, "rows_hub": len(df),
                    "missing_cols": missing, "seconds": round(time.time() - t0, 1)}
            report["months"].append(info)
            print(f"{info['file']}: {n_total:,} vols, {len(df):,} au hub {a.hub} ({info['seconds']} s)", flush=True)
        if frames:
            out = pd.concat(frames, ignore_index=True)
            dst = os.path.join(a.out, f"bts_{a.hub}_{year}.parquet")
            out.to_parquet(dst, index=False)
            print(f"-> {dst}: {len(out):,} lignes, {len(files)} mois", flush=True)
    with open(os.path.join(a.out, f"bts_{a.hub}_extract_report.json"), "w") as fh:
        json.dump(report, fh, indent=2)

if __name__ == "__main__":
    main()
