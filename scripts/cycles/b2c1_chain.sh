#!/bin/bash
# B2-c1d chain (prereg: founder order 2026-09-01 item 1; cycle doc
# ops/alive/cycles/b2c1.md). Stages: bitwise-assert -> gate-on-prime ->
# 3x 200k feature worlds flag-ON -> rescore all three estates.
set -u
cd /opt/earth1
PY=.venv/bin/python
LOG=/opt/earth1-data/b2c1/chain.log
mkdir -p /opt/earth1-data/b2c1
echo "B2C1 START $(date -u +%FT%TZ) HEAD=$(git rev-parse --short HEAD)" >> "$LOG"

# candidate flag set (same block as afull_run.sh / freeze-0.9)
export EARTH1_HARDSHIP_MODE=gradient EARTH1_INCOME_CALIBRATION=v1 \
  EARTH1_SUBSTRATE_FLAG=c2plus_v1 EARTH1_C2PLUS_TABLES=c2plus_tables_v2.json \
  EARTH1_MORTALITY_MODE=gompertz EARTH1_GM_OTHER_SHARE=0.21407724082954704 \
  EARTH1_WANT_MODE=rr EARTH1_WANT_RR=4.933765606879083 \
  EARTH1_WEATHER_SCALE=0.020333010074315046 \
  EARTH1_DISTRESS_LAYOFFS=on EARTH1_LAYOFF_GAIN=0.0028
export EARTH1_RELIGIOSITY=1 EARTH1_RELIGIOSITY_FILE=religiosity_factbook.json \
  EARTH1_INJECT=religiosity

echo "== bitwise assert ==" >> "$LOG"
$PY - >> "$LOG" 2>&1 <<'PYEOF'
import os
import numpy as np
from earth1.alive import birth_world
w_on = birth_world(20000, 777, substrate="c2plus_v1")
os.environ.pop("EARTH1_RELIGIOSITY")
w_off = birth_world(20000, 777, substrate="c2plus_v1")
assert w_on.civ.religiosity is not None and w_off.civ.religiosity is None
for name in ("forces", "openness", "empathy", "age", "education", "income"):
    a, b = getattr(w_on.civ, name), getattr(w_off.civ, name)
    assert np.array_equal(a, b), f"BITWISE VIOLATION: civ.{name}"
for name in ("wage", "wealth", "employed", "firm_health"):
    a, b = getattr(w_on.life, name), getattr(w_off.life, name)
    assert np.array_equal(a, b), f"BITWISE VIOLATION: life.{name}"
print("BITWISE ASSERT PASS: flag-on differs only in civ.religiosity")
PYEOF
grep -q "BITWISE ASSERT PASS" "$LOG" || { echo "B2C1 ABORT: bitwise assert failed" >> "$LOG"; exit 2; }

echo "== adjacency gate (prime) ==" >> "$LOG"
$PY scripts/feature_adjacency_gate.py >> "$LOG" 2>&1 || { echo "B2C1 ABORT: gate blocked" >> "$LOG"; exit 3; }

echo "== feature worlds ==" >> "$LOG"
export SB_OUT=/opt/earth1-data/b2c1
for S in 4242 5151 6363; do
  $PY scripts/scoreboard/run_features.py $S >> "$LOG" 2>&1 &
done
wait

echo "== rescore ==" >> "$LOG"
export SB1_FEATURES_DIR=/opt/earth1-data/b2c1 SB1_OUT_SUFFIX=_b2c1
$PY scripts/scoreboard/score_sb1.py goqa_dev wvs_heldout wvs_extended >> "$LOG" 2>&1
echo "B2C1 COMPLETE $(date -u +%FT%TZ)" >> "$LOG"
