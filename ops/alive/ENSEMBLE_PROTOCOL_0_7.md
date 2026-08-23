# FROZEN — the 0.7 paired-ensemble workload

Committed BEFORE any timing measurement, per the 0.7 contract: "the
benchmark must not quietly become easier after measurements begin."
The Bible (Phase 0 table, row 0.7) fixes only the shape and the bar —
"a paired 20-repeat ensemble completes < 30 min" — so scenario,
horizon, and scale are defined here, once, and bound.

## The workload

**Baseline world.** The production backup
`2026-08-20T074529Z-day1142` (world.pkl sha256
`379212b25f5735202aa3e9dd7f18fcf397451756df6c60d388471e41eb7cef2c`),
day 1142, 4,000,000 agents, 3,797,604 alive, schema v1 — restored on
prime through the canonical loader (`persistence.load_world`), complete
persisted state, RNG present. Full scale: no reduced populations, no
subsampled graphs. A benchmark on a smaller world is a benchmark of a
different universe.

**Pairs.** i = 1…20, each pair = (control_i, scenario_i), 40 members
total. Common random numbers: both members of pair i evolve under
`np.random.default_rng(700000 + i)`. Nothing else differs within a
pair except the intervention.

**Scenario.** At branch time (before the first tick), scenario members
receive one fixed initial-condition perturbation:
`forces[alive & country == TARGET, Force.FEAR] += 0.20`, clipped to
[0, 1], where TARGET is the most populous country of the frozen
baseline snapshot (deterministic given the snapshot; the runner
records its name and index). This uses only existing state and the
existing physics — 0.7 licenses no new mechanisms — and is the same
paired-perturbation shape the 0.8 chaos re-measurements need.
Control members receive no perturbation.

**Horizon.** 30 world-days per member, advanced by `live_one_day`
with `CANONICAL_DAY` — the one loop, the one configuration. 1,200
full-world-days per job.

**Recorded per member.** seed, kind, end-of-run `world_hash` (the
equivalence anchor for any later optimization: same state + same seeds
⇒ same hash), alive_end, cumulative deaths, employment rate, mean FEAR
in TARGET, wall seconds, per-day seconds, peak RSS.

**Recorded per job.** Reproducibility manifest (`earth1.manifest`):
git SHA, snapshot identity, schema, CANONICAL_DAY config hash, seeds,
machine spec, worker/thread counts, start/end wall time, artifact
paths. Total wall-clock is door-to-door — snapshot load, worker
startup, orchestration, result collection all included. Summed CPU
time is a diagnostic, never the headline.

## The bar

Total wall-clock for the complete 20-pair job **< 30 minutes on
prime**, canonical loop, canonical configuration, complete state,
this workload. A miss is profiled by subsystem and attacked with
established optimizations under the equivalence rule (same state +
same seeds + same inputs ⇒ same scientifically relevant outputs, or a
documented, proven-harmless tolerance). Physics simplification to win
the benchmark is forbidden.

## Free parameters (explicitly NOT frozen)

Worker count and threads-per-worker — the saturation study's job is to
find their optimum. Everything the physics sees is frozen above.
Saturation-study subsets may run fewer pairs or shorter horizons for
scaling curves, but the exit-criterion measurement is the full frozen
workload, and only that measurement can satisfy the bar.
