# 0.0d PRODUCTION ACCEPTANCE — fabric re-homing

**2026-08-19 · VERDICT: ACCEPTED · 339 real migrations + 34,126 real
employment transitions inspected, zero violations**

Deployed `f37e172`, then `7cc7a73` after the first real-event window
caught a wiring miss. Verification window: day 381 → 391 (post-fix),
on prime through the canonical loader. Restart continuity green:
`7cc7a73 · day 391 · rng_continued True · dirty False`, boundary count
unchanged (2), ticking at day 394. Tick budget intact (median 60.0 s).

## Real events, real invariants

| check | events | violations |
|---|---:|---:|
| region adopted from destination | 339 migrations | **0** |
| locality key valid at destination | 339 | **0** |
| no stale old-locality neighbour ties | 339 | **0** |
| no reverse refs in the old community | 339 | **0** |
| kinship (household+friends) became diaspora | 339 | **0** |
| unemployment holds no phantom workplace | 16,068 lost-and-idle | **0** |
| colleague ties at the actual firm | 600 sampled of 18,058 | **0** |
| colleague ties mutually consistent | 600 sampled | **0** |

All five required failing controls were proven by sabotage in CI before
deployment (preserved neighbour tie, stale colleague matrix, invalid
locality key, omitted policy category, one-sided edge — each detected).

## The production miss, worked through XI.A

First window (day 362→372): **180 phantom workplaces — 179 were
exactly the employed migrants.** `class_tick` ends a migrant's job
AFTER `life_tick` builds its lost set, so the `VIA_EMPLOYMENT` policy
was declared but never wired for migration-driven job loss. Fixed in
`7cc7a73` (migrants merged into the employment severing, same tick),
with a full-live-path regression test.

## Disclosure: the 208,469-tie remediation at day 372

Remediating "the 180" surfaced the true backlog: **208,469 unemployed
agents held colleague ties** — the entire accumulated legacy of the
original defect (colleague ties frozen at day-0 for the world's whole
history; every pre-0.0d job loss left its ties in place). All severed
in a supervised, journaled state edit (`state_remediation`, day 372,
RNG stream preserved), then adj recomposed.

**Consequences, stated plainly:**
- Day 372 is a **fabric-density discontinuity** (~208k agents lost
  their stale workplace edges at once). It is an engineering
  remediation, not organic tie decay — the journal record says so, and
  no social-dynamics analysis may read across day 372 as if the fabric
  evolved continuously.
- This is now the third recorded state boundary (day 284 epoch
  migration; day 372 fabric remediation), all journaled and
  machine-findable.

## Demographic/fabric window notes (preserved, not calibrated)

Day 381→391: 339 migrations (≈34/day), 16,068 job losses standing,
17,477 hires, 581 direct firm switches. Alive 3,947,206 → 3,945,756.

## Status

**0.0d ACCEPTED.** Epoch 1 ✅ → 0.0a ✅ → 0.0b ✅ → **0.0d ✅** → 0.1
next: (a) `u[4]`→`u[5]` in health; (b) conviction decay stays OFF until
the 0.8 A/B; (c) `CauseOfDeath` enum (war=5 vs fall=5); (d) the
journal `deaths` key = disease-only — end-of-tick mortality contract.
