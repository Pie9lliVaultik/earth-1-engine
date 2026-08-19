# Earth-1 — session guidance

**Read `BIBLE.md` before doing anything else.** It is the canonical
assessment (v4, 2026-08-19): what exists, what is wired, what is
measured, the benchmark targets, and the plan. Every claim in it was
measured or cited on that date. Do not trust any earlier STATUS
document over it.

## The one-paragraph state

Earth-1 is one project with two substrates: an older opinion engine
(`engine.py` family — DEAD, but still what every benchmark and the API
import) and the living world (`earth1/alive.py::live_one_day` — what
actually runs: 4M agents on the world box, one world-day per 60s).
They are not connected. Phase 0 of BIBLE.md Part VIII connects them,
and **nothing else is meaningful until Phase 0 exits.**

## Current phase

**Phase 0 — INTEGRITY** (BIBLE.md Part VIII, eight tasks with exit
criteria). Next task: 0.1, the four correctness bugs (unseeded RNG in
`memory.spread`; shared RNG row in `health.py`; conviction decay
no-op in `influence.py`; cause-of-death code collision).

## Machines

- **world box** 167.233.77.48 (8c/30GB) — `earth1-alive.service`, the
  single writer. Do not run experiments here.
- **prime** 46.4.189.237 (96c/503GB) — ALL ensemble/research work runs
  here, never on the laptop. SSH key: `~/.ssh/earth1_hetzner`.
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

## Working style (from the founder, standing)

- Pre-register thresholds before measuring; honour them when they fire
  against us.
- Commit regenerated data immediately (sync clobbered fresh artifacts
  twice).
- Run `date` before narrating time. Push after every meaningful unit
  of work.
