#!/usr/bin/env bash
# Back up the LIVING world — data/alive/ — and verify the remote copy.
#
# Replaces the script that shipped before 2026-08-19, which backed up
# data/living/ (the old 200K opinion world) while the real 4M
# civilization went unprotected. The timer had been firing green for
# weeks against the wrong directory: a backup nobody had ever restored,
# of a world nobody was running.
#
# Three rules this script exists to enforce:
#   1. The canonical protected state is data/alive/, and nothing else.
#   2. A copy is not a backup until its checksum is verified ON THE FAR
#      END. rsync's exit code proves transport, not integrity.
#   3. No credential lives in this file. It reads the Storage Box target
#      from ops/alive/BACKUP_ENV (chmod 600, not in git).
#
# Retention: one dated directory per run, newest N kept. Snapshots are
# never overwritten in place, so a corrupt save cannot destroy the last
# good copy by being copied on top of it.

set -euo pipefail

ROOT="${EARTH1_ROOT:-/opt/earth1}"
ALIVE="$ROOT/data/alive"
ENV_FILE="$ROOT/ops/alive/BACKUP_ENV"
KEEP="${BACKUP_KEEP:-7}"
STAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"

log() { printf '%s  %s\n' "$(date -u +%H:%M:%S)" "$*"; }
die() { printf 'BACKUP FAILED: %s\n' "$*" >&2; exit 1; }

[ -f "$ENV_FILE" ] || die "no $ENV_FILE (needs BACKUP_TARGET, BACKUP_PORT)"
# shellcheck disable=SC1090
. "$ENV_FILE"
: "${BACKUP_TARGET:?BACKUP_TARGET not set in $ENV_FILE}"
: "${BACKUP_PORT:=23}"

[ -d "$ALIVE" ] || die "$ALIVE does not exist — is this the world box?"
[ -f "$ALIVE/state.json" ] || die "$ALIVE/state.json missing — refusing to back up a directory with no world in it"

# Refuse to archive a half-written save. save_world writes the checksum
# sidecar LAST, so its absence means an interrupted write — except for
# pre-schema worlds, which never had one.
SCHEMA="$(python3 -c "import json;print(json.load(open('$ALIVE/state.json')).get('schema_version'))" 2>/dev/null || echo null)"
if [ "$SCHEMA" != "null" ] && [ ! -f "$ALIVE/world.pkl.sha256" ]; then
    die "v$SCHEMA world has no world.pkl.sha256 — the last save did not complete"
fi

DAY="$(python3 -c "import json;print(json.load(open('$ALIVE/state.json'))['day'])" 2>/dev/null || echo unknown)"
DEST="$BACKUP_TARGET/alive/$STAMP-day$DAY"
log "backing up $ALIVE (schema v$SCHEMA, world day $DAY) -> $DEST"

cd "$ALIVE"
MANIFEST="$(mktemp)"
trap 'rm -f "$MANIFEST"' EXIT
# Hash every file we are about to send. The manifest must EXCLUDE
# itself: a previous run leaves BACKUP_MANIFEST.sha256 in place, so
# including it hashes the stale copy and then overwrites it — the first
# backup verifies and every one after it fails. Found by the local
# rehearsal before this ever ran on the box.
find . -maxdepth 1 -type f ! -name '*.tmp' \
     ! -name 'BACKUP_MANIFEST.sha256' -printf '%P\n' | sort \
  | xargs -r sha256sum > "$MANIFEST"
cp "$MANIFEST" ./BACKUP_MANIFEST.sha256

ssh -p "$BACKUP_PORT" "${BACKUP_TARGET%%:*}" "mkdir -p ${DEST#*:}" \
  || die "cannot create $DEST"

rsync -a --partial --inplace -e "ssh -p $BACKUP_PORT" \
      --exclude '*.tmp' ./ "$DEST/" \
  || die "rsync failed"

# THE VERIFICATION. A copy nobody checked is a hope, not a backup.
#
# The Storage Box runs a restricted shell: no `cd`, no remote pipes, so
# `cd DEST && sha256sum -c manifest` dies with "Command not found" and
# bare manifest names can't resolve (found in production, first run,
# 2026-08-19). Plain `sha256sum <explicit path>` IS supported, so the
# remote is asked to hash each file by full path and the comparison
# happens here. Same integrity guarantee: digests computed on the far
# end, compared against the local manifest.
log "verifying checksums on the far end"
RHOST="${BACKUP_TARGET%%:*}"
RDIR="${DEST#*:}"
REMOTE_SUMS="$(mktemp)"
LOCAL_SUMS="$(mktemp)"
trap 'rm -f "$MANIFEST" "$REMOTE_SUMS" "$LOCAL_SUMS"' EXIT
awk -v d="$RDIR" '{print d "/" $2}' "$MANIFEST" \
  | xargs ssh -p "$BACKUP_PORT" "$RHOST" sha256sum > "$REMOTE_SUMS" \
  || die "remote hashing failed at $DEST"
# strip the remote path prefix so both sides read `hash  name`
sed "s|  $RDIR/|  |" "$REMOTE_SUMS" | sort > "$LOCAL_SUMS.remote"
sort "$MANIFEST" > "$LOCAL_SUMS.local"
diff -u "$LOCAL_SUMS.local" "$LOCAL_SUMS.remote" \
  || die "REMOTE CHECKSUM MISMATCH at $DEST — the copy is not the world"
rm -f "$LOCAL_SUMS.remote" "$LOCAL_SUMS.local"

log "verified OK"

# retention: keep the newest $KEEP, never delete the only copy.
# Restricted shell: list remotely with a bare `ls -1`, decide locally,
# remove by explicit path.
LISTING="$(ssh -p "$BACKUP_PORT" "$RHOST" ls -1 "${BACKUP_TARGET#*:}/alive" 2>/dev/null || true)"
COUNT="$(printf '%s\n' "$LISTING" | grep -c . || true)"
if [ "$COUNT" -gt "$KEEP" ] && [ "$COUNT" -gt 1 ]; then
    log "pruning to newest $KEEP of $COUNT"
    printf '%s\n' "$LISTING" | sort | head -n "-$KEEP" | while read -r OLD; do
        [ -n "$OLD" ] || continue
        ssh -p "$BACKUP_PORT" "$RHOST" rm -rf "${BACKUP_TARGET#*:}/alive/$OLD"
    done
fi

printf '{"at":"%s","day":%s,"schema":%s,"dest":"%s","verified":true}\n' \
       "$STAMP" "$DAY" "$SCHEMA" "$DEST" >> "$ROOT/data/alive/backup_log.jsonl"
log "done — world day $DAY safe at $DEST"
