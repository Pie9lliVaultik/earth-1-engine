# 0.1 PRODUCTION ACCEPTANCE — the correctness ledger

**2026-08-19 · VERDICT: ACCEPTED · 12 observed days, accounting exact
on every one**

Deployed `7055597` (four independently attributable commits:
`1381803` 0.1a · `5f97cdc` 0.1b · `92950c5` 0.1c · `7055597` 0.1d),
then `8a269f5` (journal whitelist carrying the full accounting — caught
while writing the acceptance verifier, before the window burned).

## The accounting, closed

For every observed day 529–540:

    alive_end = alive_start − deaths_total + births_total   ✓ EXACT
    deaths_total = Σ (disease + war + weather + want + road) ✓ EXACT

Snapshot↔journal agreement on the save day: **3,921,896 == 3,921,896,
exact.** The previously measured −63/day journal undercount is gone.

## Cause codes, in production

2,940 new deaths in the day 523→540 window, all codes valid and
collision-free:

| cause | code | deaths |
|---|---:|---:|
| want (starvation/thirst) | 7 | 1,751 |
| fall | 5 | 450 |
| cvd | 2 | 303 |
| weather | 6 | 204 |
| infection | 3 | 106 |
| cancer | 1 | 76 |
| injury | 4 | 36 |
| road | 8 | 13 |
| **war** | **9** | **1** — the new code, live, no collision with fall |

Legacy rule enforced in code: a persisted 5 from pre-fix state is
`legacy_war_or_fall`; strict readers refuse it; history is never
relabeled.

## Also green

- restart continuity: `8a269f5 · day 540 · rng_continued True · dirty
  False`; boundary/remediation records unchanged at 3
- 0.1b bit-identity: production conviction output identical to
  pre-0.1; decay remains DISABLED, adjudication reserved for the 0.8
  A/B (the experimental arm exists and is proven non-no-op)
- 0.1a physical consequence verified in CI: with independent draws,
  treatment among fallers ≈ access (55%), not 100% — untreated falls
  now occur, as the health model intended
- all failing controls demonstrated (restore u[4] → CI fails; enable
  decay → detectably different; duplicate codes → fails; strict reader
  on legacy 5 → refuses; omit a killer → identity breaks; late-tick
  road deaths → counted same tick)

## Status

**0.1 ACCEPTED.** Epoch 1 ✅ → 0.0a ✅ → 0.0b ✅ → 0.0d ✅ → **0.1 ✅**
→ 0.2 one-world-loop begins now.
