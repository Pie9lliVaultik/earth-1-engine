# CYCLE v1.1-URBAN — urban-axis orientation fix (PRE-REGISTRATION)
_XI.A.2 pre-registration, filed BEFORE any measurement run. Registered defect:
ops/alive/DEFECT_URBAN_INVERSION.md (found 2026-09-08) incl. its 2026-09-08
addendum (external review M01a: consumer inventory corrected upward, poverty
anchors no longer assumed inert). The fix is PREPARED behind
`EARTH1_URBAN_AXIS_FIX` (default **off**, popsynth.py:41-55) and does NOT run
until the founder's v1.1 ruling on this document. Physics stays frozen at
freeze-0.9; flag-off is bit-identical (KA + day-10 trajectory hash,
tests/test_review_urban_flag.py). Gates below are final as of this commit;
numbers get filled in only by the registered runs._

## THE ONE NAMED CHANGE
`EARTH1_URBAN_AXIS_FIX=on` ⇒ `urb = (u == 0)` in `popsynth.draw_c2plus`
(popsynth.py:55). The joint axis carries the URBAN mass at index 0
(build_tables.py:86 `m_urb = [urban%, 1 − urban%]`), so `u == 0` IS urban;
the frozen behaviour stores `u.astype(bool)`, i.e. `civ.urban == True` means
RURAL — every country measures exactly `1 − census`. One env read, one branch,
no other code moves. Same rng stream either way (the flag flips only the
boolean; sex/age/edu/income are proven byte-identical across flag states in
tests/test_review_urban_flag.py::test_flag_on_flips_only_the_boolean).

## RESULT (to be filled by the registered runs — schema fixed now)
| field | value |
|---|---|
| gate(s) exercised | pov $8.30, pov $3.00, median, CDR, ageAtDeath, 65+, casc×, urban margins, disease-death share, air gap |
| number(s) | null board → fix board, per gate, with paired-seed σ |
| target | the registered bands in GATES below (this file is the prereg hash source) |
| gap | after − band, per gate |
| agents / seeds | 200,000 × 180 d × 4 seeds (4242 / 5151 / 6363 / 7777), both arms |
| flag set | freeze09.env verbatim + EARTH1_URBAN_AXIS_FIX={off,on}; substrate c2plus_v1 |
| hashes | tree · c2plus_tables_v2.json (t:256fe63229) · anchors (a:39d484d65f) · income-cal (i:89be94309c) — all UNCHANGED by this cycle |
| host / commit / wall-clock | stamped by the runner (Rule 10) |

## GATES — registered BEFORE the run
All gates are evaluated **board-vs-board under CRN seeds**: `branch-vs-null`
does NOT apply — this is a genesis change, so null and treatment worlds differ
from birth and cannot share a trajectory. CRN = the same 4 seeds, the same
freeze09.env flag set, the two arms differing ONLY in EARTH1_URBAN_AXIS_FIX.
σ_seed = sd of the 4 paired per-seed differences.

