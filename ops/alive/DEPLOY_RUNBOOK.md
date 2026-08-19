# Deployment runbook — Epoch 0 → Epoch 1

**Purpose:** migrate the live 4M world onto the provenanced, exactly-persistent
path (0.0e + 0.0c, frozen at tag **`v1-persistence-deploy-1`** = `ae65bcd`).

**Authorised:** founder, 2026-08-19. **Owner: Claude Code**, which executes
every step itself with abort gates. This document is the record of what it
runs, not a hand-off. Deployment target is frozen at the tag above so it cannot
drift mid-deploy.

---

## ⚠️ READ FIRST — the living world has never been backed up

`CLAUDE.md` records the 2026-08-19 rehearsal finding: `run_backup.sh` backs up
`data/living/` (the **old 200K** world), **not** `data/alive/` (the real 4M
world). `earth1-backup.timer` has been firing successfully against the wrong
directory.

**Consequence:** step 1 below is not a formality. It is the **first backup this
civilization will ever have**, and it must complete and verify *before* the
process is stopped. Do not proceed past step 1 on a failed or unverified copy.

Budget for size: the Bible records the world at ~18 GB. Check free space on the
Storage Box and on `/opt` before starting.

---

## Step 0 — pre-flight

```bash
ssh -i ~/.ssh/earth1_hetzner root@167.233.77.48
date -u
systemctl is-active earth1-alive
df -h /opt                       # room for a second copy?
ls -la /opt/earth1/data/alive/
cat /opt/earth1/data/alive/state.json
tail -3 /var/log/earth1-alive.log
```

Record: world day, alive count, wall-clock, `git rev-parse HEAD` (expect
`14401ea`), and that `RUNTIME_MANIFEST_2026-08-19.md` still describes the tree.

**Abort if** the service is not active, or `/opt` has less free space than the
world is large.

## Step 1 — final v0 checkpoint, backed up off-box

`SIGTERM` makes the daemon finish the current day, save, and exit cleanly
(`world_alive.py`, `_sigterm`). `systemctl stop` is a deliberate stop, so
`Restart=always` will **not** bring it back.

```bash
systemctl stop earth1-alive           # finishes the day, saves, exits
tail -5 /var/log/earth1-alive.log     # expect "saved at day N"

cd /opt/earth1/data/alive
sha256sum world.pkl adj.npz state.json | tee /opt/earth1/EPOCH0_CHECKSUMS.txt
ls -la

# THE FIRST REAL BACKUP OF THIS CIVILIZATION
rsync -avP -e 'ssh -p 23' world.pkl adj.npz state.json \
      /opt/earth1/EPOCH0_CHECKSUMS.txt \
      u652120@u652120.your-storagebox.de:earth1/epoch0-2026-08-19/

# VERIFY the copy rather than trusting rsync's exit code
ssh -p 23 u652120@u652120.your-storagebox.de \
    "cd earth1/epoch0-2026-08-19 && sha256sum -c EPOCH0_CHECKSUMS.txt"
```

**Do not continue until the remote `sha256sum -c` prints OK for every file.**

Record alongside the backup: world day, wall-clock, population, the running
commit (`14401ea`), and a copy of `ops/alive/RUNTIME_MANIFEST_2026-08-19.md`.

## Step 2 — preservation commit (MANDATORY per founder ruling)

An immutable anchor for the exact composite tree that produced the first 110
days. **Never deploy from this tag.**

```bash
cd /opt/earth1
git add -A
git -c user.name='Earth-1 world box' -c user.email='ops@earthling.local' \
    commit -m 'PRESERVATION: exact tree the 4M world ran for Epoch 0 (days 0-~110)

Not for deployment. This commit exists so the first 110 days of the
living civilization can be reconstructed exactly. Captured before the
0.0c persistence migration.

Per ops/alive/RUNTIME_MANIFEST_2026-08-19.md, all 203 .py files here
match known blobs; six differ from e7545f8 and only institutions.py
(== d3d2a0c, a 3-line offset) is on the live daily path.'

git tag -a alive-pre-v1-persistence-2026-08-19 \
    -m 'Epoch 0: the 4M world as it actually ran, days 0-~110'
git rev-parse alive-pre-v1-persistence-2026-08-19   # RECORD THIS SHA
git push origin alive-pre-v1-persistence-2026-08-19  # if the box has a remote
```

If the box cannot push, record the SHA here and in the audit by hand.

## Step 3 — deploy the frozen tag

```bash
cd /opt/earth1
git fetch origin v1-unification
git checkout v1-persistence-deploy-1   # frozen tag == fe09377
git status --porcelain        # MUST be empty — the gate refuses otherwise

mkdir -p ops/alive
printf 'EARTH1_EXPECT_COMMIT=%s\n' "$(git rev-parse HEAD)" > ops/alive/DEPLOYED
cat ops/alive/DEPLOYED

install -m 644 ops/alive/earth1-alive.service \
        /etc/systemd/system/earth1-alive.service
systemctl daemon-reload

# the daemon compares these; they must match
sha256sum ops/alive/earth1-alive.service /etc/systemd/system/earth1-alive.service
```

