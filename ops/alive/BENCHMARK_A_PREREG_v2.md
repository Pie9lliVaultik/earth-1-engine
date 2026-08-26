# BENCHMARK A — PREREGISTRATION v2 (FROZEN)

Frozen 2026-08-26, before any confirmation target is built or scored.
Design source: VNF_CALIBRATION_LESSONS.md (accepted by founder GO). No
physics change; Epoch-3 physics untouched; lab worlds only.
Principle: **the statistical calibration layer supplies absolute
population levels; Earth-1 must earn incremental value through agent
structure.** If v2 merely reproduces MRP everywhere, that is the
failure mode, not the goal.

## 1. Core architecture
Per scored cell: logit(p_i) = logit(p_anchor) + Δ_i − K, where Δ_i is
the agent latent with its weighted mean removed (`center_latent`) and K
is solved by bisection (`earth1/benchmark_a/mean_preserving.py`, sha
4a8f31e98a42138e…) so the weighted synthetic mean equals the anchor to |err| ≤ 1e-9.
No sigmoid averaging or later stage may shift the calibrated marginal.
KA (frozen, passing): `ka_mean_preservation` — 200 deterministic cases,
worst |mean − anchor| ≤ 1e-8, ordering of p_i identical to ordering of
Δ_i (structure preserved). `tests/test_benchmark_a_v2.py`.

## 2. No target leakage through MRP
p_anchor is NEVER an observed target. Every anchor is the MRP
prediction for a country produced from the frozen fold's TRAIN
countries only (folds = `cv_folds` protocol: 5 folds × seeds 42/7/13).
Every scored row records: target, anchor, anchor_train_countries,
anchor_model, Earth-1 residual contribution, final hybrid. The scorer
calls `leakage.assert_anchor_oos` on every row and FAILS CLOSED
(`test_leakage_guard_fails_closed`).

## 3. Task strategies (what MRP supplies vs what Earth-1 must earn)
- **(i) country means — calibration sanity, no credit.** The hybrid
  inherits the OOS MRP country marginal exactly (KA). Reported: anchor
  inheritance error (must be ≤ 1e-8) and, as diagnostic only, Earth-1's
  own unanchored national readout. No gate credit for the level.
- **(ii) cohorts — Earth-1's test.** Cell prediction = weighted mean of
  the anchored agent p_i inside (country, band): the country anchor is
  the OOS MRP national value; the weighted cohort deviations aggregate
  to it EXACTLY by construction (single per-country K). Cohort cells
  are NOT anchored to their observed values. Baselines: national-copy
  (= anchor), global-gradient (anchor + TRAIN-country mean band offset
  per item), **cohort-MRP** (fit_mrsp on TRAIN-country cohort cells with
  band dummies + band×context). Gate: ≥10 % relative MAE reduction vs
  the strongest baseline AND ≥75 % gradient direction (sign of cell −
  country anchor vs sign of truth − truth-national).
- **(iii) joints — central.** Marginals are anchored to the OOS MRP
  predictions for BOTH arms: Earth-1 agents (per-item K against the MRP
  marginal) and the independence baseline (items sampled independently
  from the SAME MRP marginals, equal n). Energy distance (Hamming) to
  the weighted respondents then shares the marginal error and differs
  only in dependence/covariance/tail/conditional structure. Gate:
  Earth-1 lower, median over countries, paired bootstrap CI excluding
  0. The v1 observed-marginal variant is DIAGNOSTIC ONLY (it touches
  the target marginal).
