# CYCLE c-EXT — external-channel death audit (non-GM channels: disease, weather, war, roads)
_Retroactive XI.A.2 report under BIBLE.md v4.2 §4.2.3. Cycle IN PROGRESS —
sections below record what is done, what is owed, and by which run._

## RESULT
| field | value |
|---|---|
| gate(s) exercised | CDR, ageAtDeath (m5/m6, MOMENTS_v1.md); cause-composition (diagnostic, no prereg gate yet) |
| number(s) | GM_OTHER_SHARE fixed point: 0.49 (measured, c009) → TODO-VERIFY → TODO-VERIFY → TODO-VERIFY (iterates ran on the server; only 0.49 is on this disk). CDR 0.008 (c009) → 0.0069 pooled (c011×4) vs anchor 0.0076 |
| target | CDR anchor 0.00755/yr (m5, SP.DYN.CDRT.IN 2024); ageAtDeath on-pyramid ref 69.0, band 66.2–71.8 (c011 derivation); cause-composition target NOT YET PREREGISTERED — owed with FP4 |
| gap | CDR in band (pooled 0.0069 grazes floor); ageAtDeath 64.1±2.8, residual 4.9yr (c011); external-channel share vs real-world composition: TODO-VERIFY (per-channel shares not on disk) |
| agents / seeds | 20000 × seed 4242 (decomp_2x2.py:20-22); c009/c011 replicates ×4 (4242/5151/6363/7777) |
| flag set | MODE=gradient;CALIBRATION=v1;FLAG=c2plus_v1;TABLES=c2plus_tables_v2.json;GRADIENT=off;MODE=gompertz;SHARE=0.49 (+EARTH1_WANT_MODE=rr per c012 commit 024eb2b); substrate c2plus_v1 |
| hashes | t:256fe63229 a:39d484d65f i:89be94309c (c009/c011 rows, CALIBRATION_CYCLES.md) |
| host / commit / wall-clock | instrument fix commit e89b702; repo HEAD at report time 5dd0137; runner stamp TODO-VERIFY (FP4 will be runner-emitted per Rule 10) |

## INSTRUMENT
This cycle's first product IS an instrument finding. The decomp death capture
(`prev_alive & ~alive`) missed same-tick reborn slots: dead slots are reborn
within the same tick, so per-run capture was ~30 of ~780 deaths at 200k (~95%
missed) and every prior age-at-death figure from scripts/c2plus/decomp_2x2.py
carried ±3.5yr noise, not the claimed ±1 (decomp_2x2.py:42-48; commit e89b702).
Fix: person_id-turnover detection, ages from the PRE-tick snapshot, cause read
post-tick before rebirth rewrites it (decomp_2x2.py:49-66). Per-cause death-age
accounting added in commit 5a751ca; disease/war/weather counters exported in
commit 0a26723. Failure case this instrument reports: a death whose slot is
reborn before the post-tick scan — pre-fix it was silently dropped; post-fix
person_id turnover flags it regardless of the alive bit. Known-answer check
owed at FP4: captured deaths must equal the journal counter cum["deaths"]
(TODO-VERIFY — post-fix run output lives on the server, not this disk).
CDR reference in-instrument: 0.0076 (decomp_2x2.py:77). Ground truth: fetched
anchors per MOMENTS_v1.md (ids/vintages/sha in data/anchors_worldbank.json,
gompertz_world.v1.json). Leakage: none — audit reads engine journals only.

## DIAGNOSIS
Causal path: the GM baseline inherits the fetched life table by construction
(earth1/health.py:293-317, RR normalized to mean 1 within age strata), but the
non-GM channels ADD deaths on top with independent, uncalibrated lethalities:
disease (earth1/alive.py:557), weather (earth1/weather.py:187), war
(earth1/institutions.py:286), roads (earth1/alive.py:387). Their combined share
is removed from the GM baseline only as one scalar, GM_OTHER_SHARE
(health.py:135, health.py:341), fixed-point iterated so total CDR converges to
anchor (c009: measured 0.49; commit 79ec16a records starvation alone at 24% of
deaths = own registered miss ~30x reality, unnamed 17%). Working observation
driving this audit: post-instrument-fix per-cause accounting shows the non-GM
channels taking a death share far above the real-world external/violent-cause
share, at young mean ages (specific shares and the real-composition bound:
TODO-VERIFY — the FP iterate logs and per-cause JSONs are not on this disk).
Classification: (d) structurally missing channel discipline — no scalar
OTHER_SHARE can fix composition, because it rescales the baseline while leaving
each named channel's lethality free; c011 already showed the residual 4.9yr
ageAtDeath gap persists with CDR in band (young-age external deaths drag the
mean). Secondary: (a) instrument — now fixed (e89b702).

