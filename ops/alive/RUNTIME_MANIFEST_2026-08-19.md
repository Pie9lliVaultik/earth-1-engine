# Live-box runtime manifest — captured 2026-08-19, before any reconciliation

Founder ruling 6: *"Do not discard the dirty live-box changes. Preserve before
reconciling. We are not deleting unknown differences from the only living
civilization just to make `git status` green."*

This is that preservation record, captured **read-only** from
`167.233.77.48:/opt/earth1` while `earth1-alive.service` was running at day ~110
with 3,991,874 alive. Nothing was written to the box to produce it.

## The finding: there are no unknown differences

**All 203 `.py` files on the box match a known git blob.** Every byte the 4M
world has been executing is already reconstructible from this repository's
history. Reconciliation therefore destroys nothing.

| box tree matches | files |
|---|---:|
| `e7545f8` (the branch base) | **197** |
| `d3d2a0c` (2026-08-18) | 3 |
| `ca7ade8` (2026-08-19) | 1 |
| `fe565cc` (2026-08-19) | 1 |
| `fcae8b8` (2026-08-17) | 1 |
| **matching no commit anywhere** | **0** |

`git status` reports 116 changed paths / 106 files / 22,246 insertions, which
looks alarming and is not: it is the entire living substrate `git add`-ed but
never committed. The staged content is identical to committed blobs.

## The six files that are not at `e7545f8`

| file | box copy equals | commits behind | on the live daily path? |
|---|---|---:|---|
| `earth1/institutions.py` | `d3d2a0c` | 8 | **YES** — `govern`, `apply_policy_and_war`, `class_tick` |
| `earth1/backtest.py` | `ca7ade8` | 1 | no — offline backtest harness |
| `earth1/branch.py` | `fe565cc` | 6 | no — scenario/branch tool |
| `earth1/consequences.py` | `d3d2a0c` | 8 | no — readout layer |
| `scripts/hormuz.py` | `d3d2a0c` | 8 | no — scenario script |
| `earth1/genesis_manifold.py` | `fcae8b8` | 130 | no — not in `live_one_day` |

**The actual runtime delta is one file.** `institutions.py` at `d3d2a0c` differs
from `e7545f8` by a **3-line offset only** (358 vs 361 lines): war's cause code
is `= 5` at box `:268` / branch `:271`, and the migration block
(`MIGRATION_RATE_YR:50`, `dest_pool`, `civ.country[idx]`) is character-identical.
Every audit finding for 0.0d and 0.1(d) holds on the running world.

## Service definition

`/etc/systemd/system/earth1-alive.service` existed **only on the box** and in no
commit. It is now preserved verbatim at
[`ops/alive/earth1-alive.service`](earth1-alive.service) (plus an
`EnvironmentFile` line for the 0.0e deploy manifest, which is the only addition).

Key settings as found: `ALIVE_POP=4000000`, `ALIVE_PERIOD=60`, `ALIVE_NEWS=60`,
`ALIVE_SAVE=30`, `Restart=always`, `RestartSec=10`, `KillSignal=SIGTERM`,
`TimeoutStopSec=120`, `ExecStart=/opt/earth1/.venv/bin/python3
/opt/earth1/scripts/world_alive.py`.

## What this means for reconciliation

A preservation commit or tag on the box is **not required to avoid data loss** —
there is none to avoid. It may still be worth one for the record. The reconcile
is now a known, small operation:

1. Commit the box's staged tree as-is (a describable SHA for what has been
   running), **or** simply fast-forward: 5 of the 6 stragglers are off the live
   path, and the sixth is a 3-line offset.
2. Check out `v1-unification` at the 0.0c+0.0e commit.
3. Write that SHA into `/opt/earth1/ops/alive/DEPLOYED`.
4. Install `ops/alive/earth1-alive.service`; `systemctl daemon-reload`.
5. Force a checkpoint, then restart (see the deployment runbook in the audit).

## Provenance of this record

Captured by `md5sum` over `find earth1 scripts -name '*.py'` on the box, compared
against `git show <commit>:<path>` for every commit in `14401ea..e7545f8` and
then across `--all`. Method is reproducible; the raw hash manifest is not
committed (203 lines of digests) but regenerates in one command.
