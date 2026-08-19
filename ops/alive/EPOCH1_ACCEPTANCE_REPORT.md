# EPOCH 1 PRODUCTION ACCEPTANCE REPORT

**2026-08-19 · executed end-to-end by Claude Code · founder criteria of the runbook template**

**VERDICT: ACCEPTED.** All ten items green, every control demonstrated in the
failing direction. The living world is at **day 290, 3,962,337 alive**, ticking
under provenanced code with exact persistence, off-site memory, and rehearsed
restore.

```
known code + known state + off-site memory + exact restart   ✓
```

## Deployed code

| | |
|---|---|
| frozen target | `v1-persistence-deploy-1` → `ae65bcd` |
| running | **`d2e55b0`** = `ae65bcd` + three fixes found *by this acceptance run* |
| physics delta from target | `git diff ae65bcd..d2e55b0 -- earth1/ scripts/` → **`earth1/persistence.py` only** — the migration/load path. `live_one_day` and every physics module byte-identical |

The three fixes, each a production MISS worked through under Part XI.A
(recorded exactly → instrument verified → diagnosed → smallest correction →
retested):

1. **`6eae4bc`** — Storage Box restricted shell has no `cd` and no remote
   pipes; far-end verification rewritten to explicit-path hashing compared
   locally. *(Found: backup run 1 failed its own verification.)*
2. **`8258f7c`** — backing up a **live** directory can never agree with
   itself; consistent staging via hardlinks (atomic-replace files) + real
   copies (append/truncate files). *(Found: backup run 2 failed — the daemon
   appends to `journal.jsonl` every tick.)*
3. **`d2e55b0`** — **the serious one.** `_restore_v0` printed "rebuilt at
   birth values" while rebuilding nothing: the first migration left
   `presence=None, mobility=None`, so Epoch-1 attempt 1 ran ~20 world-days
   with contagion, shared attention and mobility **switched off** — the exact
   N2 defect 0.0c exists to prevent, reintroduced by its own migration path.
   *(Found: the restore rehearsal on prime loaded the first v1 snapshot and
   asserted every persistent field non-None.)* Fix rebuilds both subsystems,
   adds fail-closed refusal of any v1 snapshot carrying a gating field as
   None, plus the two regression tests the suite was missing.

**Remediation of the miss:** the tainted attempt (days 284→304) was
**annulled and discarded**, the world restored to the verified day-284 v0
checkpoint, and migration re-run under fixed code. Physics evidence the fix
is real: attempt 1 reached day 286 with 3,963,038 alive; the fixed run has
**3,963,003** — 35 more deaths in two days, the road-death and contagion
channels actually running.

## The ten criteria

| # | item | evidence | verdict |
|---|---|---|---|
| 1 | **Frozen code provenance** | startup journal: `code_commit == intended_commit == d2e55b0f27af`, `dirty_worktree: false`, `service_matches: true` (unit sha256 `fe9916c4…` identical repo↔installed), config hash journaled | ✅ |
| 2 | **Verified off-box `data/alive/` backup** | day-240 (`7ae853d6…`), day-284 final (`efc3af26…`), day-286 v1 (`9d914aef…`) — all hashed independently **on the Storage Box**, all 3/3 match | ✅ |
| 3 | **Corrupted-copy control fails** | size-preserving mid-file byte flip → `783753d1…` REJECTED; truncation → `b0db229e…` REJECTED; clean copy → MATCH | ✅ |
| 4 | **Explicit Epoch 0→1 boundary** | `continuity_break / legacy_v0_missing_presence_mobility`, `epoch: 1`, `bit_continuous: false`, journaled at 15:55 **before the first tick**; exactly **2** boundary events in the journal — the annulled first attempt and the real one — plus one self-describing `epoch_annulled` record | ✅ |
| 5 | **v1 snapshot/restore** | `state.json`: `schema_version: 1`, `sha256: 9d914aef…`, `rng_persisted: true`; sidecar written last; atomic tmp+replace | ✅ |
| 6 | **Perturbed-field control fails** | on prime, on the real 4M restored world: baseline `96e1aba8…`, one agent's `flourishing.hope` moved by **1e-9** → `184d7f0a…` **DETECTED**, hash stable under undo | ✅ |
| 7 | **Exact restart continuity** | two zero-discontinuity restarts (day 286 under `d2e55b0`, day 286→290 running): `rng_continued: true`, `snapshot_schema: 1`, day/alive exact, no MIGRATED line, no new boundary, `checksum verified` | ✅ |
| 8 | **Recurring backup ×2** | runs at 15:59:45 and 16:00:22, both far-end verified, retention pruning working (anchors sort last and survive) | ✅ |
| 9 | **Restore rehearsal** | on prime, through the canonical loader: manifest OK → whole civilization (all 14 persistent fields non-None), day/alive match `state.json`, checksum verified, RNG carried | ✅ |
| 10 | **Migration override removed; v0 fails closed** | `systemctl show` environment carries no `EARTH1_MIGRATE_V0`; the **real** epoch-0 artifact refused by the canonical loader: *"pre-schema (v0) snapshot… cannot carry presence, mobility or the RNG stream"* | ✅ |