## RESEARCH
Two established approaches considered:
1. **Cause-of-death composition accounting** — multiple-decrement /
   cause-deleted life tables (Chiang 1968, "Introduction to Stochastic
   Processes in Biostatistics"; Preston, Heuveline & Guillot 2001,
   "Demography: Measuring and Modeling Population Processes"), with the
   cause-composition envelope from WHO Global Health Estimates methodology
   descending from the Global Burden of Disease programme (Murray & Lopez
   1996). Each named cause carries a share of all-cause mortality and an age
   profile; the all-cause table is the sum of its decrements.
2. **Single all-cause hazard with an age-independent background term** — the
   Gompertz–Makeham law (Gompertz 1825; Makeham 1860), where the Makeham
   additive constant absorbs external mortality without naming channels.
Selected: (1). Earth-1 already has named external channels with their own
mechanisms; the defensible form is to give each a SOURCED share bound from
GHE-style composition and iterate the fixed point over the named composition
vector, not one scalar. (2) rejected: a Makeham term cannot attribute deaths
to named channels, so over-lethal disease/weather/war/roads would keep
distorting age-at-death composition while total CDR looks calibrated.

## IMPLEMENTATION
Landed so far (instrument only — no physics change yet):
- person_id-turnover death capture + per-cause death-age accounting,
  scripts/c2plus/decomp_2x2.py:49-66 (commits 5a751ca, e89b702, 0a26723).
- gm_deaths counter exported from the GM branch (health.py:343-344) so the
  OTHER_SHARE fixed point can be computed from named parts (commit 024eb2b).
No new constants introduced. GM_OTHER_SHARE remains FITTED
(fixed-point-seeded) per MOMENTS_v1.md θ_MSM. The physics change (per-channel
lethality bounds under a named composition) is NOT landed — it is the FP4
step and will go behind its own flag, default OFF. This is the smallest
change: measure correctly first (Rule 2) before touching any lethality.

## ABLATION
Paired runs on disk: data/cycles/c008.json (MODE=gompertz, SHARE=off) vs
data/cycles/c009.json (SHARE=0.49), same seed 4242 and flags otherwise —
isolates the OTHER_SHARE scalar: CDR 0.016→0.008, ageAtDeath 58.9→66.3
(CALIBRATION_CYCLES.md rows c008/c009). Seed spread: c009_s5151/6363/7777.
NOT on disk: a paired pre-fix vs post-fix decomp run on identical seeds
(quantifying the ±3.5yr capture artifact), and any ON/OFF pair for external-
channel lethality. Owed: exactly one rerun — FP4, the post-instrument-fix
decomp (decomp_2x2.py, c2plus/gradient cell, pop 20000, seed 4242, 180d)
under the current flag set, emitting the named per-cause composition table
that the c008/c009 pair and the pre-fix history can be scored against.

## RETEST
Not yet run — cycle is IN PROGRESS; no physics change has landed to retest.
Current standing gate table (c011 pooled, unchanged gates, frozen anchors):
$9.22✓ · 49.3%✓ · CDR ~0.0069△ (floor graze) · ageAtDeath 64.1✗ (4.9yr
residual) · 65+ 14.2%✓ · casc 0.55✓ · attitude RED on structure
(FROZEN-RESCORE row). Full re-run of every gate is owed in the same cycle as
the FP4 composition change, on the same frozen cells/anchors/seeds; 200k rung
only if 20k moves ≥0.3pp in the right direction.

## STATUS
**ITERATING** — next step named: FP4, the named-composition fixed-point run
(post-instrument-fix decomp_2x2.py under SHARE seeded from named per-channel
parts instead of one scalar), emitting the per-cause share/age table, the
capture==journal known-answer check, and the composition numbers this report
marks TODO-VERIFY.
