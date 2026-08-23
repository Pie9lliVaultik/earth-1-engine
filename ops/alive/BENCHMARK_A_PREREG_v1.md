# BENCHMARK A (PHASE 1) — PREREGISTRATION v1 (FROZEN)

Frozen 2026-08-23 before any dataset is built from the frozen rules and
before any model sees any target. Bible v4.1 §11. Code under test:
`main` (Epoch-3 physics `0.8-candidate-v4.1/posthumous-invariant-rc`).
Commit SHA of this registration: recorded in BENCHMARK_A_REPORT_v1.md.

## 1. Data

- **Available and used:** WVS Wave 7 (2017–2022) Cross-National v6.0
  official microdata, `WVS_Cross-National_Wave_7_csv_v6_0.csv`, sha256
  `593a18671f9edd4d53d1e0cf2101c8f5a34b159c5bed9da4de9bd07bc8d56cd4`, 97,220 respondents, design weight `W_WEIGHT`, country
  `B_COUNTRY_ALPHA` (ISO3 → ISO2 via `benchmark_questions.ISO3_TO_ISO2`).
  Held on prime under the terms accepted on 2026-08-18; never committed.
- **Specified but NOT available:** the WVS/EVS Trend 1981–2022 file
  (repeated cross-sections). It is registration/licence-gated and not in
  the estate; the in-repo W5/W6 numbers are self-described estimates of
  published aggregates (`earth1/wvs_wave5.py`) and are NOT admissible
  ground truth. Consequence: **task (v) cross-wave deltas is
  BLOCKED-ON-DATA in v1** (registered below; executable unchanged once
  the Trend file is supplied). Tasks (i)–(iv) run on Wave-7 microdata.
- **Inclusion:** respondents with `W_WEIGHT > 0` and a valid (≥ 0) answer
  on the item; country cells with n ≥ 100 respondents on the item;
  countries present in `GENESIS_COUNTRIES`. Cohort cells: n ≥ 50.
  Missing = listwise per item (no imputation).
- **Item coding (frozen, per item; recorded in
  `data/benchmark/goqa_gt_rule_diagnosis.json`):** 1–10 scales → yes iff
  ≥ 6, except Q106/Q164/Q48 ≥ 7 and Q240 ≤ 4; 1–4/1–5 scales → top-2
  (codes 1,2) except Q131/Q36 bottom-2; Q57 = 1; Q65 = 1; Q222 = codes
  2–4 (scale rule for the two irreproducible items). New questions
  (§4 iv): 1–10 → ≥ 6; 1–4/1–5 → top-2; binary → = 1. **Weighted by
  W_WEIGHT.** Targets file: `data/benchmark_a/targets_v1.json` with
  manifest (counts per country/item, hashes).
- Cohort cells: country × age band {18–29, 30–49, 50+} from `Q262`
  (age). Joint vectors: the 8 GOQA items with widest country coverage
  after coding, chosen by the builder by coverage count (ties by code),
  recorded in the manifest.

## 2. Splits

- **Country CV = the frozen protocol** `data/cv_folds.json` (reference
  pop 200,000, genesis seed 42, 5 folds, CV seeds 42/7/13; test folds
  by seed permutation as in `scripts/living_readout_dev.ridge_cv`).
  Held-out countries never enter fitting, standardization, or selection.
- **Validation for hyperparameters:** inner leave-one-country-out INSIDE
  each train fold (ridge λ ∈ {0.1, 0.3, 1, 3, 10}; MRP λ, τ as in
  `scripts/mrp_baseline.py`).
- **Question holdout** `earth1.holdout.HOLDOUT_IDS` untouched (not part
  of any arm).
- **New-question set (task iv), frozen now:**
  `data/benchmark/benchmark_a_new_questions_v1.json` sha256 `9827c8e540941fa3307408710af1137760bd8139a0995491f11e85b08d7d208a` —
  Q10, Q23, Q51, Q68, Q86, Q138, Q169, Q196 (deterministic rule: sorted
  non-GOQA labelled items, indices 3,16,29,… stride 13, first 8). No
  Earth-1 readout has been taken on them.
- **Final wave untouched** (task v): n/a in v1 (no Trend data).

## 3. Earth-1 arms (no physics change; all on lab worlds)

- Worlds: `birth_world(200_000, seed)` for seeds **42** (pinned genesis),
  **20260901, 20260902** (fresh, burned here), lived **60 canonical days**
  on Epoch-3 physics (the living-readout protocol), paired across arms.
