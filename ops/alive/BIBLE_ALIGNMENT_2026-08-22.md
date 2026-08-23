# BIBLE ALIGNMENT AUDIT — 2026-08-22 (read-only; Bible v4.1 canonical)

Scope: reconcile branch `v1-unification` (HEAD 2617218) and the A–I
acceptance campaign against the exact Phase 0 sequence of Bible v4.1
(Part VIII table + the v4.1 amendments 0.0a–d). No code was modified.
Stage C continues on prime; Stage D is NOT started.

Classification: DONE / PARTIAL / NOT DONE / SUPERSEDED WITH EQUIVALENT.
Every DONE carries executable evidence (commit, path, test, artifact).

## A. BIBLE PHASE 0 — STATUS TABLE

| # | Bible requirement (v4.1 text) | status | executable evidence |
|---|---|---|---|
| 0.0a | aging wired into `live_one_day`; invariant: 365 days age every survivor exactly one year | **DONE** | `earth1/alive.py` step 0.0a (`advance_age`, :126-127); `tests/test_alive_semantics.py:28 test_one_year_ages_everyone_by_one_year`, `:76 test_daily_increments_compose_to_a_year`, `:45 test_the_frozen_age_defect_is_detectable`; production acceptance chain "0.0a ✅" in `ops/alive/REBIRTH_ACCEPTANCE_0_0B.md:61`. Note: no standalone 0.0a acceptance doc (attested in chain + release gate). |
| 0.0b | virgin-slot rebirth; zero inherited ties | **DONE** | `ops/alive/REBIRTH_ACCEPTANCE_0_0B.md` (ACCEPTED, 1,266 real rebirths, zero violations); `tests/test_rebirth.py:138 test_zero_inherited_ties_all_types`, `:84`, `:101`. |
| 0.0c | complete persistence (presence, mobility, RNG, clock, version); save→restore→hash equality; branch-from-snapshot ≡ branch-from-live | **DONE** | `earth1/persistence.py` PERSISTENT_FIELDS policy + completeness assertion (`:70-108`); `tests/test_persistence_roundtrip.py:112 test_roundtrip_hash_equality`, `:158 test_rng_state_roundtrips`, `:102 test_every_persistent_field_reaches_disk`; tag `v1-persistence-deploy-1`=`ae65bcd` (`ops/alive/DEPLOY_RUNBOOK.md:4`); branch-equivalence additionally evidenced by PF-DECAY KA5 bitwise restart continuation (`data/pf_decay2/ka.json`) and the 0.7 deterministic paired-ensemble (`ops/alive/SESSION_STATE.md:28-29`). No standalone 0.0c doc. |
| 0.0d | fabric re-homing on migration/firm change | **DONE** | `ops/alive/REHOME_ACCEPTANCE_0_0D.md` (ACCEPTED, 339 migrations + 34,126 employment transitions, zero violations); `tests/test_rehome.py:84, :155, :262, :285`; `earth1/rehome.py`. |
| 0.1 | four correctness bugs: seeded `memory.spread`; separate RNG row for treatment; conviction decay real or deleted; shared `CauseOfDeath` | **DONE (one by equivalent)** | `earth1/memory.py:99 spread(self, civ, rng)` seeded; `earth1/types.py:22 class CauseOfDeath(IntEnum)`; conviction decay: the docstring claim removed and the no-op made explicit/disabled (`earth1/influence.py:43, :110-119` — the "delete the claim" branch of the Bible's either/or); treatment RNG: SUPERSEDED WITH EQUIVALENT — `branch.run` gives treatment and control the SAME stream (`earth1/branch.py` "SAME dice as control") and `apply()` draws no randomness, so common random numbers hold without a structural separate row; paired determinism proven in 0.7. `ops/alive/CORRECTNESS_ACCEPTANCE_0_1.md` ACCEPTED. |
| 0.2 | unify the loop: `chaos.world_step` = wrapper over `live_one_day`; one cascade implementation; one beta declared | **DONE** | `earth1/chaos.py:30-40 world_step` delegates to `live_one_day`; only one `*_step` in `earth1/`; one cascade block (`alive.py` step 9); `CANONICAL_DAY` declared (`alive.py:95`); `ops/alive/ONE_LOOP_ACCEPTANCE_0_2.md` ACCEPTED (deployed `ca95903`). **Annotation (the drift):** the unified loop is the INCUMBENT physics; candidate `76a574c` is a second *configuration* of that loop assembled by monkeypatch in `scripts/it6_dyadic.py` — see §C. |
| 0.3 | live-path tests first; semantic invariant suite as release gate | **DONE** | `ops/alive/RELEASE_GATE_0_3.md` ("delivered"; `python3 -m earth1.release_gate`, machine-readable `data/release_gate_report.json`); 14 live-path test files incl. the four invariant suites (`test_alive_semantics.py`, `test_rebirth.py`, `test_persistence_roundtrip.py`, `test_rehome.py`); `earth1/release_gate.py` gates `single_writer_world`, `one_production_earth`. Observation: 35 test files still exercise the dead family (legitimate until retirement completes; not a 0.3 miss). |
| 0.4 | `answer.py` gets a World adapter; `_build_features` extended with within-unit life state; leakage gate re-run; a WVS item answered from the living world end-to-end | **PARTIAL (readout DONE by equivalent; `answer.py` NOT DONE)** | DONE side: `earth1/calibration.py:94-146 LIVING_FEATURES / _living_matrix / living_features(w)` builds the exact v4.1 feature set from the living World; `ops/alive/LIVING_READOUT_ACCEPTANCE_0_4.md` ACCEPTED (dev gate closed on frozen protocol, holdout untouched). NOT DONE side: `earth1/answer.py:113` still takes `civ` not `World`, calls the non-living `_build_features` (`answer.py:130,137`), imports the dead family (`answer.py:231 from earth1.tick import _make_mutable`), and has ZERO importers — `earth1/legacy_gate.py:47-49` records it as "audited orphan awaiting its Benchmark-A rebuild on the living readout". The Bible's literal exit was met via a parallel path, not via `answer.py`. |
| 0.5 | port unique physics (`perishability`, `coupling`, `graph_dynamics`, `event_generation`, `dynamics`-residue); repoint `benchmark.py`/`predictions.py`/API; quarantine `engine/tick/living/advance/diffusion/forces`; exit: no benchmark or API route imports the dead family; every production surface resolves the same world UUID/hash as the daemon | **PARTIAL** | DONE: API — all mounted routes (`ask/world/forecast/observatory`) resolve `alive.World` through `earth1/api/deps.py:48-70 get_world()` with `snapshot_sha256`/`checksum` identity; retired resolvers raise (`deps.py:111-121`); `routes_legacy/lab.py` unmounted (`api/main.py:77-82`). DONE: quarantine gate — `earth1/legacy_gate.py:26-31 QUARANTINED` + `assert_one_production_earth()` (`:95-102`), package init no longer imports the family (`earth1/__init__.py:6-14`), CI sabotage control (`tests/test_api_one_earth.py:162-175`). DONE/SUPERSEDED: unique physics dispositions machine-checked in `tests/test_legacy_dispositions.py` — `graph_dynamics` PORTED as `earth1/plasticity.py` ("Phase 0.5 port"); `perishability` pure readout; `coupling` question-layer only; `event_generation` bound to retired engine; `dynamics` superseded (coverage test); `ops/alive/ONE_EARTH_ACCEPTANCE_0_5.md` ACCEPTED (47/47 handlers; 1 PORT · 2 READOUT-ADAPTER · 2 SUPERSEDED). **NOT DONE:** `earth1/benchmark.py:22,1664` and `earth1/predictions.py:21,535` still import `earth1.engine`; `scripts/benchmark_v2.py` runs `genesis + run_goqa_benchmark` on the old engine — the Bible's exit "no benchmark … imports the dead family" is unmet for the benchmark modules (the `predictions` API ROUTE itself is DB-only and clean). The dead-family modules still exist un-deleted (quarantined by gate, not removed). |
| 0.6 | kill the third world; world box is the single writer | **DONE** | `ops/alive/SINGLE_WRITER_ACCEPTANCE_0_6.md` ACCEPTED; plist archived `ops/legacy_archive/com.earthling.earth1-daily.plist.retired`; zero `.plist` in repo; `earth1/single_writer.py` + `release_gate.py:79-80 single_writer_world`; `data/living/NON_CANONICAL.md`. |
| 0.7 | all ensembles on Prime (96c); storage-box backup verified green AND made incremental (18 GB worlds); exit: paired 20-repeat ensemble < 30 min | **PARTIAL / OPEN by ruling** | DONE: backup chain CLOSED and verified green — `ops/alive/earth1-backup.{service,timer}`, `ops/alive/run_backup.sh`, on-box restore rehearsal PASSED (`SESSION_STATE.md:23-30`); 0.7a software leg COMPLETE (`SESSION_STATE.md:18`). NOT DONE: backup is NOT incremental — `run_backup.sh:89 rsync -a --partial --inplace` (whole-file per run; no `--link-dest`/snapshotting); Prime not granted Storage Box credentials (`SESSION_STATE.md:40`). NOT MET: <30 min — prime f64 ~46 min; 0.7b OPEN / HARDWARE-DEFERRED by founder ruling 2026-08-20 (`SESSION_STATE.md:19`). |
| 0.8 | re-measure butterfly, FSLE, noise floor, consciousness profile on the unified loop — same preregs, same thresholds; exit: the chaos chapter re-stated on the real system | **NOT DONE (and currently mis-targeted)** | None of the four remeasurements has been run on the unified loop. The instruments (`scripts/butterfly_full.py`, `scripts/consciousness_profile.py`) drive canonical `live_one_day` — i.e. the INCUMBENT physics — with no candidate assembly; run today they would measure the wrong Earth relative to the validated candidate (§C). The A–I campaign's Stage H is where this was scheduled; it cannot honestly execute until §C is resolved. |

Semantic invariants 0.0a–d: all four suites exist and are green in the
release gate (`tests/test_alive_semantics.py`, `test_rebirth.py`,
`test_persistence_roundtrip.py`, `test_rehome.py`; `earth1/release_gate.py`).

## B. THE EXPANDED HUMAN-PHYSICS A–I CAMPAIGN (developed during 0.8)

Correct description: an expanded Phase-0 human-physics acceptance
campaign created during the 0.8 work, grown from real falsifications
(pinned force field → IT1–IT12 → PF-DECAY-1/2 → Stage A v1 FAIL →
GEO-0/1). It is valid evidence and methodologically aligned with the
Bible (MISS → diagnosis → hypothesis → calibration → DEV retest →
FREEZE → HOLDOUT once; immutable preregs; paired controls; evidence
ledger; no tuning for chaos). It is NOT the Bible's 0.8 and must not
redefine it:
- Stages A, B (PASS) and C (running) are internal validity — Bible
  evidence classes E1–E3.
- Stage D (T2 post-9/11 holdout) is the first external test — moving
  toward E4; E1–E3 cannot substitute for it.
- Completion of A–I ≠ Bible Phase 0.8 completion. Bible 0.8 is the
  four chaos remeasurements on the unified canonical executable.
- V1-readiness per module still requires all five: save/reload +
  snapshot/restore (have); parameter provenance + uncertainty
  (authored slopes/amplitudes remain — NOT met); an observable
  calibrated against real data (Stage D is the first); expected causal
  difference when disabled (Stage B's broken twins partially cover);
  timestep/resolution stability (dt=1 only; declared N/A).
- Public claim stays: "a living, branchable synthetic civilization
  kernel with material, biological, social, institutional and memory
  state" — not "validated predictor of civilization".

## C. THE DRIFT — candidate `76a574c` vs the canonical executable

Finding (verified): the validated candidate does NOT exist in canonical
physics modules.
- `earth1/alive.py` imports the incumbent `propagate` and
  `update_conviction` (`alive.py:29`) and declares `CANONICAL_DAY`
  relax=0.25 (`alive.py:95-96`); it references neither `field_lab` nor
  `conviction_lab` (grep: zero hits).
- Every candidate social-physics component — dyadic propagate
  (k=3, mu=0.05, tie-weighted sampler), dyadic feed, dyadic conviction
  (C3 log-odds, gain 0.003, encounter-driven), flourishing level-map,
  flourishing-write suppression, CONTAGION_GAIN=0, relax=0.045 — lives
  only in `earth1/field_lab.py`, `earth1/conviction_lab.py` and the
  assembly in `scripts/it6_dyadic.py:run_arm` (op="dy", cnv="dy",
  flr=True, cas=True), reused by every 0.8 runner.
- Only the three flag-gated repairs are canonical code, and default
  OFF: cascade cooldown (`alive.py:349`), open-loop residue
  (`alive.py:257,354-355`), centered COLLECTIVE (`life.py:163`,
  `field_lab.py:126`).
- The production daemon `scripts/world_alive.py:284` runs
  `live_one_day(w, rng, **CANONICAL_DAY)` — incumbent physics, no
  flags (correct per the standing "production untouched" ruling, but it
  makes the canonical Earth and the validated candidate different
  physics). The API (`deps.get_world`) and the Observatory demo
  therefore also answer from incumbent physics.
- Consequence for Bible 0.8: the chaos instruments measure
  `live_one_day` as canonically defined, i.e. the incumbent. The Bible's
  "instrument and world are the same program" holds for the incumbent
  and is VIOLATED for the candidate, which was validated as a lab
  assembly — precisely the "two systems that both look canonical"
  pattern the Bible exists to prevent.

## D. THE MECHANICAL PORT REQUIRED (specified; NOT performed)

Port `76a574c` into canonical modules so that `live_one_day` with no
flags IS the candidate — one declared physics, no env toggles in
production:
1. `earth1/influence.py`: canonical `propagate` := the dyadic law
   (tie-weighted inverse-CDF partner sampling, k=3, mu=0.05 toward
   partner value; DRIVE_ACC/ENC_COUNT bookkeeping moved out of module
   globals into World state); canonical `update_conviction` := dyadic
   C3 log-odds (gain 0.003) driven by the day's encounters.
2. `earth1/feed.py`: `feed_tick` := dyadic feed law (feed graph +
   arousal weights preserved).
3. `earth1/contagion.py`: CONTAGION_GAIN declared 0 (ambient smoothing
   off) as the canonical value, not a runtime patch.
4. `earth1/life.py` `life_force_target`: absorb the flourishing
   level-map terms natively (FEAR/DESIRE/COLLECTIVE/CULTURE/EXPERIENCE
   from hope/need/belonging/meaning/curiosity) including the centered
   COLLECTIVE law as the law, not a flag; `earth1/flourishing.py`:
   unconditional daily force increments removed (level map only).
5. `earth1/alive.py`: `CANONICAL_DAY.relax` := 0.045; cascade cooldown
   and open-loop residue semantics unconditional (flags removed);
   `effective_forces` retained as the readout contract; test-only
   broken-twin flags relocated to a test harness or kept under a
   single `EARTH1_TEST_*` namespace excluded by the release gate.
6. Retire `field_lab`/`conviction_lab` assembly to `experiments/` (or
   add to `legacy_gate.QUARANTINED`); `scripts/it6_dyadic.py` becomes a
   thin runner over canonical `live_one_day` (cfg keys map to the
   declared canonical values only).
7. Parameter registry entry per ported constant with provenance class
   (empirical / derived / authored-experimental) — Bible III.6.

Equivalence tests the Bible requires before the port is accepted
(0.2/0.3 class — the instrument and the world must be the same program):
- KA0-class bit-identity: ported canonical `live_one_day` vs the lab
  assembly (it6 "ALL" + three flags) on seed 8890, 120d — bitwise
  `civ.forces` every day AND the recorded panels/tau/transmission
  (`data/it6_dyadic/arms.json`-class) exact; same for a GEO-1-era seed
  (e.g. 9301) at 365d vs `data/acceptance_0_8/stageA_v2/endurance.json`.
- Full semantic invariant suite green (`python3 -m earth1.release_gate`).
- PF-DECAY open-loop KA battery and GEO-1 KA battery re-run green on
  the ported canonical (no flags).
- `legacy_gate.assert_one_production_earth()` green; no benchmark or
  API route imports the dead family (this also closes the 0.5 residue
  in `benchmark.py`/`predictions.py`).
- API identity: `/world` resolves the same world hash as the daemon
  after deploy (0.5 exit); Observatory repointed to the canonical world.
- Only then: Bible 0.8 chaos remeasurements on THAT executable — and
  the A–I Stage H becomes the same run.

Deployment caveat for the founder (not a port question): the living
production Earth has ~1,180+ days of history under incumbent physics.
Making the ported candidate canonical in CODE is mechanical; switching
the RUNNING civilization's physics is an epoch-class decision (state +
physics continuity), to be ruled separately. The Bible's 0.5 ordering
assumed the port preceded that history.

## E. SUMMARY VERDICT

Bible Phase 0 status: 0.0a–d DONE · 0.1 DONE · 0.2 DONE · 0.3 DONE ·
0.4 PARTIAL · 0.5 PARTIAL · 0.6 DONE · 0.7 PARTIAL/OPEN · 0.8 NOT DONE.
Phase 0 is NOT complete. The A–I campaign is valid E1–E3 (E4 pending
Stage D) evidence about a lab assembly that is not yet the canonical
Earth. No further "Phase 0.8 completion" claim is admissible until the
§D port lands and its equivalence tests pass.
