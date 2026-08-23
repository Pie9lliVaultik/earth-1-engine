#!/usr/bin/env bash
# Archive the live epoch (ops/alive/EPOCH_POLICY.md). Run ONLY after the
# daemon has been stopped (it finishes the day and saves on SIGTERM) and
# BEFORE any new epoch is born. Idempotent on failure: the live
# directory is renamed only after every integrity step has passed.
#
#   archive_epoch.sh <epoch-number> <running-commit-sha>
#
# Steps: refuse if the daemon is active; verify the last save completed
# (sha256 sidecar present and matching); write ARCHIVE_MANIFEST.json
# (identity: day, alive, seed, snapshot sha256, world hash, RNG presence,
# commit, physics version, config hash from the journal, per-file
# sha256); copy to the Storage Box under archive/ (outside the pruned
# alive/ retention) with far-end checksum verification; restore-rehearse
# that copy through the canonical loader; then rename data/alive ->
# data/archive/epochN-final-dayD and make it read-only.
set -euo pipefail
ROOT="${EARTH1_ROOT:-/opt/earth1}"
ALIVE="$ROOT/data/alive"
ENV_FILE="$ROOT/ops/alive/BACKUP_ENV"
EPOCH="${1:?epoch number}"
COMMIT="${2:?running commit sha}"
PYBIN="${EARTH1_PYTHON:-$ROOT/.venv/bin/python3}"
log() { printf '%s  %s\n' "$(date -u +%H:%M:%S)" "$*"; }
die() { printf 'ARCHIVE FAILED: %s\n' "$*" >&2; exit 1; }

systemctl is-active --quiet earth1-alive && die "earth1-alive is ACTIVE — stop it first (it checkpoints on SIGTERM)"
[ -f "$ALIVE/world.pkl" ] || die "no world.pkl in $ALIVE"
[ -f "$ALIVE/world.pkl.sha256" ] || die "no world.pkl.sha256 — last save did not complete"
cd "$ALIVE"
log "verifying the final checkpoint sidecar"
[ "$(sha256sum world.pkl | cut -d' ' -f1)" = "$(cut -d' ' -f1 world.pkl.sha256)" ] || die "world.pkl does not match its sidecar"
DAY="$($PYBIN -c "import json;print(json.load(open('state.json'))['day'])")"
NAME="epoch${EPOCH}-final-day${DAY}"
log "archiving $NAME"

log "computing identity (loads the world once; minutes at 4M)"
EARTH1_ROOT="$ROOT" ALIVE="$ALIVE" EPOCH="$EPOCH" COMMIT="$COMMIT" "$PYBIN" - <<'PY' || die "identity computation failed"
import json, os, sys, hashlib, time
sys.path.insert(0, os.environ["EARTH1_ROOT"])
from pathlib import Path
from earth1 import persistence
d = Path(os.environ["ALIVE"])
st = json.loads((d / "state.json").read_text())
w, rng_state, info = persistence.load_world(d / "world.pkl")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""): h.update(c)
    return h.hexdigest()
files = {f.name: {"bytes": f.stat().st_size, "sha256": sha(f)}
         for f in sorted(d.iterdir()) if f.is_file() and f.name != "ARCHIVE_MANIFEST.json"}