- Features: `calibration.living_features(w)` (18 static + 8 lived);
  banned features excluded by the gate (active injected set: none).
- **E1-national:** per item, ridge in logit space on country-aggregated
  features (train folds), prediction = held-out country sigmoid
  readout; agent-level stance for cohorts/joints uses the same fitted
  weights on individual features (`calibration` path:
  `sigmoid(b0 + z_i·w)`).
- **E1-hybrid:** MRP national prediction as offset + Earth-1
  within-country structure (cohort/joint) — the Bible's calibration-
  layer reading if MRP wins nationally.
- Readouts are means of per-agent stances over alive agents (country /
  country×age-band), 3 seeds → CIs.

## 4. Tasks, baselines, gates (verbatim from Bible v4.1 §11)

| task | Earth-1 readout | baselines | gate |
|---|---|---|---|
| (i) country means, 40 items × ~60 countries | E1-national, E1-hybrid | **MRP-strong** = `scripts/mrp_baseline.py` (MrsP/autoMrP-style: ridge + partial-pooling country intercept, context covariates log GDP pc / HDI-class / region, λ,τ by inner LOO; PARITY inputs); **naive** grand mean | non-inferior to MRP (≤ 0.5 pp excess MAE) **or** significant hybrid gain (paired bootstrap CI excludes 0). The country mean alone is not sufficient. |
| (ii) cohort/age cells | E1 agent-level cohort means (national + within-country structure) | **national-copy** (cell = MRP national), **global-gradient** (MRP national + train-fold mean cohort offset per item) | ≥ 10 % relative MAE reduction vs the strongest baseline **AND** ≥ 75 % correct gradient direction on held-out cells |
| (iii) joint distributions, 8-item binary vectors per country | E1 agents' binarized stances (raw; and marginal-matched by per-country quantile shift, secondary) | **independent-marginal synthetic population** (items sampled independently from the weighted microdata marginals, same n) | energy distance (Hamming) to respondents lower than the independent-marginal population, median over held-out countries, bootstrap CI excluding 0 |
| (iv) held-out question generalization | weights via `calibrate.calibrate_from_neighbors` (cosine over force vectors of calibrated items) → readout on held-out countries | **semantic-neighbour** (country shares of the most text-similar GOQA item, hashed-TF-IDF cosine); **LLM** = `claude-haiku-4-5-20251001`, temperature 0, frozen prompt (Appendix A) asking per-country yes-shares — **AWAITING AUTHORIZATION** (spends money; stop condition); if authorized it is scored by the frozen scorer on the same set and its answers cannot depend on Earth-1 output | beat the LLM/semantic-neighbour baseline (lower MAE, paired CI excluding 0) |
| (v) cross-wave deltas | — | no-change, trend | beat both — **BLOCKED-ON-DATA (Trend file)** |

Baselines run through the frozen scorer BEFORE any Earth-1 readout.

## 5. Scoring (frozen)
`earth1/benchmark_a/scoring.py` sha256 `9ad644b0ea286c38107fb351b8cb83867b3af79612c3b7375225d3044e1e92be` — mae_pp, relative_reduction,
gradient_direction_pct, energy_distance (Hamming, weighted, deterministic
subsample 4,000), bootstrap_ci / paired_bootstrap_diff_ci (2,000 resamples,
seed 0). All arms use it.

## 6. Reporting rule
Headline = incremental value over the best statistical baseline, written
first. If MRP wins national means, Earth-1 uses MRP as the calibration
layer and the claim moves to cohorts / joints / held-out questions /
cross-wave. Misses reported as misses. No arm added after this freeze. A
disappointing number is not an instrument defect; instrument defects ⇒
VOID + repair + rerun, recorded.

## 7. Provenance stamp (every result row)
physics_version, epoch uuid (lab world: none; live reference
bf5359fa-3ddd-4389-be8e-9083b428576c), world_hash, world_day, alive,
seed, calibration_source, commit SHA, scoring sha256, targets sha256.

## Appendix A — frozen LLM prompt (not executed without authorization)
System: "You estimate World Values Survey Wave 7 (2017–2022) results."
User: "For the question: «{text}» (answer coded yes = {rule}), give your
best estimate of the share of adults answering yes in each of these
countries: {ISO2 list}. Reply as JSON {ISO2: share in [0,1]}."
Model claude-haiku-4-5-20251001, temperature 0, max_tokens 2000, one call
per question, no retries on content.
