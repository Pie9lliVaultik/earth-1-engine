#!/usr/bin/env bash
# Restore rehearsal — pull a backup back and LOAD it, off production.
#
# An unrestored backup is a hope. This script closes that loop: it
# fetches a dated backup from the Storage Box into a scratch directory,
# verifies its checksums locally, and then actually constructs the World
# through the canonical loader — which is the only thing that proves the
# bytes are a civilization and not just the right number of them.
#
# It NEVER touches data/alive/. It refuses to run if asked to.
#
#   ops/alive/verify_restore.sh                 # newest backup
#   ops/alive/verify_restore.sh 2026-08-19T...  # a specific one

set -euo pipefail

ROOT="${EARTH1_ROOT:-/opt/earth1}"
ENV_FILE="$ROOT/ops/alive/BACKUP_ENV"
SCRATCH="${RESTORE_SCRATCH:-/tmp/earth1-restore-rehearsal}"

log() { printf '%s  %s\n' "$(date -u +%H:%M:%S)" "$*"; }
die() { printf 'RESTORE REHEARSAL FAILED: %s\n' "$*" >&2; exit 1; }

case "$SCRATCH" in
  *"/data/alive"*) die "refusing to restore into the live world directory" ;;
esac

[ -f "$ENV_FILE" ] || die "no $ENV_FILE"
# shellcheck disable=SC1090
. "$ENV_FILE"
: "${BACKUP_TARGET:?}"
: "${BACKUP_PORT:=23}"
HOST="${BACKUP_TARGET%%:*}"
BASE="${BACKUP_TARGET#*:}"

WHICH="${1:-}"
if [ -z "$WHICH" ]; then
    # restricted shell on the Storage Box: no remote pipes, so list
    # remotely and sort locally. Only timestamp-named dirs are backups:
    # annulled ones are renamed TAINTED-DO-NOT-RESTORE-* precisely so
    # nothing restores them — the first real rehearsal run picked the
    # tainted dir via a bare `sort | tail -1` and failed on it.
    WHICH="$(ssh -p "$BACKUP_PORT" "$HOST" ls -1 "$BASE/alive" \
             | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}T' | sort | tail -1)"
    [ -n "$WHICH" ] || die "no restorable backups found at $BASE/alive"
fi
log "rehearsing restore of $WHICH"

rm -rf "$SCRATCH"; mkdir -p "$SCRATCH"
rsync -a -e "ssh -p $BACKUP_PORT" "$HOST:$BASE/alive/$WHICH/" "$SCRATCH/" \
  || die "fetch failed"

log "verifying checksums locally"
( cd "$SCRATCH" && sha256sum -c BACKUP_MANIFEST.sha256 --quiet ) \
  || die "checksum mismatch after fetch — the stored copy is corrupt"

log "loading the world through the canonical loader"
# the canonical loader needs the project venv (numpy/scipy); bare
# python3 on the box is the system interpreter and cannot load a world
PYBIN="${EARTH1_PYTHON:-$ROOT/.venv/bin/python3}"
[ -x "$PYBIN" ] || PYBIN=python3
EARTH1_ROOT="$ROOT" SCRATCH="$SCRATCH" "$PYBIN" - <<'PY' || die "the backup did not load as a world"
import json, os, sys
root = os.environ["EARTH1_ROOT"]; scratch = os.environ["SCRATCH"]
sys.path.insert(0, root)
from pathlib import Path
from earth1 import persistence

d = Path(scratch)
pkl = d / "world.pkl"
if not pkl.exists():
    raise SystemExit("no world.pkl in the backup")

st = json.loads((d / "state.json").read_text())
schema = st.get("schema_version")
legacy = d / "adj.npz"
w, rng_state, info = persistence.load_world(
    pkl,
    allow_v0_migration=(schema is None),
    adj_path=(legacy if legacy.exists() else None))

alive = int(w.health.alive.sum())
print(f"  loaded: day {w.day}, pop {w.civ.n:,}, alive {alive:,}, "
      f"schema v{info['schema_version']}, rng={'yes' if rng_state else 'no'}")

# the world must be WHOLE, not merely loadable
missing = [f for f in persistence.PERSISTENT_FIELDS
           if getattr(w, f, None) is None]
if missing:
    raise SystemExit(f"restored world is missing state: {missing}")

if st.get("day") is not None and int(st["day"]) != int(w.day):
    raise SystemExit(f"day mismatch: state.json {st['day']} vs world {w.day}")
if st.get("alive") is not None and int(st["alive"]) != alive:
    raise SystemExit(f"alive mismatch: state.json {st['alive']} vs world {alive}")

print("  RESTORE REHEARSAL PASSED — the backup is a civilization")
PY

log "cleaning up $SCRATCH"
rm -rf "$SCRATCH"
printf '{"at":"%s","rehearsed":"%s","passed":true}\n' \
       "$(date -u +%Y-%m-%dT%H%M%SZ)" "$WHICH" \
       >> "$ROOT/data/alive/backup_log.jsonl"
log "done"
