# PREREG — social-emergence experiment: does the graph earn its keep?

Registered BEFORE any run (founder ruling 4, 2026-09-08). The central
scientific objective: establish whether social interactions improve the
model's account of observed societal change, beyond what material
conditions and population composition explain alone. Outcome
definitions, readout, and scoring are fixed by this file.

## Estate declaration

This is a DEV-estate MECHANISM experiment. The judge (real protest
events following 2010-12-16, GDELT-derived, country-normalized) was
fetched and opened for the scored historical battery
(ops/alive/historical/arab_spring_scored.json) and is public data. No
sealed estate is touched; no fresh confirmatory claim is made on a
sealed judge. A confirmatory replication on an unspent event is named
below as follow-up.

## Arms (3 graph configurations × shock/no-shock × 4 seeds = 24 runs)

Graph configurations, identical genesis otherwise (200k, c2plus_v1,
freeze-0.9 base flags; seeds {4242, 5151, 6363, 7777}):
- INTACT: the engine's homophilous genesis graph, untouched.
- NO-TRANSMISSION: EARTH1_SOCIAL_TRANSMISSION=off — dyadic force
  transmission zeroed at the application site; encounters, RNG stream,
  agreement evidence, conviction and plasticity inputs identical by
  construction. This is the material-conditions + composition model.
- REWIRED: degree-preserving random rewire of the genesis graph
  (scripts/emergence/rewire_graph.py; per-type degree sequences and
  weight multisets preserved; household exempted if co-residence
  semantics require — the utility's docstring is normative), rewire
  seed = world seed. Tests whether WHO is connected matters beyond how
  much connection exists.

Shock condition = historical birth at T=2010-12-16 warmed on the real
archive news window (the machinery of the scored battery row).
No-shock control = identical genesis and configuration, cold (no news
warm), same seeds, same 90-day horizon. The shock response of a
configuration is the warm−cold difference of its fields.

Horizon: 90 days (the scored battery's window; judge overlap 185
countries).

## Registered outcomes and scoring

PRIMARY (H1, transmission): mean over seeds of Spearman
rho(Δhunger_by_country, judged protest events), where Δ = warm−cold
country mean at day 90, events normalized by country total volume
(forward-only rule of the battery). H1 holds iff
rho(INTACT) − rho(NO-TRANSMISSION) > 0 in ≥3 of 4 seeds AND the paired
mean difference exceeds its seed-level standard error.
SECONDARY (H2, structure): same statistic, INTACT vs REWIRED.
COMPARABILITY: the raw warm-field rho is also computed per arm for
comparability with the recorded +0.168 row; the Δ-based statistic is
primary because it isolates the shock response per ruling 4.
FEAR CHANNEL: same statistics on the fear field, reported (the record
says fear carried no signal; +0.069 n.s.).
NEGATIVE CONTROL (registered): census-weighted material aggregates
(poverty $8.30, unemployment, median income) at day 90 must NOT differ
between INTACT and NO-TRANSMISSION beyond 2 seed-sigma — transmission
moves beliefs, not the material board. A violation is reported as a
finding, not suppressed.
CHARACTERIZATION (no gates): neighbour force-correlation and
within-locality variance per arm; the transmission share of neighbour
correlation (INTACT vs NO-TRANSMISSION difference) — this executes the
paper's registered zero-transmission ablation.

## Interpretation rules, fixed now

- H1 pass, H2 pass: social interactions improve the account of observed
  change, and specific structure matters. Strongest claim.
- H1 pass, H2 fail: transmission matters; homophilous structure beyond
  degree does not (at this event/scale). Honest partial.
- H1 fail: the graph does not improve this account at this event; the
  paper's emergence section is REVISED to say so and the result is
  published with the same prominence as a pass.
- Power note: 4 seeds bounds detectable effects; a null is "not
  demonstrated at n=4," never "demonstrated absent."

## Follow-up named now

If H1 passes: confirmatory replication on the next unspent
protest-geography event under sealed protocol before any paper claims
"validated"; the paper may meanwhile report this DEV result as such.

## Provenance

Runner: scripts/cycles/run_emergence.py (committed with this file).
Each run records env, HEAD, seed, config, day-0 hash, day-90 country
fields, and the negative-control aggregates. Scoring script is part of
the runner and runs only after all 24 runs complete.
