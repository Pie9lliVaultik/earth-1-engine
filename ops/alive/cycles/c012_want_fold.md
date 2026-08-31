# CYCLE c012 — WANT→RR fold: starvation/dehydration deaths folded into the GM baseline as relative risk
_Retroactive report owed under BIBLE.md v4.2 §4.2.3 (XI.A.2). Drafted 2026-08-31 from on-disk
evidence only; run artifacts for c012 itself are NOT on disk (see ABLATION/RETEST)._

## RESULT
| field | value |
|---|---|
| gate(s) exercised | ageAtDeath, CDR (mortality structure); all other gates re-run per XI.A |
| number(s) | ageAtDeath before 64.6 (c011.json), pooled 64.1±2.8 (CALIBRATION_CYCLES.md c011 row) → after TODO-VERIFY; CDR before 0.0062✗ (c011.json) → after TODO-VERIFY |
| target | ageAtDeath on-pyramid reference 69.0, band [66.2, 71.8] (gompertz_world.v1.json `age_at_death_reference_own_pyramid`); CDR band [0.007, 0.015] (c011.json) |
| gap | TODO-VERIFY (prior gap 4.9yr, CALIBRATION_CYCLES.md c011 row) |
| agents / seeds | 20000 × 180d; seeds TODO-VERIFY (protocol: 4242 primary + 5151/6363/7777 replicates) |
| flag set | c011 set (MODE=gradient; CALIBRATION=v1; FLAG=c2plus_v1; TABLES=c2plus_tables_v2.json; MODE=gompertz; SHARE=0.49) + EARTH1_WANT_MODE=rr + EARTH1_WANT_RR=5.0; substrate c2plus_v1 |
| hashes | t:256fe63229 · a:39d484d65f · i:89be94309c (config hashes, unchanged from c011.json); run-tree hash TODO-VERIFY |
| host / commit / wall-clock | TODO-VERIFY (no runner stamp on disk for c012) |

## INSTRUMENT
Ground truth: fetched World Bank aggregates (SP.DYN.LE00.IN, SP.DYN.AMRT.*, SP.DYN.CDRT.IN,
SH.DYN.MORT, SP.POP.*) behind the GM fit — data/gompertz_world.v1.json, status
"DERIVED-FROM-FETCHED-AGGREGATES". Units: ages in years (age_years = 18 + civ.age*72,
health.py:305), hazards per day (m_age/365, health.py:341). Leakage: anchors read under
calibration purpose only; WVS DEV cells untouched by this mortality change; HOLDOUT untouched.
Telemetry added for this instrument: `want_rr_mean_share` and `gm_deaths` emitted every tick
(health.py:343-344, 366), so the WANT share is observable against the fetched cause-composition
bound (comment, health.py:325-326). Canonical path: the fold lives on the unified loop behind
env flags, not in a script-level assembly (flourishing.py:180, health.py:319). Failure case this
instrument reports: if the fold double-counts (RR term ON while the separate draw still fires),
cause_of_death would still record CauseOfDeath.WANT (flourishing.py:190) and want_rr_mean_share
plus WANT-coded deaths would both be nonzero — the rr-mode block zeroes the draws precisely so
that signature is impossible (flourishing.py:184-185). Known-answer check: with hunger=thirst=0,
want_term=0 and the GM path reproduces c011 bitwise on paired CRN — TODO-VERIFY (owed rerun).

