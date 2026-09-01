#!/bin/bash
# Full per-event pipeline: warm -> 16 workers -> assemble (freeze).
set -u
EV=$1
cd /opt/earth1
PY=.venv/bin/python
export EARTH1_HARDSHIP_MODE=gradient EARTH1_INCOME_CALIBRATION=v1 \
  EARTH1_SUBSTRATE_FLAG=c2plus_v1 EARTH1_C2PLUS_TABLES=c2plus_tables_v2.json \
  EARTH1_MORTALITY_MODE=gompertz EARTH1_GM_OTHER_SHARE=0.21407724082954704 \
  EARTH1_WANT_MODE=rr EARTH1_WANT_RR=4.933765606879083 \
  EARTH1_WEATHER_SCALE=0.020333010074315046 \
  EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.0028
LOG=/opt/earth1-data/historical/${EV}_pipeline.log
mkdir -p /opt/earth1-data/historical/$EV
echo "PIPELINE $EV START $(date -u +%FT%TZ)" >> "$LOG"
$PY scripts/historical/run_event.py $EV warm >> "$LOG" 2>&1 || { echo "ABORT-warm $EV" >> "$LOG"; exit 2; }
for i in $(seq 0 15); do
  $PY scripts/historical/run_event.py $EV worker $i 16 >> "$LOG" 2>&1 &
done
wait
$PY scripts/historical/run_event.py $EV assemble >> "$LOG" 2>&1
echo "PIPELINE $EV COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