startup = None
try:
    for line in open(d / "journal.jsonl"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("event") == "startup": startup = rec
except OSError: pass
ep = {}
try: ep = json.loads((d / "EPOCH.json").read_text())
except (OSError, ValueError): pass
man = {"epoch": int(os.environ["EPOCH"]), "status": "ARCHIVED / READ-ONLY / HISTORICAL",
       "archived_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "world_uuid": ep.get("world_uuid") or st.get("world_uuid"),
       "final_day": int(w.day), "population": int(w.civ.n), "alive": int(w.health.alive.sum()),
       "seed": int(w.civ.seed), "schema_version": info["schema_version"],
       "snapshot_sha256": st.get("sha256"), "checksum_state": info.get("checksum"),
       "world_hash": persistence.world_hash(w), "rng_state_persisted": rng_state is not None,
       "git_commit": os.environ["COMMIT"],
       "physics_version": getattr(__import__("earth1.alive", fromlist=["x"]), "PHYSICS_VERSION", None),
       "last_startup_provenance": startup, "epoch_record": ep or None,
       "files": files}
(d / "ARCHIVE_MANIFEST.json").write_text(json.dumps(man, indent=1, default=str))
print(json.dumps({k: man[k] for k in ("final_day","alive","seed","snapshot_sha256","world_hash","rng_state_persisted","git_commit","physics_version")}, indent=1))
PY

[ -f "$ENV_FILE" ] || die "no $ENV_FILE"
. "$ENV_FILE"; : "${BACKUP_TARGET:?}"; : "${BACKUP_PORT:=23}"
HOST="${BACKUP_TARGET%%:*}"; BASE="${BACKUP_TARGET#*:}"
DEST="$BASE/archive/$NAME"
find . -maxdepth 1 -type f ! -name '*.tmp' ! -name 'BACKUP_MANIFEST.sha256' -printf '%P\n' | sort | xargs -r sha256sum > BACKUP_MANIFEST.sha256
ssh -p "$BACKUP_PORT" "$HOST" "mkdir -p $DEST" || die "cannot create $DEST"
log "copying to $HOST:$DEST"
rsync -a --partial --partial-dir=.rsync-partial -e "ssh -p $BACKUP_PORT" --exclude '*.tmp' --exclude '.rsync-partial' --exclude '.backup-stage' ./ "$HOST:$DEST/" || die "rsync failed"
log "verifying on the far end"
awk -v d="$DEST" '{print d "/" $2}' BACKUP_MANIFEST.sha256 | xargs ssh -p "$BACKUP_PORT" "$HOST" sha256sum | sed "s|  $DEST/|  |" | sort > /tmp/archive_remote.sums
sort BACKUP_MANIFEST.sha256 > /tmp/archive_local.sums
diff -u /tmp/archive_local.sums /tmp/archive_remote.sums || die "REMOTE CHECKSUM MISMATCH"
log "far-end copy verified"

log "restore rehearsal from the archive copy"
SCR="/tmp/earth1-archive-rehearsal"; rm -rf "$SCR"; mkdir -p "$SCR"
rsync -a -e "ssh -p $BACKUP_PORT" "$HOST:$DEST/" "$SCR/" || die "rehearsal fetch failed"
( cd "$SCR" && sha256sum -c BACKUP_MANIFEST.sha256 --quiet ) || die "rehearsal checksum mismatch"
EARTH1_ROOT="$ROOT" SCR="$SCR" "$PYBIN" - <<'PY' || die "archive did not load as a world"
import json, os, sys
sys.path.insert(0, os.environ["EARTH1_ROOT"])
from pathlib import Path
from earth1 import persistence
d = Path(os.environ["SCR"]); man = json.loads((d / "ARCHIVE_MANIFEST.json").read_text())
w, rng_state, info = persistence.load_world(d / "world.pkl")
assert int(w.day) == man["final_day"], "day mismatch"
assert int(w.health.alive.sum()) == man["alive"], "alive mismatch"
assert persistence.world_hash(w) == man["world_hash"], "world hash mismatch"
assert (rng_state is not None) == man["rng_state_persisted"]
print(f"  ARCHIVE RESTORE PASSED: day {w.day}, alive {man['alive']:,}, hash {man['world_hash'][:16]}")
PY
rm -rf "$SCR"

ARCH="$ROOT/data/archive/$NAME"
mkdir -p "$ROOT/data/archive"
[ -e "$ARCH" ] && die "$ARCH already exists"
mv "$ALIVE" "$ARCH"
chmod -R a-w "$ARCH"
printf '{"at":"%s","archived":"%s","remote":"%s","verified":true,"restore_rehearsed":true}\n' "$(date -u +%Y-%m-%dT%H%M%SZ)" "$ARCH" "$HOST:$DEST" >> "$ROOT/data/archive/archive_log.jsonl"
log "EPOCH $EPOCH ARCHIVED at $ARCH (read-only) and $HOST:$DEST"
