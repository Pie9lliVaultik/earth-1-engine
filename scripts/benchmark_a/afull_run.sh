#!/usr/bin/env bash
# =========================================================================
# A-FULL-1 campaign chain (measurement only) — execute ON PRIME from
# /opt/earth1 as root:  bash scripts/benchmark_a/afull_run.sh
#
# Tasks:  i  country means      (run_features.py x3 + score_sb1.py)
#         ii cohort cells       (frozen_score.py + A-v2 run_v2 earth1+score)
#         iii joints            (A-v2 run_v2 score + afull_joints.py)
#         iv held-out items     (A-v2 run_v2 score + afull_heldout_items.py)
#         v  cross-wave         (afull_crosswave.py; data-blocked fallback)
#         then afull_assemble.py -> $EARTH1_AFULL_OUT/AFULL_TABLE.json
#
# REUSE policy (S2 audit): confirm_targets + baselines stages are frozen and
# bit-reproducible c06b57d -> HEAD; they are COPIED, never re-run (the
# confirm_targets stage would rewrite the frozen joint_vectors npz).
# earth1 + score MUST re-run because physics changed (c008-c012).
# NEVER point EARTH1_AV2_OUT at data/benchmark_a or /opt/earth1-data/av2_c2plus.
# Stages continue on error so the assembler can mark missing rows PENDING.
# =========================================================================
set -u -o pipefail

REPO="${EARTH1_REPO:-/opt/earth1}"
PY="${EARTH1_PY:-$REPO/.venv/bin/python}"
export EARTH1_AFULL_OUT="${EARTH1_AFULL_OUT:-/opt/earth1-data/benchmark_a_full1}"
FROZEN_AV2="${AFULL_FROZEN_AV2:-/opt/earth1-data/av2_c2plus}"

