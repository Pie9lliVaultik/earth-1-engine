#!/bin/bash
# c-SHOCK v2 chain: EVENT-TIME onset counting (VERIFY-2, cshock.md).
# Same design as v1, separate OUT so v1 artifacts stay intact.
set -u
cd /opt/earth1
PY=.venv/bin/python
export CSHOCK_OUT=/opt/earth1-data/cshock_v2
LOG=/opt/earth1-data/cshock_v2/chain.log
mkdir -p "$CSHOCK_OUT"
echo "CHAIN-V2 START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"

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
echo "CHAIN-V2 COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
