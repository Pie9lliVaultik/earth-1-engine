# BENCHMARK B — PREREGISTRATION v1 (FROZEN, per-scenario)

Frozen 2026-08-26 before any run. Bible v4.1 §12 reconciled tiers;
founder GO-B. System under test: canonical Epoch-3 physics
`0.8-candidate-v4.1/posthumous-invariant-rc` at current `main` — NOT a
C2-modified population. No physics/genesis changes; no calibration
against Benchmark-B outcomes; a miss is evidence.

## Question
Does Earth-1's dynamic causal machinery (event → material consequence →
firms/jobs/health → psychology → propagation) add measurable value on
real historical perturbations, despite Benchmark A's static failure?

## Honest scope (registered up front)
The population is a synthetic present, not a historically initialised
2019/2008/2011 (the timeline was never built). Therefore all effects
are TREATMENT − PAIRED CONTROL deltas scored on direction, normalized
magnitude, and cross-event proportionality — never point levels.
Timing vs OxCGRT is NOT EXERCISED in v1 (no calendar). Geography is
claimable only if the exercised outcome clears the frozen repeat-
stability bar (the 0.8 noise-floor verdict and the recorded −0.60
same-scenario rank correlation predict refusal; the check runs anyway).
COVID excess deaths: Earth-1 v4.1 has NO epidemiological transmission
channel for a scenario (deaths arise from material-hardship mortality),
so deaths are gated on DIRECTION only; the WHO magnitude anchor is
reported as an unguarded diagnostic with that mechanism caveat.

## Events (3, across 3 domains) — registry `earth1/backtest.py`, anchors verified to named primary sources
| event | domain | scenario (frozen, unchanged from registry) | horizon | anchors (primary source) |
|---|---|---|---|---|
| covid_2020 | pandemic (health+economic) | forces {fear +0.45, econ −0.30, collective +0.25}, global, firm_damage 0.35, trade_shock 0.18, persists 900 | 365 d | jobs: **255M FTE lost 2020 (ILO Monitor 7th ed., Jan 2021: 8.8 % of global working hours)**; GDP −3.1 % 2020 (IMF WEO Apr 2021); extreme poverty +~80–97M (World Bank, Jan 2021 projection); excess deaths **14.9M 2020–21 (WHO, May 2022)** — diagnostic only (no epi channel) |
| gfc_2008 | financial | forces {fear +0.35, econ −0.40}, OECD-15, firm_damage 0.28, trade_shock 0.10, persists 500 | 540 d | unemployment +~30M 2007→09 (ILO GET Jan 2010); world GDP −1.7 % 2009 (World Bank WDI) |
| arab_spring_2011 | political contention | forces {identity +0.40, collective +0.35, fear +0.30}, MENA-10, firm_damage 0.15, trade_shock 0.06, persists 700 | 540 d | governments fell: 4 (Tunisia, Egypt, Libya, Yemen — documentary record); displacement order 1e6–1e7 over horizon (UNHCR reporting; wide tolerance registered) |
| placebo | — | zero scenario (no forces, no damage) | 365 d | all effects ≈ 0 |

## Protocol (frozen)
POP 200,000; genesis seed 42; WARM 90 canonical days, snapshot saved;
each (arm, repeat) resumes from the identical warm snapshot; paired
control with COMMON RANDOM NUMBERS (rng seed 977·13 + r, the
`branch.run` convention); repeats R = 5 (r = 0..4); arms = control-365,
control-540, covid, gfc, arab, placebo. Consequence extraction:
`earth1.consequences.snapshot/compare` unchanged; census-weight scaling
to 8.3B. Runner: `scripts/benchmark_b/run_b.py`; one process per
(arm, repeat); no physics flag anywhere.

## Gates (frozen; ACCEPT/GOOD tiers per §12)
1. **Direction** — per event over its registered observable family
   (covid: jobs↓, poverty↑, hope↓, deaths↑; gfc: jobs↓, poverty↑,
   hope↓; arab: governments-at-risk↑, displacement↑, unrest/protest↑):
   ≥75 % correct = ACCEPT, ≥85 % = GOOD, per event and pooled.
2. **Magnitude** — median normalized absolute error
   |log10(pred/recorded)| on exercised magnitude anchors (jobs for
   covid+gfc; displacement for arab) must BEAT the strongest simple
   causal baseline: **LOO-exposure baseline** = one elasticity
   k = recorded_jobs / (firm_damage × exposed_workers × horizon/365)
   fitted on the OTHER events (leave-one-event-out) then applied;
   identical formula family for displacement. Earth-1 wins the gate iff
   its median error < the baseline's median error.
3. **Proportionality/ranking** — covid > gfc > arab on attributable job
   losses (`ranking_check`), and between-scenario distance > within-
   scenario spread: gap between event means > 2× pooled repeat SD.
4. **Placebo** — every placebo effect CI (across repeats) includes 0
   AND |median placebo effect| < 5 % of the smallest treatment effect.
5. **Coverage** — leave-one-repeat-out: the nominal 80 % interval from
   4 repeats covers the held-out repeat's effect 70–90 % of the time,
   pooled over (event × outcome).
6. **Geography eligibility** — Spearman between repeat country-vectors
   ≥ 0.5 required before any geographic claim; else REFUSED (expected).
No gate, tolerance, observable, or arm changes after outputs. Misses
are reported as misses. Instrument defects ⇒ VOID + repair + rerun.

## Provenance
Every artifact stamps commit, physics_version, world hashes (warm
snapshot), seeds, scorer git path. Artifacts: `data/benchmark_b/`.
Report: BENCHMARK_B_REPORT_v1.md, then STOP (founder ruling point).

## VOID + REPAIR (2026-08-26, recorded before any repaired number was seen)
The placebo caught the jobs instrument: placebo "jobs_lost" (rectified
positive-part endpoint sum) ≈ treatment values while every other
placebo channel ≈ 0 — the statistic rectifies chaos-amplified
divergence (a zero-force scenario still writes a Memory, which draws
one RNG per day in `memory.spread`, desyncing the paired stream; FSLE
+0.22/day amplifies it), and endpoint snapshots miss transient job
losses entirely (the India probe recovery rate implies healing before
day 365). Repair, frozen now: jobs scored on the SIGNED PAIRED DAILY
PATH — covid on the year-integral `jobs_fte_year` (matching ILO's
definition), gfc on `jobs_peak_excess` (matching a stock increase
anchor), displacement/destitution/deaths stay endpoint stocks;
direction/proportionality/placebo/coverage consume the repaired
statistics. First-run endpoint results are archived as
INSTRUMENT-DEFECTIVE (scoreboard_b_defective.json). Arms rerun with
full paths persisted; scored once after the rerun.
