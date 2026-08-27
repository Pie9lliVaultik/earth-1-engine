# C2PLUS SUBSTRATE v1 — CHANGE IMPACT (classified BEFORE any run)
2026-08-27. Change: genesis(substrate="c2plus_v1") draws each agent's
(sex, age, education, income, urban) jointly from per-country IPF
tables (data/c2plus_tables_v1.json) instead of the incumbent
independent-ish draws; adds civ.sex. Dynamic laws untouched — the diff
is confined to genesis Layer 1 demographics; every downstream layer
(traits, forces, fabric, life) consumes the same variables through
unchanged code.

Class: **2 — subsystem physics change** (population substrate).
Required per policy: rerun of the affected subsystem's validation and
downstream consumers; unrelated subsystems inherit.

Registered battery (all TRAIN/DEV; no canonical promotion):
1. KA byte-identity of the DEFAULT path (already green:
   tests/test_popsynth.py, trajectory hash equal) — proves the change
   is inert unless invoked.
2. Dynamics-law identity: the candidate uses live_one_day unchanged;
   proof = code diff confined to genesis/popsynth + KA1. No dynamics
   rerun owed beyond the paired regression below.
3. STAGE-A PAIRED HEALTH REGRESSION (this run): incumbent vs candidate
   worlds, SAME seed and rng stream, 200k × 90 d; report paired daily
   trajectories of alive, deaths (by class), employment, deprivation,
   destitute share, cascades, force means/sds. No new thresholds:
   deltas reported against the incumbent's own trajectory; divergence
   beyond CRN-noise scale is flagged for ruling, not auto-failed.
4. A-v2 DEVELOPMENT scoring on the candidate substrate (structure
   target) — queued after today's compute frees.
INHERIT: all non-population subsystem validations (mechanism untouched
— dynamics code byte-identical; only x0 composition changes).

## STAGE-A RESULT (2026-08-27, paired 200k×90d, seed 4242)
Unchanged: alive −0.1%, employment +0.2%, disease deaths −0.6%, firms
+2.5%, force_sd max |Δ| 0.015. DIVERGENT (flagged for ruling, not
auto-failed): deprivation +17.6%, destitution +17.9%, wealth −36%,
starvation deaths +31.9% (⇒ total deaths +15.1%), cascades +69%,
force_mean max |Δ| 0.090. Competing diagnoses recorded: (a) honest
joints expose the known informal-floor/hardship-gain response defects
harder; (b) WVS income-frame mismatch over-poors the world (131
tier-fallback countries suspect). Discriminating tests queued:
country-level decomposition (surveyed vs fallback) + A-v2 development
scoring — the substrate's canonical judge per Bible v4.1 re-entry.
