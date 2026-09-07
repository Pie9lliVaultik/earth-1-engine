# THE 100-MILLION RUN — scale invariance measured (2026-09-02)

> **CONFIG CORRECTION (2026-09-02, same day):** every run on this page was launched
> WITHOUT the freeze-0.9 exports and therefore used engine DEFAULTS —
> `hardship_mode=cliff`, `income_calibration=off`, `mortality_mode=legacy`,
> `distress_layoffs=off`. That is the OLD physics, not the frozen candidate.
>
> **What survives:** every comparison here was internally consistent — all scales ran
> the SAME configuration — so **scale invariance holds as measured**, and the memory
> and timing results are config-independent (array shapes and tick structure do not
> change with flags). The DeathWatch capture validation and the rare-events argument
> are also config-independent.
>
> **What does NOT survive:** any claim that "the *calibrated* anchor board survives
> scale-up." That question was never tested here, because the calibrated config was
> never loaded. The day-180 4M figures produced on this config (median $3.58,
> poverty $8.30 = 92.95%, CDR 0.0263, age-at-death 48.4) are the LEGACY equilibrium
> and are comparable to nothing on any committed board.
>
> **Fix, structural:** `scripts/env/freeze09.env` is now the single source of the flag
> set, and `earth1/configstamp.py` stamps the loaded physics into every artifact and
> hard-refuses a non-freeze-0.9 run. The equilibrated test has been relaunched on the
> correct physics; results land in `equilibrate_4M_f09.json` / `_100M_f09.json`.

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

## Mortality at scale — closed, with the correct observer (2026-09-02)
Re-measured with `earth1.deathwatch` (person_id turnover). Same 5 days, same seed:

| population | deaths captured | engine reported | capture | CDR/yr | mean age at death |
|---|---|---|---|---|---|
| 200,000 | 4 | 4 | **100%** | 0.00146 | 41.4 |
| 1,000,000 | 34 | 34 | **100%** | 0.00248 | 53.5 |
| 4,000,000 | 131 | 131 | **100%** | 0.00239 | 51.3 |

Capture is exact at every scale. CDR agrees between 1M and 4M within 4% (n=34 vs
n=131); the 200k row rests on **four deaths** and is pure Poisson noise — which is
itself the point below. Day-5 mean age at death (~51) sits below the equilibrated
69.0 for the same reason the poverty numbers do: the world has not settled. Nothing
here is scale-dependent.

## WHAT SCALE ACTUALLY BUYS: rare events, measured fast
The freeze board's mortality census needed **200k × 180 days = 36M agent-days** to
collect **717 deaths**. A 100M world collects roughly **10,000 deaths in 5 days**
(500M agent-days) — **14× the sample in 1/36th of the world-time.**

This is the concrete product argument for population, and it generalises past
mortality: the Vaultik model scenario selected **71 agents** from a 20k world, which
is a shrug; the same predicate at 100M selects ~355,000, which is a measurement.
Scale substitutes for world-time on anything rare — deaths, cascades, tail events,
narrow commercial segments. That, not the headline number, is why 8.3B is worth
building.

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

---

# THE ANSWER: the calibrated board holds at 20× (freeze-0.9, 2026-09-02)

Re-run on the correct physics (`configstamp` verified `gradient / v1 / gompertz /
on`), 4,000,000 agents, 180 days, DeathWatch throughout.

| day | median $/day | poverty $8.30 | poverty $3.00 | CDR/yr | mean age at death |
|---|---|---|---|---|---|
| 5 | 8.61 | 0.4874 | 0.1864 | 0.00772 | 68.40 |
| 15 | 8.63 | 0.4867 | 0.1858 | 0.00764 | 68.09 |
| 30 | 8.66 | 0.4856 | 0.1849 | 0.00745 | 67.78 |
| 60 | 8.72 | 0.4830 | 0.1828 | 0.00735 | 67.96 |
| 90 | 8.96 | 0.4739 | 0.1766 | 0.00729 | 68.21 |
| 120 | 9.30 | 0.4610 | 0.1681 | 0.00729 | 68.18 |
| **180** | **9.52** | **0.4529** | **0.1630** | **0.00738** | **68.29** |
| 200k board @180d | 9.605 | 0.4588 | 0.1680 | 0.00727 | 68.99 |
| REAL (fetched) | 9.27 | 0.461 | 0.104 | 0.0076 | band 66.2–71.8 |

**Verdict: the freeze-0.9 anchor board survives a 20× scale-up.** Median within 0.9%
of the 200k board, poverty $8.30 within 0.59pp, poverty $3.00 within 0.50pp, CDR
within 1.5%, mean age at death within 0.70yr and inside its derived band. Against the
real fetched anchors the 4M world sits 0.81pp low on the poverty line and 2.7% high on
median income — it reproduces the board, it does not merely agree with itself.
Mortality is measured here with the correct observer, so 68.29 is a real number.

## A correction to our own earlier reasoning
The wild day-5 census on the legacy runs (median $3.23, poverty 94.6%) was attributed
to *equilibration*. That was wrong, and this table shows why: under freeze-0.9 the
day-5 census is ALREADY near-calibrated (median 8.61, poverty 48.7%) and drifts
gently toward the anchor over 180 days. The catastrophic day-5 numbers were the
WRONG PHYSICS, not a cold start. The scale-invariance finding is unaffected — every
scale ran the same configuration, so the invariance comparison was valid — but the
mechanism we named for the deviation was not.

## Still open
500× confirmation: the 100M freeze-0.9 run is in flight (born in 741s, physics
stamped correct in its artifact), reporting at the same checkpoints.