**G-A. Urban margins must match census, per country (the fix worked at all).**
At genesis, per-country `civ.urban` share equals the census margin
(GENESIS_COUNTRIES `urban%` = the table's axis-0 mass). Registered spot rows
(50k single-country draws, tolerance ±1.0 pp): JP **0.920**, US **0.833**,
IN **0.364**, NG **0.543**. Full check: all 194 genesis countries within
±1.0 pp on a 50k dedicated draw. (Flag-off measures exactly 1 − census;
already demonstrated, tests/test_review_urban_flag.py.)

**G-B. Poverty anchors — GATED, not assumed inert** (addendum consequence:
rent feeds deprivation, so the original "anchor board is inert" assumption is
withdrawn). Board's registered values: real (fetched) vs frozen 200k board
(FREEZE_PACKAGE_0_9.md / CALIBRATION_CYCLES.md c-MSM):
- **pov $8.30**: fix board ∈ **46.1 ± 2.0 pp** (real 46.1, frozen 45.9). Paired
  movement vs null reported with σ_seed; movement is EXPECTED (rent channel) but
  may not leave the band.
- **pov $3.00**: registered RED on the frozen board (16.8 vs real 10.4). Gate:
  **no regression** — fix board ≤ null board + 2σ_seed. Movement toward 10.4 is
  recorded, not required.
- **median $/day**: fix board within **±5 % of real 9.27** (frozen 9.61, +3.7 %).
- **CDR**: in the registered band **[0.007, 0.015]** /person-yr.
- **ageAtDeath**: in the registered on-pyramid band **[66.2, 71.8]** yr.
- **65+ adult share, casc×**: within 2σ_seed of the null board (XI.A no-regression
  rule; a >2σ regression on any board gate VOIDs the promotion).

**G-C. The five physics consumers — observables named, one must move.**
The fix must demonstrably do something; per DEFECT registration, movement of the
named movers is the test that it did. Registered movers and directions:
1. **Contagion density** (contagion.py:168, ×1.6 urban / ×0.5 rural): the
   multiplier lands on the true urban population. Observable: **disease-death
   share** (DeathWatch causes) and infection prevalence, per arm; expected UP in
   high-urban countries (JP 92 % urban), DOWN in rural-majority (IN).
2. **Air channel** (flourishing.py:113, +0.05·urban): observable: the
   **urban-minus-rural air-burden gap must flip sign** (frozen: rural agents
   carry urban pollution).
3. **Rent → deprivation** (life.py:388, ×1.35 urban / ×0.8 rural →
   Life.rent → arrears → evictions → deprivation): observables: **mean RENT,
   arrears rate, eviction rate** per arm — the channel that gates G-B.
4. **Water access** (flourishing.py:143, rural −0.12 infra offset →
   `_water_access` → thirst): observable: **water-access share / thirst
   burden**, expected to shift off the urban majority in high-urban countries.
5. **Commute / belonging** (mobility.py:100 commute factor ×1.25 urban, and the
   car-ownership term mobility.py:98 +0.6·urban): observable: **commute-time
   distribution and relationship/belonging decay** by true cohort.
Gate: at least one of movers 1–2 (the DEFECT-registered detectors) moves >2σ_seed
at 200k, else the cycle is **INERT** (flag stays off, finding recorded).

**G-D. Readout consumers — expected flips enumerated** (labels, no physics;
verified by inspection + spot probes on the fix arm):
- answer_living.py:90-91 — `urban`/`rural` cohort masks stop being swapped.
- cohort_features.py:40 — urban feature un-inverted. NOTE: any readout weights
  fitted on the inverted feature see a sign-flipped input; the frozen-cell
  rescore below is the detector.
- api/readouts.py:72,355 — profile urban/rural labels flip; api/readouts.py:473
  — the "cities" count starts counting urban localities (frozen: counts rural).
  (The M01a addendum cites the review archive's :70/:471; these are this tree's
  lines at HEAD.)
- event_log.py:163,212 — urban event filters select the true urban cohort.
- models.py:128 (custom-model urban feature; addendum cites archive :117),
  rebirth.py:487 (flights re-applied at rebirth), observe.py:51,
  db/store.py:404, loop.py:141 — stored/served labels flip.
- earth1/cohorts.py population frame: NO flip — it reads the joint axis and was
  always correct; with the flag on, boolean and frame finally AGREE (frozen:
  they contradict each other).
- Locality keys (alive.py / consequences.py / contagion.py:161 / fabric.py):
  membership structure unchanged (symmetric partition bit), but keyed GROUPINGS
  re-shuffle under CRN — covered by board-vs-board, no separate gate.

## INSTRUMENT
Flag-off bit-identity: tests/test_review_urban_flag.py (draw_c2plus bitwise vs
a fresh no-flag process, two-country mixed draw; defect probe 1 − census
reproduced; flag on ⇒ JP 0.920). Trajectory neutrality: 2,000-agent world under
freeze09.env, 10 days, v1 pop-hash identical before/after the code change with
the flag unset (hashes recorded in the apparatus-cycle report,
EXTERNAL_REVIEW_VERIFICATION_2026-09-08.md item M01a). Ground truth: census
urban margins already SOURCED inside c2plus_tables_v2.json (t:256fe63229,
axis-0 mass = GENESIS_COUNTRIES urban%); no new data role is read. Leakage:
none — no sealed/holdout estate is touched by the measurement plan. Canonical
path: both arms run the unified loop under freeze09.env with only the one flag
differing; configstamp + flags dict stamped per run. Failure case this
instrument reports: a flag-off run whose draw differs bitwise from HEAD (the
subprocess KA fails) or a fix-arm margin at 1 − census (G-A fails, fix inert
or doubly-inverted).

## DIAGNOSIS (registered)
Causal path: build_tables.py:86 puts urban mass at axis index 0 →
popsynth.py:55 stores the axis INDEX as the boolean → civ.urban inverted for
every C2+ world (class (a)/(c) implementation defect, not a missing channel).
Legacy genesis (genesis.py:203) is correct; the inversion arrived with C2+ =
the freeze-0.9 substrate. Measured signature: model urban share = 1 − census,
all four probe countries, exact (DEFECT table).

## RESEARCH
No new mechanism and no new constant — the fix restores the SOURCED census
margin orientation the tables already carry; the science of the margins was
settled at table-build time (WVS-7 + census margins, IPF; C2PLUS_BAKEOFF
REPORT v1). Competing approach considered and rejected: fixing the TABLES
(swap axis-0/1 mass) instead of the sampler — rejected because cohorts.py and
every axis-consumer already read index 0 as urban correctly; the boolean
store is the single wrong reader, so it is the smallest change.

## IMPLEMENTATION
popsynth.py:41-55: one env read (`EARTH1_URBAN_AXIS_FIX`, default "off"), one
branch (`(u == 0)` vs frozen `u.astype(bool)`), comment "review M01a —
flag-gated, founder ruling pending". Constants introduced: NONE. Substrate
tables, anchors, income calibration untouched (hashes above unchanged). Default
off ⇒ freeze-0.9 worlds bit-identical (KA + neutrality hash).

## MEASUREMENT PLAN (registered; runs only after the founder ruling)
- **Primary**: 200,000 agents × 180 days × 4 seeds (4242/5151/6363/7777),
  TWO arms per seed: null (flag off) and fix (flag on) — 8 runs. CRN seeds,
  freeze09.env otherwise verbatim. Board recomputed per arm; gates G-A..G-C
  scored on the pooled 4-seed board with paired σ_seed.
- **Margins**: 50k dedicated single-country draws, all 194 countries (G-A);
  cheap, no world run.
- **Readout**: frozen-cell rescore (FROZEN-RESCORE protocol) on the fix arm to
  detect cohort_features sign-flip damage (G-D note); TRAIN/DEV only, holdout
  untouched.
- DeathWatch threaded for the disease-death share observable (G-C.1).
- No sealed or holdout estate is read at any point in this cycle.

## PROMOTION RULE (registered)
The flag defaults **on** (and the frozen inversion is retired) ONLY when ALL of:
1. the founder's v1.1 ruling on this pre-registration is recorded;
2. G-A green (margins = census) and G-B green (poverty anchors in their
   registered bands, no >2σ regression on any board gate);
3. G-C: at least one registered mover (disease-death share or air gap) moves
   >2σ_seed — otherwise **INERT**: flag stays off, sign findings retained;
4. promotion is a NEW physics tag (v1.1) with the full anchor-board retest
   stamped, boards re-labelled board-vs-board, and DEFECT_URBAN_INVERSION.md
   closed with a pointer here. freeze-0.9 boards are never re-scored under the
   fix.
Any red gate ⇒ flag stays off, STATUS goes ITERATING with the next hypothesis
named in one line. Silent promotion (defaulting the flag without this file's
gates green and the ruling recorded) is a governance violation, not a fix.

## STATUS
**REGISTERED — AWAITING FOUNDER RULING (v1.1, first tier).** No measurement
run has been executed under this registration; the RESULT table is empty by
design. Prepared code: popsynth.py flag (default off, bit-identical),
tests/test_review_urban_flag.py (4 KAs, green), neutrality hash pair recorded.