- **(iv) held-out questions — zero-shot transfer.** AMENDMENT
  2026-08-26, pre-result (recorded before any confirmation baseline or
  Earth-1 number was seen): because the anchored country mean equals the
  transfer anchor BY CONSTRUCTION, task (iv) is scored on the zero-shot
  items' COHORT CELLS. Baselines per cell: national-copy (= the
  transfer anchor) and neighbour-offset transfer (anchor + the
  neighbour item's TRAIN-country mean band offset). Earth-1 arm: band
  means of the anchored agent p_i under transferred weights. Gate
  unchanged in spirit: beat the strongest baseline, paired CI excluding
  0. Joint binarization: Bernoulli(p_i) with crc32-keyed deterministic
  RNG (the salted-hash seeding in the first implementation was
  non-reproducible; fixed pre-result). The scored item's
  observed responses are used for nothing. Earth-1 arm: anchor = the
  semantic neighbour's OOS MRP prediction for that country; Δ from the
  neighbour's fitted weights (transfer); K per cell. Baseline:
  **semantic-MRP transfer** = the neighbour's OOS MRP prediction itself
  (same information, no agents). Neighbour = highest cosine
  (`earth1.embedder`, thenlper/gte-base) among development items. Gate:
  beat the baseline, paired CI excluding 0. LLM baseline remains frozen
  (Appendix A of v1) and unexecuted pending authorization.
- **(v) cross-wave: BLOCKED-ON-DATA** (unchanged).

## 4. Features and orthogonalization (frozen before confirmation)
Feature set: `living_features` (26) restricted by TRAIN-side rank
analysis on the development items: drop exact linear combinations and
near-collinear columns (|r| > 0.98, drop-later-by-frozen-order), report
condition number and VIF; adjacency-gate bans stand (active injected
set: none). Country axes are removed by construction (within-country
centering of Δ); age/cohort axes are NOT orthogonalized away — cohort
credit is assigned by scoring against the cohort-aware baselines, not
by feature surgery. The surviving feature list is written to the report
and frozen before the confirmation run.

## 5. Data, development vs confirmation
- **Development (v1 holdout = CONSUMED):** the 40 GOQA items, their
  cohort cells and joints. Used for architecture, hyperparameters (ridge
  λ grid {0.1,0.3,1,3,10} by inner LOO on TRAIN), feature treatment, and
  development-labelled results including comparison to the v1 scoreboard.
  No E4/generalization claim can come from them.
- **Genuinely untouched confirmation set (exists):** all labelled
  non-GOQA WVS-7 items EXCLUDING the v1-consumed 8 (Q10 Q23 Q51 Q68 Q86
  Q138 Q169 Q196), with mappable scale (max ≤ 5, = 10, or binary) and
  ≥ 40 country cells (cell n ≥ 100) under the frozen default coding
  (1–10 → ≥6; 1–4/1–5 → top-2; binary → =1). These items have never
  been aggregated, scored, or seen by any model or reviewer in this
  program. Their targets are built AFTER this freeze. Cohort cells and
  an 8-item joint set (widest coverage, ties by code) come from the same
  items; the (iv) zero-shot subset = 8 items by stride over the sorted
  confirmation list (indices 0, ⌊N/8⌋, 2⌊N/8⌋, …). Evaluated ONCE.
  (GSS and ANES zips in the estate remain untouched future confirmation
  options; not used in v2.)
- Worlds: the three v1 lab worlds (seeds 42/20260901/20260902, 200k,
  60 days, Epoch-3 physics; hashes in earth1_v1.json), reused unchanged.

## 6. Compression trace and abstention
Every published prediction carries the trace raw_latent → anchor →
mean_preserved → guard → published, each with spread |2p−1| and the
spread delta. Guards may ABSTAIN (cell dropped and counted: agents < 30,
anchor missing, |Δ| degenerate) and may never move a value toward 0.5;
no stage after mean-preservation may change the cell marginal.

## 7. calibration_source
Every row declares the decomposition: level = mrp@fold (train
countries listed); structure = earth1@{world seed, world hash};
transfer = neighbour item + cosine (task iv only); offsets: none in v2.
The product sentence this enables: "the population level is empirically
calibrated; the heterogeneity and simulated response are generated by
Earth-1."

## 8. Frozen artefacts
Scorer `earth1/benchmark_a/scoring.py` sha 9ad644b0ea286c38… (unchanged from v1);
mean-preserving solver sha 4a8f31e98a42138e…; folds `data/cv_folds.json`; targets
builder rules §5; baseline versions: MRP = `scripts/mrp_baseline.py`
fit_mrsp + build_context (parity inputs), cohort-MRP as §3(ii);
seeds: worlds 42/20260901/20260902, CV 42/7/13, bootstrap 0; tolerance
1e-9; abstention rules §6; leakage KA §2; gates §3. Execution order:
fit on TRAIN → hyperparameters on validation (inner LOO) → freeze the
candidate → KA proof → baselines on confirmation → Earth-1 on
confirmation → score ONCE. Committed before any confirmation target
exists.
