#!/usr/bin/env bash
# ------------------------------------------------------------------
# download_bts.sh — Téléchargement des fichiers mensuels BTS
# "Reporting Carrier On-Time Performance (1987-present)"
# Source : https://transtats.bts.gov/PREZIP/
# Usage  : bash download_bts.sh [YEAR_START] [YEAR_END] [OUT_DIR]
#          bash download_bts.sh 2023 2024 data/raw/bts
# Chaque archive (~27 Mo zip, ~250 Mo CSV) contient un mois de vols
# domestiques US (~500 000 - 650 000 lignes).
# ------------------------------------------------------------------
set -u
Y0="${1:-2023}"
Y1="${2:-2024}"
OUT="${3:-data/raw/bts}"
BASE="https://transtats.bts.gov/PREZIP"
mkdir -p "$OUT"

for y in $(seq "$Y0" "$Y1"); do
  for m in $(seq 1 12); do
    f="On_Time_Reporting_Carrier_On_Time_Performance_1987_present_${y}_${m}.zip"
    dst="$OUT/$f"
    if [ -s "$dst" ] && unzip -tq "$dst" >/dev/null 2>&1; then
      echo "[skip] $f (déjà présent et valide)"
      continue
    fi
    echo "[get ] $f"
    for attempt in 1 2 3; do
      curl -fsSL --retry 3 --retry-delay 5 --max-time 900 -o "$dst.part" "$BASE/$f" \
        && mv -f "$dst.part" "$dst" && break
      echo "       tentative $attempt échouée, nouvel essai..."
      sleep 10
    done
    if [ ! -s "$dst" ]; then echo "[FAIL] $f"; fi
  done
done

echo "--- Résumé ---"
ls -l "$OUT"/*.zip 2>/dev/null | awk '{s+=$5; n++} END {printf "%d fichiers, %.1f Mo\n", n, s/1048576}'
