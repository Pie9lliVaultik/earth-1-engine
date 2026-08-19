# Earth-1 — session guidance

**Read `BIBLE.md` before doing anything else.** It is the canonical
assessment (v4.1, 2026-08-19, three-auditor reconciliation): what
exists, what is wired, what is measured, the benchmark targets, and
the plan. Every claim in it was measured or cited on that date, and
its central findings carry three independent auditors' agreement. Do
not trust any earlier STATUS document over it.

## The one-paragraph state

Earth-1 is one project with two substrates: an older opinion engine
(`engine.py` family — DEAD, but still what every benchmark and the API
import) and the living world (`earth1/alive.py::live_one_day` — what
actually runs: 4M agents on the world box, one world-day per 60s).
They are not connected. Phase 0 of BIBLE.md Part VIII connects them,
and **nothing else is meaningful until Phase 0 exits.**

## Current phase

**Phase 0 — INTEGRITY** (BIBLE.md Part VIII + the v4.1 amendments at
the top of the document; now 12 tasks with exit criteria).

**First deliverable: WP-0** — create branch `v1-unification`, no new
physics, produce `V1_UNIFICATION_AUDIT.md` (entry-point graph, state
schemas, persistence field lists, test gaps, exact files to edit) and
have it reviewed BEFORE any implementation.

Then, in order:
- 0.0a fix aging (`live_one_day` never advances `civ.age` — verified
  max|Δage|=0.0 over 30 days; invariant: 365 days = +1 year)
- 0.0b virgin-slot rebirth (reborn slots inherit the dead agent's
  adjacency row — verified; invariant: zero inherited ties)
- 0.0c complete persistence (presence, mobility, RNG, clock missing
  from `world_alive.save_world` and `timeline._save`; invariant:
  save→restore→hash round-trip + restored-branch parity)
- 0.0d fabric re-homing on migration/firm change
- 0.1 the four correctness bugs (unseeded RNG in `memory.spread`;
  shared RNG row in `health.py`; conviction decay no-op in
  `influence.py`; cause-of-death code collision)
- 0.2–0.8 as written. Note 0.5 explicitly includes the product API:
  `earth1/api/deps.py:19-35` still loads the OLD world.

Founder-gated parallel track (independent of wiring, start
immediately): WVS microdata registration (gates R16), FRED/ACLED
keys, RunPod key rotation, one backup restore rehearsal, the
destitution-bar ruling.

## Machines

- **world box** 167.233.77.48 (8c/30GB) — `earth1-alive.service`, the
  single writer. Do not run experiments here.
- **prime** 46.4.189.237 (96c/503GB) — ALL ensemble/research work runs
  here, never on the laptop. SSH key: `~/.ssh/earth1_hetzner`.
- **Storage Box** `u652120@u652120.your-storagebox.de` port 23 — SSH
  key auth from the world box. Daily backup at 09:50 Berlin via
  `earth1-backup.timer` → `/opt/earth1/run_backup.sh`. **WARNING
  (2026-08-19 rehearsal): the script currently backs up the OLD 200K
  world (`data/living/`), NOT the real 4M world (`data/alive/`).
  Fix pending — the living civilization has never been backed up.**
- Laptop = iteration only. A leftover launchd job
  (`com.earthling.earth1-daily`) must be removed (Phase 0.6).

## Standing rules (BIBLE.md Part XI — enforced, not advisory)

1. Verify every instrument on a known answer before believing a
   negative result (two identical runs must score +1.0).
2. Every control must be able to fail.
3. Small before large — binary questions never need full-scale runs.
4. A parameter read back out is not a finding.
5. Calibrate by MSM/Indirect Inference with pre-registered moments,
   never by eye.
6. One engine, one path. The instrument and the product run the same
   program.
7. No result without mechanism and citation.
8. Grep the named defect classes: GM (global mean where local
   belongs), CF (control that cannot fail), IP (input echoed as
   finding).
9. Report failures as solved problems — iterate to the working state,
   verify honestly, then report with receipts. Never present a
   negative result as the deliverable, and never cheat a positive.
   The clean form of this rule is the four-partition doctrine
   (BIBLE v4.1 §9): iterate relentlessly on train/dev; the holdout is
   scored once, after freeze, and targets never move after results.
10. Result provenance stamping: every result JSON stamps hostname,
    git commit, seed, and wall-clock at write time.
11. The ten prohibitions (BIBLE v4.1 §19 / V1-Readiness Appendix H) —
    including: no third world for a benchmark; no promoting a
    mechanism because output looks more alive/chaotic; never
    calibrate to chaos; no design document outranks current code.

## Working style (from the founder, standing)

- Pre-register thresholds before measuring; honour them when they fire
  against us.
- Commit regenerated data immediately (sync clobbered fresh artifacts
  twice).
- Run `date` before narrating time. Push after every meaningful unit
  of work.