## Epoch timeline

| moment | world day | alive | note |
|---|---|---|---|
| Epoch 0 first backup | 240 | 3,970,839 | first off-box copy in the world's existence |
| Epoch 0 final checkpoint | 284 | 3,963,340 | SIGTERM save; "the world is paused, not lost" |
| ~~Epoch 1 attempt 1~~ | ~~284→304~~ | — | **ANNULLED** — reduced physics (presence/mobility None); state quarantined in `data/alive/tainted-epoch1-attempt1/` and `TAINTED-DO-NOT-RESTORE-epoch1-attempt1` on the Storage Box; forensic only |
| **Epoch 1** | **284 →** | 3,963,340 → | migrated under `d2e55b0`, boundary journaled before first tick |
| first v1 snapshot | 286 | 3,963,003 | `9d914aef…`, off-box verified |
| at report time | 290 | 3,962,337 | full physics, ticking every 60 s |

**Standing rule:** no causal benchmark may span the day-284 boundary, and
nothing may cite the annulled attempt as world history.

## Epoch-0 preservation

Runtime tree committed on the box as **`9b983d1`**, tagged
`alive-pre-v1-persistence-2026-08-19` (3 commits: staged tree + operational
scripts including the wrong-target `run_backup.sh` as evidence + supervisor
config). The box cannot push (no GitHub credentials) — the tag lives on the
box; every blob also exists in this repo's history per the runtime manifest.
Pushing the ref when convenient is housekeeping, not risk.

## Operational notes

- **The v0 destructive-save window is closed.** v1 saves are atomic
  (tmp+replace, sidecar last). Under v0 there was a multi-minute window every
  30 minutes with no complete world on disk.
- Backups run from a consistent stage; the epoch anchors
  (`epoch0-day240`, `epoch0-final-day284`, `epoch1-day286-v2`) sort after
  timestamped entries and survive retention. Moving them out of the pruned
  directory is nice-to-have housekeeping.
- Legacy `adj.npz` still sits beside the v1 files and rides along in backups
  (~390 MB); removable after a deliberate decision, not urgent.
- Prime's system python lacks numpy; the repo venv works. Prime's displaced
  lab artifacts are preserved in `/root/prime-preserved-2026-08-19/`.
- The journal's per-tick `alive` field undercounts a day's deaths (measured
  −63 at day 240): it is read at `health_tick`, before three later killers.
  Take mortality from snapshots or per-cause counters.

## What this run demonstrated about the method

Item 9 — the restore rehearsal — caught a production-critical defect that
935 green unit tests missed, *because it loaded the real artifact and asserted
wholeness rather than trusting the save path's own reporting*. And items 3/6
were proven in the failing direction before their greens were accepted. The
acceptance criteria did exactly what they were designed to do:

> A test that cannot demonstrate failure is not yet evidence.