## Step 4 — the one migration restart

```bash
systemctl set-environment EARTH1_MIGRATE_V0=1
systemctl start earth1-alive
sleep 90
tail -40 /var/log/earth1-alive.log
```

Expect, in order: the provenance line (commit, `dirty=False`, schema, snapshot),
`MIGRATED a v0 snapshot. It could not carry: presence, mobility`, the
`EPOCH BOUNDARY journaled` line, then normal ticking.

```bash
grep continuity_break /opt/earth1/data/alive/journal.jsonl | tail -1 | python3 -m json.tool
```

This record is the permanent epoch marker. **No causal benchmark may span it.**

## Step 5 — verify provenance, then force a v1 save

```bash
grep '"event": "startup"' /opt/earth1/data/alive/journal.jsonl | tail -1 \
  | python3 -m json.tool
```

Check every field: `code_commit` == `intended_commit` == `ae65bcd…`;
`dirty_worktree: false`; `service_matches: true`; `schema_version: 1`;
`snapshot_version: null` (it came from v0 — correct); population and world day
match step 0.

**Abort and investigate if any of those disagree.**

```bash
systemctl stop earth1-alive          # SIGTERM → immediate v1 save
cat /opt/earth1/data/alive/state.json   # expect schema_version 1, sha256, rng_persisted true

cd /opt/earth1/data/alive
sha256sum world.pkl world.adj.npz state.json | tee /opt/earth1/EPOCH1_CHECKSUMS.txt
rsync -avP -e 'ssh -p 23' world.pkl world.adj.npz state.json \
      /opt/earth1/EPOCH1_CHECKSUMS.txt \
      u652120@u652120.your-storagebox.de:earth1/epoch1-2026-08-19/
ssh -p 23 u652120@u652120.your-storagebox.de \
    "cd earth1/epoch1-2026-08-19 && sha256sum -c EPOCH1_CHECKSUMS.txt"
```

Note the graph filename changes to `world.adj.npz` at v1. The legacy `adj.npz`
can stay until step 7 as a fallback.

## Step 6 — the production acceptance test: a restart with ZERO discontinuity

```bash
systemctl unset-environment EARTH1_MIGRATE_V0
cp /opt/earth1/data/alive/state.json /tmp/state_before.json
systemctl start earth1-alive
sleep 90
tail -30 /var/log/earth1-alive.log
```

**Pass criteria — all must hold:**

- **No** `MIGRATED` line and **no** new `continuity_break` record.
- Startup record shows `schema_version: 1`, `snapshot_version: 1`,
  `rng_continued: true`.
- `woke up: day N` where N equals the day in `/tmp/state_before.json`.
- Alive count matches exactly.
- `checksum verified` in the wake-up line.

```bash
diff <(python3 -c "import json;d=json.load(open('/tmp/state_before.json'));print(d['day'],d['alive'],d['pop'])") \
     <(python3 -c "import json;d=json.load(open('/opt/earth1/data/alive/state.json'));print(d['day'],d['alive'],d['pop'])")
```

This is the moment restart continuity becomes **operationally** proven rather
than unit-tested.

## Step 7 — close the migration door permanently

```bash
systemctl show earth1-alive -p Environment    # must NOT contain EARTH1_MIGRATE_V0
```

Then prove a v0 snapshot now fails closed, **on a copy, never on the live world**:

```bash
cd /tmp && mkdir -p v0check && cd v0check
cp /opt/earth1/data/alive/../alive/world.pkl /dev/null 2>/dev/null || true
python3 - <<'EOF'
import sys; sys.path.insert(0,'/opt/earth1')
from earth1.persistence import load_world, SnapshotError
# point at the Epoch 0 backup pulled back from the Storage Box
try:
    load_world('/tmp/v0check/world.pkl')
    print("FAIL: a v0 snapshot loaded without opt-in")
except SnapshotError as e:
    print("PASS: fails closed —", str(e)[:120])
EOF
```

## Rollback

At any point before step 4 completes: `git checkout alive-pre-v1-persistence-2026-08-19`,
restore the Epoch 0 files from the Storage Box, reinstall the old unit (it is in
the preservation commit), `daemon-reload`, `start`. Epoch 0 is intact and
verified off-box from step 1.

---

## After this runbook

The world is in **Epoch 1: exactly persistent Earth**. From here,
`Save → Restart → Restore` preserves the civilization exactly, and every
subsequent restart must show zero discontinuity. Any future
`continuity_break` record is a defect, not a routine event.

**Remaining, and now overdue:** fix `run_backup.sh` to target `data/alive/`.
The timer has been backing up the wrong world; the two manual copies above are
the only backups of the living civilization that exist.
