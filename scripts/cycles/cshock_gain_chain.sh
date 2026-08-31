#!/bin/bash
# c-SHOCK LAYOFF_GAIN calibration chain (prereg ops/alive/cycles/cshock.md).
# covid arm x 6 gains x 3 seeds (fit target: WB 2019->2020 +0.999pp),
# null arm flag-on + flag-off x 3 seeds (baseline-invariance gate).
# GFC held-out check runs AFTER the gain is picked, not here.
set -u
cd /opt/earth1
PY=.venv/bin/python
export CSHOCK_GAIN_OUT=/opt/earth1-data/cshock_gain
export EARTH1_HARDSHIP_MODE=gradient
LOG=$CSHOCK_GAIN_OUT/chain.log
mkdir -p "$CSHOCK_GAIN_OUT"
echo "GAIN CHAIN START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"

for SEED in 401 402 403; do
  for GAIN in 0.002 0.005 0.01 0.02 0.05 0.10; do
    EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=$GAIN \
      $PY scripts/cycles/cshock_gain_sweep.py $SEED covid >> "$LOG" 2>&1 &
  done
  EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.05 \
    $PY scripts/cycles/cshock_gain_sweep.py $SEED null >> "$LOG" 2>&1 &
  EARTH1_DISTRESS_LAYOFFS=off \
    $PY scripts/cycles/cshock_gain_sweep.py $SEED null >> "$LOG" 2>&1 &
done
wait
echo "GAIN CHAIN COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
