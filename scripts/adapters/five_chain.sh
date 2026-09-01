#!/bin/bash
set -u
cd /opt/earth1
PY=.venv/bin/python
export FIVE_OUT=/opt/earth1-data/five
export EARTH1_HARDSHIP_MODE=gradient EARTH1_INCOME_CALIBRATION=v1 \
  EARTH1_SUBSTRATE_FLAG=c2plus_v1 EARTH1_C2PLUS_TABLES=c2plus_tables_v2.json \
  EARTH1_MORTALITY_MODE=gompertz EARTH1_GM_OTHER_SHARE=0.21407724082954704 \
  EARTH1_WANT_MODE=rr EARTH1_WANT_RR=4.933765606879083 \
  EARTH1_WEATHER_SCALE=0.020333010074315046 \
  EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.0028
LOG=$FIVE_OUT/chain.log
mkdir -p "$FIVE_OUT"
echo "FIVE START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"
$PY scripts/adapters/five_scenarios.py warm >> "$LOG" 2>&1 || { echo ABORT-warm >> "$LOG"; exit 2; }
for i in $(seq 0 39); do
  $PY scripts/adapters/five_scenarios.py worker $i 40 >> "$LOG" 2>&1 &
done
wait
$PY scripts/adapters/five_scenarios.py assemble >> "$LOG" 2>&1
echo "FIVE COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
