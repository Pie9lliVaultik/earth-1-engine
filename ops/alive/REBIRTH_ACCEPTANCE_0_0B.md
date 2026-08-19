# 0.0b PRODUCTION ACCEPTANCE — virgin-slot rebirth

**2026-08-19 · VERDICT: ACCEPTED · 1,266 real rebirths inspected, zero violations**

Window: day 333 (pre-deploy snapshot, verified off-box) → day 343
(post-deploy snapshot the daemon then resumed from). Deployed commit
`ce396b5`, clean provenance, no new continuity boundary.

## Real newborns, not test cases

Every slot the production daemon actually recycled in the window was
identified (dead→alive, or age dropped) and checked on prime through
the canonical loader. **20/20 invariants, zero violations across all
1,266:**

| invariant family | result |
|---|---|
| no prohibited previous-occupant state (decline, falls, street years, crimes, lifetime travel, illness history, works) | ✅ 0 violations |
| age exactly = days since own birth (0.0a quanta) | ✅ |
| only declared inheritance present; conviction and tenure within per-agent birth bounds (k·gain, k days) | ✅ |
| initialization valid under canonical birth distributions (traits, physical, mental, forces) | ✅ |
| ties household-only; created via the canonical fabric machinery (mutual) | ✅ 200 sampled |
| zero reverse references to the dead identity in any typed matrix | ✅ |
| no self-loops, duplicates, or ties created to corpses | ✅ |
| memory scopes: 295/1,266 newborns reached by pre-existing memories — via spread after birth (plausible at rate 0.06·exposure·day), not inheritance (inheritance = all at once) | ✅ observation |

**Restart continuity:** the daemon resumed *from the same artifact the
newborns were verified in* — `commit ce396b5 · day 343 · rng_continued
True · checksum verified · dirty False`, boundary count unchanged (2),
now ticking at day 348. The reborn states and graph demonstrably
survive persistence, because the persisted bytes are what passed the
inspection.

## Instrument corrections during the run (recorded per XI.A)

First pass reported 2 FAILs; both were **verification-script unit
errors**, fixed and re-run — the model was never wrong:

- `tenure` is in **days** (`life.py:175`); the check compared years and
  flagged 48 legitimately-hired newborns.
- `alpha` moves up to `CONVICTION_GAIN = 0.06`/day; a fixed ±0.35 band
  wrongly flagged 270 early-window newborns. Correct bound is
  per-agent: `|α−0.35| ≤ k·0.06` for k days of life.

## Demographic baseline, day 333→343 (PRESERVED for Benchmark D — not calibrated)

| quantity | value |
|---|---|
| slot reuses (births) | **1,266** (≈127/day) |
| gross deaths (snapshot accounting: \|Δalive\|+births) | **2,961** (≈296/day) |
| net population change | **−1,695** (3,955,071 → 3,953,376) |
| journal `deaths` key in window | 849 — **counts disease deaths only** (health_tick); war/weather/want/road land in separate keys. Use snapshot accounting for totals |

Net decline ≈170/day is consistent with the Epoch-0 rate (days 240→284:
≈170/day), so no demographic discontinuity is attributed to 0.0a/0.0b.
No calibration performed; numbers preserved as the first
post-aging-fix baseline.

## Status

**0.0b ACCEPTED.** Phase 0 chain: Epoch 1 ✅ → 0.0a ✅ → **0.0b ✅** →
0.0d next (fabric re-homing on migration/firm change).
