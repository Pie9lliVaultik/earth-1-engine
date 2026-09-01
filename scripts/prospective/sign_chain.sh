#!/bin/bash
# Multiverse re-signing chain: warm -> floors -> 24-shard sign -> (assemble runs locally after sync)
set -u
cd /opt/earth1
PY=.venv/bin/python
export SIGN_OUT=/opt/earth1-data/sign_b
export EARTH1_HARDSHIP_MODE=gradient EARTH1_INCOME_CALIBRATION=v1 \
  EARTH1_SUBSTRATE_FLAG=c2plus_v1 EARTH1_C2PLUS_TABLES=c2plus_tables_v2.json \
  EARTH1_MORTALITY_MODE=gompertz EARTH1_GM_OTHER_SHARE=0.21407724082954704 \
  EARTH1_WANT_MODE=rr EARTH1_WANT_RR=4.933765606879083 \
  EARTH1_WEATHER_SCALE=0.020333010074315046 \
  EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.0028
LOG=$SIGN_OUT/chain.log
mkdir -p "$SIGN_OUT"
echo "SIGN CHAIN START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"
$PY scripts/prospective/sign_register.py warm >> "$LOG" 2>&1 || { echo ABORT-warm >> "$LOG"; exit 2; }
$PY scripts/prospective/sign_register.py floors >> "$LOG" 2>&1 || { echo ABORT-floors >> "$LOG"; exit 3; }
for i in $(seq 0 23); do
  $PY scripts/prospective/sign_register.py sign $i 24 >> "$LOG" 2>&1 &
done
wait
echo "SIGN CHAIN COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
