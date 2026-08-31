#!/bin/bash
# c-SHOCK 200k confirmation at frozen GAIN*=0.00633 (prereg cshock.md):
# covid must hold +0.999pp; gfc held-out read at decision precision.
set -u
cd /opt/earth1
PY=.venv/bin/python
export CSHOCK_GAIN_OUT=/opt/earth1-data/cshock_gain_200k
export EARTH1_HARDSHIP_MODE=gradient
LOG=$CSHOCK_GAIN_OUT/chain.log
mkdir -p "$CSHOCK_GAIN_OUT"
echo "200K CONFIRM START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"
for S in 501 502 503 504 505 506; do
  for ARM in covid gfc; do
    EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.00633 \
      $PY scripts/cycles/cshock_gain_sweep.py $S $ARM 200000 >> "$LOG" 2>&1 &
  done
  EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.00633 \
    $PY scripts/cycles/cshock_gain_sweep.py $S null 200000 >> "$LOG" 2>&1 &
done
wait
echo "200K CONFIRM COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
