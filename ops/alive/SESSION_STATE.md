# WHERE THINGS STAND — read this immediately after BIBLE.md

*Written 2026-08-19. `CLAUDE.md`'s "Current phase" section is STALE: it
still names WP-0 as the first deliverable. WP-0 is done. This file is
current; when they disagree, this one is right. Fold it into
`CLAUDE.md` when that file is next editable.*

## ▶ THE NEXT ACTION: execute the Epoch-1 deployment

**Frozen target: tag `v1-persistence-deploy-1` → `ae65bcd`.**
Do not move it. **Do not begin 0.0a until production acceptance is
green.** Later commits on `v1-unification` are docs and tests only; the
code at the tag is complete.

Follow `ops/alive/DEPLOY_RUNBOOK.md` — all twelve steps, executed by
Claude Code, never handed to the founder. **Re-run Step 0 from scratch**
in a new session; do not resume from a mutating command.

> ### HARD GATE
> Do not stop `earth1-alive.service` until the complete canonical 4M
> `data/alive/` civilization is off-box **and independently
> checksum-verified**.
>
> The shipped `/opt/earth1/run_backup.sh` protects `data/living/` — the
> old 200K world — so **this is the first real backup this
> civilization has ever had**, despite a green timer. If any
> verification fails: **stop before mutation**, diagnose, fix the
> cause. Do not proceed on an unverified copy.

The world becomes **Epoch 1** at a recorded discontinuity
(`legacy_v0_missing_presence_mobility`), because the v0 format never
wrote `presence`/`mobility` and they are rebuilt at birth values. That
boundary is an engineering artifact, not a world event: **no causal
benchmark may span it**, and no trajectory may be treated as continuous
across it.

Acceptance is only green when all of this holds:
**known code + known state + off-site memory + exact restart.**

## Phase 0 status

| task | state |
|---|---|
| **WP-0** unification audit | ✅ **DONE** — `V1_UNIFICATION_AUDIT.md`, signed off with 3 amendments (see its §A) |
| **0.0e** provenance gate *(new task; promoted ahead of 0.0a)* | ✅ built · ⏳ **not deployed** |
| **0.0c** exact persistence | ✅ built · ⏳ **not deployed** |
| **0.0a** aging | ⬜ **next, after deployment** — see scope below |
| **0.0b** virgin-slot rebirth | ⬜ `_be_born` clears no adjacency row **and** inherits ~40 fields incl. `health.declining`/`falls` (a newborn can be born mid fall-decline). Needs a central reset schema, not a longer list |
| **0.0d** fabric re-homing | ⬜ migration updates `civ.country` but not `region`/`urban`, so the locality key `country*1000+region*2+urban` becomes an invalid address |
| **0.1** four correctness bugs | ⚠️ (a) `memory.spread` global RNG — **already FIXED** in 0.0c under ruling 4 · (b) `health.py:235` `u[4]` double-use → change to the unused `u[5]` · (c) conviction decay `× 0.0` — **mark disabled/unadjudicated, keep output bit-identical, activate only via the 0.8 A/B** · (d) cause codes: war=5 collides with fall=5 |
| **0.2–0.8** | ⬜ as written. 0.5 covers **31 API route handlers across 9 files**, and `earth1/__init__.py:1` imports `engine` unconditionally — **empty that first** or nothing is retirable |

## 0.0a scope — decided, do not re-litigate

`advance_age()` maintains **`age` and `age_bucket` ONLY.**

- ❌ Do **not** re-assert `forces[:, EXPERIENCE] = age`. In the living
  world EXPERIENCE is a real dynamical channel written every day by six
  modules (`flourishing.py:243`, `mobility.py:170`, propagate, relax,
  feed, contagion). Overwriting it would erase lived history.
- ❌ Do **not** port `_AGE_GRADIENTS` trait drift
  (`generational.py:187-192`) — that is behavioural physics, not a
  correctness fix.
- ❌ Do **not** call `generational_tick` whole: it carries its own
  Gompertz mortality and rebirth that never touch `health.alive`, which
  would create two incompatible demographic authorities.
- ✅ Extract `generational.py:181-185`; insert at `alive.py:102`, after
  policy/war and **before** `life_tick`/`health_tick`, so the day's
  hazards see today's age.
- ⚠️ Known consequence to **log, not fix here**: `life.py:267` sets
  `in_lf` once at birth and never recomputes it, so unfreezing age
  creates nonagenarians permanently in the labour force. Retirement is
  new physics and belongs to a later phase.
- Invariant: 365 simulated days advances every survivor by exactly one
  year (`atol` tight), `age_bucket` stays consistent, and age-dependent
  modules then read the correct age.

## Governing doctrine

`BIBLE.md` Part XI.A — **NO DEAD-END RESULTS**. A miss is not a
deliverable; it starts
`MISS → VERIFY → DIAGNOSE → RESEARCH → IMPLEMENT → CALIBRATE → ABLATE → RETEST → PASS → FREEZE`.
**Do not stop at "the model failed." Your job starts there.**

Read `V1_UNIFICATION_AUDIT.md` §A for the binding founder rulings and
Part 7 for defects **N1–N17** before touching any Phase 0 task.

## Open founder-side items

| item | status |
|---|---|
| RunPod token rotation | ⏳ owner-only (console). Repo is clean — no key in history, `.env` gitignored, no remediation needed |
| WVS microdata registration | ⏳ gates R16; longest lead |
| FRED / ACLED keys | ⏳ |
| Destitution-bar ruling (34.5% measured vs 25% bar) | ⏳ |
| Backup restore rehearsal | ✅ tooling built + proven locally; runs for real in deployment steps 10–11 |