## DIAGNOSIS
Causal path: deprivation → hunger/thirst (flourishing.py:164-174) → under canonical flags, two
independent Bernoulli draws kill outside the life table at STARVATION_DEATH=1.2e-4 and
DEHYDRATION_DEATH=6.0e-4 × WANT_SCALE × need³ (flourishing.py:76, 85, 176-179). These deaths
bypass the GM baseline entirely, so they are young-skewed and uncapped: at WANT_SCALE=1.0 the
channel killed 24% of the world (flourishing.py:77-78; CALIBRATION_CYCLES.md c010 rows) vs real
nutrition/famine mortality <1-2% (flourishing.py:78). c010's scale 0.10 cut the share 24%→3.9%
but kept the wrong structure: a parallel hazard that the SMR normalization (health.py:335-340)
cannot see, which is part of the residual 4.9yr ageAtDeath gap named in c011 ("within-band RR
gradients; roads/decline", CALIBRATION_CYCLES.md c011 row). Attribution class: (c) parameter on
top of a structural mis-placement — the channel existed but in the wrong term; sensitivity of the
gap to WANT_SCALE (c010: 24%→3.9% of deaths moved ageAtDeath 66.3→71.1, CALIBRATION_CYCLES.md
c009/c010 rows) proves the channel moves the age gate, so folding it under the life table is the
correct placement, not deletion.

## RESEARCH
Two established approaches were considered for representing want-driven excess mortality:
1. **Relative risk multiplied onto a baseline hazard** (proportional-hazards form — Cox, 1972;
   standard exposure→RR treatment in Rothman, Greenland & Lash, *Modern Epidemiology*). The
   exposure scales the baseline hazard; the life table keeps ownership of level and age shape.
2. **Competing-risks decomposition** (Prentice et al., 1978): starvation/dehydration as a
   separate cause-specific hazard competing with the background hazard.
Selected: (1), as a multiplicative RR term inside the already-normalized GM×RR machinery
(health.py:294-303), because c008-c011 established that the aggregate rate and age curve must be
inherited from the fetched life table by construction ("hardship decides WHO, not HOW MANY",
health.py:299-300); a competing separate hazard is exactly the structure that produced the 24%
catastrophe (it bypasses normalization), and a full cause-specific decomposition is unidentifiable
while the nutrition-death point anchor is BLOCKED_ON_DATA (health.py:322-324). The famine
literature bound — nutrition-deficiency deaths <1-2% of global deaths — is retained as the
reported-against composition bound (flourishing.py:78, health.py:325-326).

## IMPLEMENTATION
Smallest defensible change, two flagged blocks, default OFF (canonical behavior unchanged):
- flourishing.py:180-185 — under EARTH1_WANT_MODE=rr, the standalone starvation/dehydration
  draws are zeroed (`starving[:] = False; parched[:] = False`); the flourishing-side draw is
  disabled rather than removed so canonical stays bit-identical.
- health.py:319-334 — under the same flag, `want_term = k_want*(hunger³ + thirst³)` multiplies
  the RR before SMR normalization (`rr = rr * (1.0 + want_term)`, health.py:331), so WANT deaths
  pass through the age-stratified normalization (health.py:335-340) like every other risk factor.
Constants: EARTH1_WANT_RR=5.0 (health.py:327) — **FITTED** via the fetched age-structure anchor
(data/gompertz_world.v1.json; anchors hash a:39d484d65f); fit-run artifact TODO-VERIFY (not on
disk). The nutrition-share **point** anchor remains BLOCKED_ON_DATA (WHO GHO/FAOSTAT unreachable,
health.py:322-324; gompertz_world.v1.json `status`). hunger³/thirst³ exponents inherited from the
canonical draw (flourishing.py:176-178), class ASSUMED (unchanged). Smallest because it moves an
existing hazard between terms and introduces exactly one constant.

## ABLATION
No paired ON/OFF run for c012 exists on disk — data/cycles/ contains c001–c011 plus frozen/noise
files only, and grep for "c012" over ops/alive/ and data/ returns nothing. Per hard rule (3), no
ablation numbers are claimed. **Owed: one paired CRN rerun** — 20k × 180d, seed 4242, c011 flag
set, EARTH1_WANT_MODE=rr + EARTH1_WANT_RR=5.0 (ON) vs EARTH1_WANT_MODE unset with
EARTH1_WANT_SCALE=0.10 (OFF, the c010 shipped configuration), written to data/cycles/c012.json
and data/cycles/c012_off.json, plus WANT_RR sensitivity at {2.5, 5, 10}. Until then, attribution
of any ageAtDeath/CDR movement to this change alone is unmeasured. Regression guard (>2σ on any
other gate, σ from data/cycles/noise_floor.json: σ(MAE)=0.155, σ$0.06, σ0.7pt, σ.002, σ3.2)
applies to that rerun.

## RETEST
After-numbers TODO-VERIFY (no c012 row in CALIBRATION_CYCLES.md; no data/cycles/c012*.json).
Before-state on the same frozen cells/anchors/seeds, from c011.json (seed 4242, 20k×180d):
ageAtDeath 64.6✗ (band [66.2,71.8] own-pyramid) · CDR 0.0062✗ · median $9.21✓ · $8.30 49.4%✓ ·
65+ 14.2%✓ · casc× 0.508✓ · cohortMAE 12.335 vs floor 12.936✓. The owed rerun above doubles as
the retest; every gate re-listed before/after there. 200k rung only if 20k moves ≥0.3pp in the
right direction.

## STATUS
**ITERATING** — implementation is on disk and flagged OFF-by-default, but the cycle's run
evidence is not; gate cannot be judged. Next action (one line): execute the paired CRN rerun
named in ABLATION and append the c012 row to CALIBRATION_CYCLES.md before any PASS claim.
