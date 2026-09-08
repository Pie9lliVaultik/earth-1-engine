# PREREG — v1.1 candidate factorial: urban-axis fix × rehome-clamp fix

Registered BEFORE any evaluation run (founder rulings 1–2, 2026-09-08).
Shares its runs with ops/alive/cycles/URBAN_FIX_PREREG.md (ruling 2:
"compare four configurations"). Gates and outcome definitions are fixed
by this file; results are inspected only after all runs complete.

## Named changes under evaluation

- U: EARTH1_URBAN_AXIS_FIX=on  (popsynth boolean reads the joint axis
  correctly; flag-off = frozen inversion)
- C: EARTH1_REHOME_LOCAL_CLAMP=1 (tie-adding clamps only the added
  coordinates; flag-off = frozen whole-matrix collapse on migration days)

## Design

2×2 factorial: {baseline, U, C, U+C} × 4 CRN seeds {4242, 5151, 6363, 7777}.
200,000 agents, c2plus_v1 substrate, freeze-0.9 base flags
(scripts/env/freeze09.env), 180 days (≈25 weekly graph-adaptation
rounds and repeated migrations — ruling 2's horizon requirement).
Matched starting populations: same seed ⇒ same genesis within each
arm-pair that shares genesis (U changes genesis; C does not — so
baseline/C share genesis bitwise per seed, and U/U+C share genesis
bitwise per seed; cross-genesis comparisons are aggregate-level only).

## Registered measurements (recorded every run; snapshots at days 30,60,90,120,150,180)

MATERIAL BOARD (census-weighted): median income $/day; poverty $8.30 and
$3.00 headcounts; unemployment; CDR and mean age at death (DeathWatch);
65+ adult share; wealth concentration p99/p50 and top-1% share.

TIE / NETWORK (per relationship type: household, neighbours, colleagues,
friends, weak, media): weight percentiles p10/p50/p90/p99 and mean;
degree mean/p90; edge count; weekly-collapse signature = day-over-day
drop in weak-tie p90 on migration days.

BEHAVIOURAL: neighbour force-correlation (mean Pearson over 20,000
sampled live edges, per force channel); within-locality force variance;
migration count cumulative; cascade episode count.

URBAN OBSERVABLES (per URBAN_FIX_PREREG G-A/G-C): urban margin vs census
per country (report worst 10); disease death share (DeathWatch by-cause);
no-safe-water share; mean rent and arrears rate by settlement; belonging
mean.

## Registered gates

G1 (board holds under U+C): poverty $8.30 within 46.1±2.0pp; median
income within ±5% of $9.27; CDR in [0.007,0.015]; mean age at death in
[66.2,71.8]; poverty $3.00 no worse than the registered RED (16.8%);
unemployment no worse than the registered RED (~9.7%).
G2 (urban margins): with U on, population urban share matches census
within 2pp for ≥180 of 194 countries (JP≈0.920, US≈0.833, IN≈0.364,
NG≈0.543 spot checks).
G3 (clamp mechanism): with C on, the weekly weak-tie collapse signature
disappears (no migration-day p90 drop beyond seed noise), and weak-tie
p90 at day 180 exceeds baseline's (the drifted weights survive).
G4 (attribution): every registered observable that moves >2 seed-sigma
under U+C is attributable to U or C alone via the single-fix arms;
an interaction-only mover is reported as an interaction, not assumed.

## Ruling-2 characterization requirement (echo-chamber claim)

The Apparatus-Cycle-1 phrase "partially undoing echo-chamber formation"
is DOWNGRADED TO HYPOTHESIS until this measurement: the claim is
supported iff, under C alone vs baseline, (a) neighbour force-correlation
at day 180 is higher by >2 seed-sigma on at least two force channels AND
(b) the weak-tie weight distribution shows the preserved drift of G3.
If (b) holds but (a) does not, the honest statement is "the clamp
suppressed tie-weight drift with no measured effect on local force
convergence at 180 days," and that is what every document will say.

## Secondary registered evaluation (candidate config only)

If U+C passes G1–G2: regenerate the three sb1 feature worlds under U+C
and score WVS-heldout (98) and GOQA/Pew (468) against the same baselines
with the same scorer (scripts/scoreboard, unchanged). ACCEPT: Earth-1
MAE within +0.5pp of the freeze-0.9 values (11.84 / 12.01); any
improvement is reported but was not required. Freeze-0.9's published
numbers remain attached to freeze-0.9 and its scorer.

## Promotion rule

v1.1 candidate = U+C iff G1–G4 pass. If C fails G3/G4 attribution or
breaks G1, promote U alone and return C to the queue with its
measurements. All four arms' full measurement JSONs are committed
regardless of outcome. VOID only for instrument defects, never results.

## Provenance

Runner: scripts/cycles/run_v11_factorial.py (committed with this file).
Every run records: full EARTH1_* env, git HEAD, seeds, world day-0 v1
hash, and per-snapshot measurements. Freeze-0.9 checkpoints, boards and
published results are untouched and remain the reproducible historical
version (ruling 1).
