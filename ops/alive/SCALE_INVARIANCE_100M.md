# THE 100-MILLION RUN — scale invariance measured (2026-09-02)

## The record
**100,000,000 Earthlings** born and lived — 25× the living world, and the largest
Earth-1 population ever run. Birth 756.7s · 924.8s per world-day · peak RSS 324.5 GB
on one AMD EPYC 9454P. The extrapolation from the scaling ladder predicted 311 GB and
14.4 min/day; measured 324.5 GB and 15.4 min/day.

## Scaling ladder (empirical, 1M → 64M)
| population | birth | tick | state | B/agent | peak RSS |
|---|---|---|---|---|---|
| 1M | 6.1s | 6.2s | 1.0 GB | 975.2 | 3.0 GB |
| 4M | 24.5s | 27.7s | 3.9 GB | 978.7 | 13.0 GB |
| 16M | 107.8s | 122.0s | 15.7 GB | 980.4 | 50.0 GB |
| 64M | 457.7s | 538.6s | 62.8 GB | 981.6 | 199.3 GB |
| **100M** | **756.7s** | **924.8s** | ~98 GB | ~980 | **324.5 GB** |

Bytes per agent is flat to 0.7% across a 100× range. Tick scales as n^1.07.
Birth needs a consistent ~3.2× the final state as working memory — the binding
constraint on a single box.

## THE FINDING: the census is scale-invariant
The record run's day-5 census looked catastrophic against the 200k freeze board
(median $3.23 vs $9.61; poverty $8.30 94.6% vs 45.9%). Two candidate causes: a real
scale defect, or equilibration — the freeze board was measured at 180 days, this at 5.
The control run settles it. Identical 5-day census at four scales:

| population | median $/day | poverty $8.30 | poverty $3.00 |
|---|---|---|---|
| 200,000 | 3.30 | 0.9456 | 0.4438 |
| 1,000,000 | 3.24 | 0.9460 | 0.4466 |
| 4,000,000 | 3.23 | 0.9464 | 0.4470 |
| 100,000,000 | 3.23 | 0.9463 | 0.4467 |

**Across a 500× population range the poverty line varies by 0.08pp and the median by
$0.07.** The day-5 numbers are an equilibration state, identical at every scale; they
are not a scale defect. The anchor board's dependence is on TIME, not on N.

**Why this matters beyond the record:** it retroactively validates the whole
calibration ladder. Tuning at 20k and confirming at 200k is legitimate precisely
because the physics is scale-free — the 200k → 100M step introduces no drift at all.
A calibration that held only at its own sampling frame would have shown here.

## What this run does NOT establish (named, not buried)
- **Mortality at scale is unmeasured — the two mortality lines above are VOID.**
  The runner counted deaths with a naive `prev & ~alive` mask, which this campaign
  already documented as missing ~95% of deaths through same-tick rebirth.
  `mean_age_at_death: 0` and `cdr_yr: 0.00185` are a broken counter, not results,
  and must not be read as findings. **Measured cost of that defect (2026-09-02,
  200k x 20d): engine reported 80 deaths; the naive mask captured 10 (12%); the
  correct observer captured 80 (100%).** Fix is now permanent and not merely
  remembered: `earth1/deathwatch.py` is the single correct observer (person_id
  turnover + pre-tick ages), shipped with a Standing-Rule-2 test that passes only
  if the naive method is measurably broken and DeathWatch is not. The poverty and
  income results are untouched by this — they never consult the death counter, and
  they were confirmed independently at three other scales.
- **Equilibrated agreement at 100M is unmeasured.** Confirming the full green board
  at scale requires 180 days at 100M ≈ 46 hours of ticking. Cheap to schedule, not
  yet run.

## The 8.3B arithmetic, now grounded in measurement
- 981 B/agent × 8.3e9 = **8.1 TB** today.
- Levers: float64→float32 across state and graph weights (~2×); graph quantization or
  implicit regeneration (34% of the footprint, 27.3 edges/agent stored as float64);
  int8 packing of bounded [0,1] quantities. Stacked: **~120 B/agent ≈ 1 TB** — one
  commodity machine.
- Clock: n^1.07 puts 8.3B at ~16 h/world-day on today's implementation. But 27.7s
  against 3.9 GB of state is ~2,000 passes over memory — the tick runs at a small
  fraction of this box's bandwidth, so the ceiling is implementation (Python
  temporaries, the sparse matmul), not silicon. A 10–20× compute win is very likely
  available before any hardware changes hands.
- Open ruling: may the precision pass move the anchor board at all, or must it hold
  every green gate exactly?
