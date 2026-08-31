#!/bin/bash
# c-SHOCK DIAGNOSE chain (prereg ops/alive/cycles/cshock.md).
# Stage 1: 20k chain-stage probes, sequential (2 modes x 2 arms x 3 seeds).
# Stage 2: 200k onset confirmation, 4 in parallel (2 modes x 2 arms x 1 seed).
# Stage 3: summarize.
set -u
cd /opt/earth1
PY=.venv/bin/python
export CSHOCK_OUT=/opt/earth1-data/cshock
LOG=/opt/earth1-data/cshock/chain.log
mkdir -p "$CSHOCK_OUT"
echo "CHAIN START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"

for MODE in gradient cliff; do
  for ARM in dose null; do
    for SEED in 201 202 203; do
      EARTH1_HARDSHIP_MODE=$MODE $PY scripts/cycles/cshock_probe.py $SEED $ARM 20000 >> "$LOG" 2>&1
    done
  done
done
echo "STAGE1 20k DONE $(date -u +%FT%TZ)" >> "$LOG"

for MODE in gradient cliff; do
  for ARM in dose null; do
    EARTH1_HARDSHIP_MODE=$MODE $PY scripts/cycles/cshock_probe.py 301 $ARM 200000 >> "$LOG" 2>&1 &
  done
done
wait
echo "STAGE2 200k DONE $(date -u +%FT%TZ)" >> "$LOG"

$PY scripts/cycles/cshock_summarize.py >> "$LOG" 2>&1
echo "CHAIN COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