# ---- frozen-dir guard: refuse to write into frozen artifact dirs ----------
for d in "$EARTH1_AFULL_OUT"; do
  case "$d" in
    /opt/earth1-data/benchmark_a|/opt/earth1-data/benchmark_a/*|\
    /opt/earth1-data/av2_c2plus|/opt/earth1-data/av2_c2plus/*|\
    "$REPO/data/benchmark_a"|"$REPO/data/benchmark_a"/*)
      echo "FATAL: EARTH1_AFULL_OUT=$d points at a FROZEN artifact dir" >&2
      exit 2;;
  esac
done

mkdir -p "$EARTH1_AFULL_OUT"
LOG="$EARTH1_AFULL_OUT/chain.log"
exec > >(tee -a "$LOG") 2>&1

echo "############################################################"
echo "# A-FULL-1 CHAIN START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# repo=$REPO  out=$EARTH1_AFULL_OUT  frozen_av2_src=$FROZEN_AV2"
echo "############################################################"

# ---- candidate flag set of record (0.9 freeze package + joint-MSM values,
#      data/cycles/msm_fit.json; authoritative per displacement protocol).
#      Flags are read at module IMPORT time -> exported before any python.
export EARTH1_SUBSTRATE=c2plus_v1
export EARTH1_SUBSTRATE_FLAG=c2plus_v1
export EARTH1_C2PLUS_TABLES=c2plus_tables_v2.json
export EARTH1_HARDSHIP_MODE=gradient
export EARTH1_INCOME_CALIBRATION=v1
export EARTH1_MORTALITY_MODE=gompertz
export EARTH1_GM_OTHER_SHARE=0.21407724082954704
export EARTH1_WANT_MODE=rr
export EARTH1_WANT_RR=4.933765606879083
export EARTH1_WEATHER_SCALE=0.020333010074315046
# NOTE (S2 audit): EARTH1_COHORT_READOUT is consumed by NO code in the repo;
# exported only because the campaign order names it, so it lands in the
# provenance stamp. The real task-ii instrument is frozen_score.py
# (reliability weighting is built in: every cell error weighted by frozen
# WVS cell n, frozen_cohort_cells.v1.json sha 55777e15f46c4d11).
export EARTH1_COHORT_READOUT=reliability_v1
# no-network rule
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

cd "$REPO" || { echo "FATAL: cannot cd $REPO"; exit 2; }
[ -x "$PY" ] || { echo "FATAL: python not found at $PY"; exit 2; }

# ---- provenance stamp (run_features.py writes none: patch-by-sidecar) -----
"$PY" - <<'PYEOF'
import json, os, subprocess, time
out = os.environ["EARTH1_AFULL_OUT"]
try:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                            text=True, cwd=os.getcwd()).stdout.strip()
except Exception:
    commit = None
stamp = {"campaign": "A-FULL-1",
         "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "git_commit": commit,
         "flags": {k: v for k, v in sorted(os.environ.items())
                   if k.startswith("EARTH1_")},
         "protocol": {"pop": 200000, "world_seeds": [42, 20260901, 20260902],
                      "warm_days": 60, "sb1_seeds": [4242, 5151, 6363],
                      "sb1_days": 180},
         "note": "EARTH1_COHORT_READOUT is inert (no consumer in repo); "
                 "recorded for the campaign order only."}
json.dump(stamp, open(os.path.join(out, "flags_stamp.json"), "w"), indent=1)
print("flags stamp written:", os.path.join(out, "flags_stamp.json"))
PYEOF

FAILED=0
run_stage() {  # run_stage <name> <cmd...>
  local name="$1"; shift
  echo ""
  echo "=== AFULL STAGE: $name === $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if "$@"; then
    echo "=== STAGE OK: $name ==="
  else
    echo "=== STAGE FAILED: $name (rc=$?) — continuing; assembler will mark PENDING ==="
    FAILED=$((FAILED + 1))
  fi
}

backup_once() {  # backup_once <file>  (preserve pre-campaign artifact once)
  local f="$1" bdir="$EARTH1_AFULL_OUT/backup_pre_afull"
  [ -f "$f" ] || return 0
  mkdir -p "$bdir"
  [ -f "$bdir/$(basename "$f")" ] || cp -p "$f" "$bdir/"
}

# =========================================================================
# TASK i — country means (four-arm table earth1/mrsp/naive/region).
# Regenerate features under the PINNED flag set (today's features_{seed}
# carry no provenance stamp -> rejected; S2 caveat).
# =========================================================================
export SB_OUT="$EARTH1_AFULL_OUT/scoreboard"
mkdir -p "$SB_OUT"
for seed in 4242 5151 6363; do
  run_stage "task-i-features-seed-$seed" \
    "$PY" scripts/scoreboard/run_features.py "$seed"
done

stage_i_install_features() {
  local ok=0
  for seed in 4242 5151 6363; do
    if [ -f "$SB_OUT/features_$seed.json" ]; then
      backup_once "data/cycles/features_$seed.json"
      cp "$SB_OUT/features_$seed.json" "data/cycles/features_$seed.json" && ok=$((ok+1))
    fi
  done
  [ "$ok" -eq 3 ]
}
run_stage "task-i-install-features" stage_i_install_features

stage_i_score() {
  backup_once "data/cycles/sb1_goqa_dev.json"
  backup_once "data/cycles/sb1_wvs_heldout.json"
  "$PY" scripts/scoreboard/score_sb1.py goqa_dev wvs_heldout || return 1
  # score_sb1's 'goqa_dev' estate == the campaign's pew_frame_dev
  # (data/concordance/goqa_dev.json, 469 items, judge-free by construction)
  cp data/cycles/sb1_goqa_dev.json "$EARTH1_AFULL_OUT/" && \
  cp data/cycles/sb1_wvs_heldout.json "$EARTH1_AFULL_OUT/"
}
run_stage "task-i-score-sb1" stage_i_score

# =========================================================================
# TASK ii (a) — frozen-cell reliability-weighted readout (physics-invariant
# floor; 18333 frozen cells, weights = frozen WVS cell n). ~1 min.
# =========================================================================
stage_ii_frozen() {
  backup_once "data/cycles/frozen_afull1_c2plus.json"
  "$PY" scripts/calibrate/frozen_score.py afull1_c2plus || return 1
  cp data/cycles/frozen_afull1_c2plus.json "$EARTH1_AFULL_OUT/"
}
run_stage "task-ii-frozen-score" stage_ii_frozen

# =========================================================================
# TASK ii (b) + iii + iv — full-fidelity A-v2 protocol on candidate
# substrate: copy frozen inputs, re-run earth1 + score ONLY.
# =========================================================================
export EARTH1_AV2_OUT="$EARTH1_AFULL_OUT/av2"
mkdir -p "$EARTH1_AV2_OUT"

stage_av2_inputs() {
  # frozen inputs: copy-not-move, never regenerate (confirm_targets stage
  # would rewrite the frozen npz in /opt/earth1-data/benchmark_a).
  local src f
  for f in confirm_targets_v2.json baselines_confirm_v2.json \
           targets_v1.json baselines_v1.json; do
    if [ ! -f "$EARTH1_AV2_OUT/$f" ]; then
      if [ -f "$FROZEN_AV2/$f" ]; then src="$FROZEN_AV2/$f"
      elif [ -f "$REPO/data/benchmark_a/$f" ]; then src="$REPO/data/benchmark_a/$f"
      else echo "missing frozen input: $f"; return 1; fi
      cp "$src" "$EARTH1_AV2_OUT/$f" || return 1
      echo "copied $src -> $EARTH1_AV2_OUT/$f"
    fi
  done
}
run_stage "task-ii-av2-frozen-inputs" stage_av2_inputs
run_stage "task-ii-av2-earth1" "$PY" scripts/benchmark_a/run_v2.py earth1
run_stage "task-ii-av2-score"  "$PY" scripts/benchmark_a/run_v2.py score

# =========================================================================
# TASKS iii / iv / v — dedicated A-FULL-1 harnesses (built separately;
# skipped with a log line if not present so the chain always completes).
# =========================================================================
for harness in afull_joints.py afull_heldout_items.py afull_crosswave.py; do
  if [ -f "$REPO/scripts/benchmark_a/$harness" ]; then
    run_stage "harness-$harness" "$PY" "scripts/benchmark_a/$harness"
  else
    echo ""
    echo "=== AFULL STAGE: harness-$harness === SKIPPED (script not present;"
    echo "    assembler will mark its rows PENDING) ==="
  fi
done

# =========================================================================
# ASSEMBLE — one table, one row per (task x estate); missing -> PENDING.
# =========================================================================
run_stage "assemble" "$PY" scripts/benchmark_a/afull_assemble.py

echo ""
echo "############################################################"
echo "AFULL CHAIN COMPLETE $(date -u +%Y-%m-%dT%H:%M:%SZ) (failed stages: $FAILED)"
echo "table: $EARTH1_AFULL_OUT/AFULL_TABLE.json   log: $LOG"
echo "############################################################"
[ "$FAILED" -eq 0 ]
