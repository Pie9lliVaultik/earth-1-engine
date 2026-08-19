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

## EARTH-1 V1 — NO DEAD-END RESULTS

> **Do not stop at "the model failed." Your job starts there.**

A benchmark miss is not an acceptable final deliverable. It is a
diagnostic result that starts the next engineering/research cycle.

When any experiment, calibration, benchmark, scenario backtest,
prediction task, module validation, or acceptance gate misses its
predefined target:

1. **Record the result exactly.** Never hide, soften, delete, or
   rewrite a bad result.
2. **Verify the instrument first.** Check ground truth, provenance,
   units, leakage, implementation correctness, persistence, state
   continuity, metric visibility, benchmark design, and whether the
   tested code is actually the production/canonical path.
3. **Explain causally why the result occurred.** Trace the output back
   through the code and quantify which mechanisms, parameters,
   datasets, or missing channels account for the error.
4. **Research before inventing.** Search peer-reviewed academic
   literature, authoritative technical reports, established
   simulators, government models, white papers, reference
   implementations, and relevant empirical datasets for methods that
   address the diagnosed problem.
5. **Do not make assumptions where established research exists.** Cite
   the methods considered and explain why the selected approach
   applies to Earth-1.
6. **Implement the smallest defensible correction or improvement.**
   Bugs are fixed. Missing empirically justified mechanisms are added.
   Poor parameterizations are calibrated. Weak algorithms are replaced
   with stronger established methods when evidence supports doing so.
7. **Run controlled ablations and sensitivity analysis** so we know
   what actually caused the improvement.
8. **Retest on TRAIN/DEV and iterate** until the predefined
   development gate is met.
9. **Never tune on the final holdout.** Never alter the acceptance
   threshold after seeing holdout results. Never manufacture a pass.
10. **Only freeze a capability** after it passes an untouched external
    holdout or prospective test appropriate to that capability.

The required workflow is:

```
MISS → VERIFY → DIAGNOSE → RESEARCH → IMPLEMENT
     → CALIBRATE → ABLATE → RETEST → PASS → FREEZE
```

A document saying "FAIL" is never the end of the task. It is evidence
preserved in the research record and the beginning of the next
iteration.

**Claude Code must not respond to a bad result with only an
explanation of why it failed.** It must return:

> result → quantified diagnosis → relevant research → proposed
> solution → implementation → new experiment → comparison with
> previous result.

The only legitimate terminal exception is when repeated clean
experiments, correct implementation, strong literature-derived
approaches, appropriate calibration, and untouched external evidence
demonstrate that the underlying hypothesis itself is false. In that
case, preserve the negative evidence and redesign the capability
rather than falsifying success.

Earth-1's goal is not to document avoidable failure. The goal is to
engineer every capability in our wheelhouse until it works, while
preserving a scientifically honest record of every attempt.

*This doctrine is carried verbatim in three places so it cannot
quietly disappear: here (execution rule), `BIBLE.md` Part XI.A
(scientific operating doctrine), and every benchmark plan
(miss-resolution protocol). If the copies ever disagree, BIBLE.md is
canonical.*

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
