# EXPERIMENT PLAN — Predictive Value of Earth-1

**Status: PLAN ONLY. No code changed. Awaiting approval before implementation.**

Mission: determine (Q1) whether empirical formative environment explains secular
cohort change, and (Q2) whether the civilization machinery itself improves
prediction. Architecture freeze respected: production physics untouched;
everything experimental is flag-gated with default-off, proven bit-identical
when off.

---

## 0. Pre-plan verification (done, read-only)

Claims the mission asked me to verify before planning — all confirmed:

| Claim | Verdict | Evidence |
|---|---|---|
| Newborn traits derive from parent + young-cohort mean | ✅ | `generational.py:212-225`: `base = h·parent + (1−h)·young_cohort_mean`, h=0.4, noise σ=0.08 |
| Default secular `cohort_drift` is zero | ✅ | `generational.py:159`: `cohort_drift = cohort_drift or {}`; docstring: "Default cohort_drift is ZERO" |
| `cohort_drift` is a **global** per-trait constant | ✅ — this is the gap Q1 fills | `generational.py:223`: same `drift` for every country and every year |
| `data/wdi_tide.json` exists with the 3 indicators | ✅ | gdp_pcap_ppp / tertiary_enroll / urban_share, 1990–2024 (tertiary→2021), 246–264 World-Bank codes (includes aggregates — must filter to ISO-2 countries) |
| WVS temporal benchmark exists | ✅ | `wvs_paired.py`: 15 questions, W6 (2010-14) → W7 (2017-22), **410 country-question pairs, 37 countries** |
| All 15 questions classified SECULAR by blind partition | ✅ | `data/temporal_partition.json` (A5, Haiku temp-0, text-only) |
| Mechanism toggles already exist in the tick | ✅ | `tick.py:109-115`: `enable_feedback / enable_coupling / enable_thresholds / enable_rewire / enable_event_generation / enable_receiver / use_force_dynamics`. **Diffusion has NO toggle** — it runs unconditionally inside `run_question()`'s settle step; needs a pass-through parameter (§6) |

**Standing preregistration that binds this experiment:** amendment **A6 + A6.1**
in `data/g5_preregistration.json` already registered (before any fit code
exists): sign-constrained ridge, W5→W6-only fitting, frozen betas, rate
normalization `drift = β_q · D_rate` with per-country fieldwork intervals,
LOO-country scoring, shuffled-development placebo, sign accuracy declared
CONTAMINATED. Q1 of this experiment **implements A6, it does not replace it**.
Any deviation would need an append-only amendment.

---

## 1. Exact datasets available

| Dataset | Location | Contents | Temporal role |
|---|---|---|---|
| WVS W6→W7 paired aggregates | `earth1/wvs_paired.py` | 15 questions × ~27 countries each; W6 2010-14, W7 2017-22 | **evaluation** (contaminated — see §3) |
| WVS W5 aggregates | **NOT YET IN REPO** — must be compiled from published sources (2005-2009 wave) into `wvs_paired.py` | same 15 questions where published | **training era** (W5→W6 deltas) — never inspected, not yet in repo |
| WDI development indicators | `data/wdi_tide.json` | GDP/cap PPP, tertiary enrollment, urban share; 1990–2024 per country per year | formative-environment source (both eras + formative windows back to 1990) |
| Fieldwork-year alignment | to be committed with the fit (A6 requirement) | per-country W5/W6/W7 fieldwork years | interval normalization (A6.1) |
| Perceived event cases | `data/perceived_cases.json` + `data/question_profiles.json` | A3 event-reaction cases with LLM-perceived shocks + response profiles | **event-class benchmark** for Q2 |
| GOQA ground truth | `data/benchmark/goqa_ground_truth.json` | cross-sectional country targets | NOT used (bypasses dynamics — tenth review; B≡C on it by construction) |
| Census/Hofstede/Inglehart | `earth1/census.py`, `earth1/culture.py` | genesis conditioning | population init (identical across all variants) |
| GDELT replay | `data/gdelt_history.json` | historical exogenous forcing (A2) | not used in v1 of this experiment (already measured; results known) |

Dataset hashes (SHA256 of file bytes; for `wvs_paired.py` the file itself) are
recorded in the frozen spec **before** any result is computed (§7).

## 2. Exact train / dev / untouched-test split

```
TRAIN   : W5→W6 observed deltas (once W5 compiled).   Fits the development→drift
          mapping. Frozen to experiments/predictive_value/frozen/dev_betas.json
          + SHA256 in the ledger BEFORE any W6→W7 evaluation runs.
DEV     : W6→W7 deltas, all 410 pairs, LOO-country.   HONESTY LABEL: "development/
          diagnostic evaluation" — NOT blind (§3). This is where Δciv and Δm are
          measured. Event-class counterpart: the A3 perceived-cases set.
UNTOUCHED TEST (frozen now, scoreable later — no genuinely untouched data
          exists inside the repo today, and the plan says so plainly):
          (a) WVS Wave 8 deltas when published — scored under the same frozen
              betas and frozen variant configs, no re-registration;
          (b) EVS 2017 aggregates for countries OUTSIDE the 37-country W6→W7
              set — same frozen betas.
          The scoring script, metric definitions, and frozen-artifact hashes
          are committed before results exist; the protocol file is
          experiments/predictive_value/frozen/untouched_protocol.json.
```

Additional in-repo guard (not blind, but anti-tuning): a **seeded country
split** — 25 of 37 countries as DEV-fit pool, 12 held aside (selected by
`sha256("earth1-pv-holdout-2026-08-17")` seeding, listed in the frozen spec) —
nothing is tuned on the 12, and results are reported on both pools separately.
This bounds within-DEV overfitting; it does not create blindness.

## 3. What has already been seen (cannot be called blind)

Recorded in STATUS and A5/A6 already; repeated here because the ledger requires it:

1. **Per-question W6→W7 MAE and sign outcomes** — inspected across G5 runs
   #1–#7 and the 2026-08-16 diagnostic screen. Therefore: **question selection
   is frozen at all 15** (no dropping), and **sign accuracy on W6→W7 is
   reported but flagged CONTAMINATED** (A6's exact wording).
2. Per-country details exist in `data/g5_results.json` — assume country-level
   partially seen. Hence the country holdout in §2 is labeled "guard", not "blind".
3. The A5 partition, GDELT replay outcomes (A2), perceived replay (A4 pending),
   GOQA/leakage/ablation results — all seen.
4. **Never seen**: W5 numbers (not in repo), W5→W6 deltas, Wave 8, EVS 2017.
5. Contamination direction is honest-by-construction where possible: the
   mapping is *fit* only on W5→W6, which no one has looked at; the design of
   the mechanism, however, was motivated by knowing W6→W7 failed — so even a
   good DEV result is "diagnostic", never "confirmatory". Confirmation waits
   for (a)/(b) in §2.

## 4. Baseline definitions (tier A)

All baselines are evaluated on identical pairs, identical LOO-country folds.

| ID | Baseline | Definition |
|---|---|---|
| A-0 | **No-change** | predicted Δ = 0 for every pair. The reigning champion — current STATUS says endogenous dynamics ≈ no-change. |
| A-1 | **Trend** | predicted Δ(W6→W7) = observed Δ(W5→W6) × interval ratio (per country-question, where W5 exists; pairs without W5 fall back to A-0 and are flagged). Legitimate because W5→W6 is training-era data. |
| A-2 | **Country-statistical** | ridge from static country features (census age structure, Hofstede, log GDP level) → observed Δ, fit LOO-country within DEV. The "simple country/cohort statistical baseline" — no simulation, no dynamics. |
| A-3 | **Development-direct** (= A6 as registered) | drift = β_q · D_rate, sign-constrained ridge fit on W5→W6, frozen; rate-normalized per A6.1. This is both a baseline for Q2 AND the aggregate-level arm of Q1. |

## 5. Q1 — formative-environment channel (flag-gated, default OFF)

Two arms, both fit on W5→W6 only, both frozen before evaluation:

**Arm 1 — aggregate (A-3 above).** Exactly A6/A6.1 as preregistered. No new
physics; a post-hoc additive term on readouts. This runs first and is the
committed deliverable regardless of Arm 2.

**Arm 2 — mechanistic (the mission's developmental-socialization channel).**
`newborn = h·parent + (1−h)·young_cohort_mean + FORMATIVE(country, cohort_year) + noise`
- `FORMATIVE(c, y) = W · D_form(c, y)` where `D_form` is the country's
  development-change vector over the cohort's formative window (birth→18,
  i.e. simulation year y−18..y, from WDI 1990–2024, rate-normalized per A6.1's
  convention), and `W` is a **(9 traits × 3 indicators)** weight matrix.
- `W` is estimated on W5→W6 only, by ridge through the frozen W6 calibration
  weights: predicted question delta = (readout of population with displaced
  cohorts) − (readout without), linearized so the fit is convex; sign
  structure NOT hand-authored per question/country — the only imposed
  structure is the trait-level Inglehart direction already registered in A6
  (development ↑ → traditional-religious traits ↓, self-expression ↑),
  matching "same claim shape as RESPONSE_GAIN".
- Implementation: `generational_tick` gains an optional
  `formative_displacement: Callable[[country_idx, slots, sim_year], dict] | None = None`
  parameter (default `None` → **bit-identical**, proven by pop_hash_full at
  50K before any experiment runs). The callable lives in
  `experiments/predictive_value/dev_channel.py`, activated only by
  `EARTH1_DEV_SOCIALIZATION=1` inside the harness. Production paths never set it.
- Country- and cohort/time-conditioned by construction (c, y arguments).

**Placebo (both arms):** shuffled-development — permute country identities of
the WDI trajectories with a fixed seeded permutation (marginals preserved,
country/time alignment destroyed), same frozen β/W. Real must beat placebo.
Second placebo for Arm 2: formative-window scramble (right country, wrong
cohort window) — separates "country development level" from "what this cohort
actually lived through". Both placebos are in the final report regardless of outcome.

## 6. Q2 — civilization ablation benchmark (tier B / C / C−m)

All variants: identical genesis (pop 50 000, same seed), identical calibration
(computed once on W6, shared), identical question set, identical
`advance_world` step count (7y, dt=30d), identical evaluation pairs. Population
hash asserted identical across variants at t0 (semantic test).

| ID | Variant | Tick configuration |
|---|---|---|
| B | **Earth-1 Individual** | demographic/generational ON, response law ON; `enable_feedback=False, enable_coupling=False, enable_thresholds=False, enable_rewire=False, enable_event_generation=False`, diffusion settle OFF |
| C | **Full civilization** | current `g5_temporal` defaults — everything ON |
| C−diff | no diffusion | C but diffusion settle OFF |
| C−fb | no feedback | C but `enable_feedback=False` |
| C−rw | no rewiring | C but `enable_rewire=False` |
| C−cp | no coupling | C but `enable_coupling=False` |
| C−ev | no endogenous events | C but `enable_event_generation=False` — **with an exercise check**: the harness counts endogenous events actually generated during the C run; if zero, the ablation is reported as "not exercised by this benchmark" (the tenth review's Ring-B finding predicts exactly this) |

Diffusion toggle requires the ONE production-code touch beyond generational.py:
`run_question()` gains `settle_steps: int = <current value>` pass-through
(default preserves today's behavior bit-identically; `0` skips the settle
loop). Proven bit-identical at default before use.

No parameter values change between variants except what disabling logically
requires. Benchmarks each variant runs on:
- **Secular class**: W6→W7 temporal leg (DEV, honesty label per §3)
- **Event class**: A3 perceived-cases event-reaction leg (the one leg where
  dynamics demonstrably act — ratio 0.97 in run #7)
- Q1 arms compose with B and C (B+dev, C+dev) to answer "does the formative
  channel need the civilization, or does it work on a dead population?"

## 7. Success metrics (frozen now)

Per variant, per benchmark class, LOO-country on DEV:

1. **MAE of Δ** (primary — A6's registered primary metric)
2. **Sign accuracy** (flagged CONTAMINATED on W6→W7 per §3)
3. **Heterogeneity accuracy**: within-question Pearson r between predicted and
   observed per-country Δ, averaged over questions (does the model know *which*
   countries move most, not just the average move)
4. **Correlation** of predicted vs observed Δ, pooled (Pearson + Spearman)
5. **Calibration**: regression slope of observed on predicted Δ (1.0 = calibrated)
6. **Uncertainty**: every variant run at seeds {42, 43, 44, 45, 46}; report
   mean ± 95% CI; Δciv and Δm get paired-across-seeds CIs
7. **Headline numbers**: `Δciv = err(B) − err(C)` and `Δm = err(C−m) − err(C)`
   for each mechanism, with CIs. A Δ whose CI includes 0 is reported as
   "no measurable contribution" — not rounded up to a win.

**Registered conclusions space** (no third option invented after results):
`C>B>A` / `B>A, C≈B` / `B≈C≈A`, judged on primary metric with CIs, separately
for secular and event classes. Prediction registered now, before running: the
current program state implies **event class: C>B>A-0; secular class without
dev channel: B≈C≈A-0; secular with dev channel: the open question this
experiment exists to answer.**

## 8. Anti-overfitting mechanics

- `experiments/predictive_value/frozen/spec.json` — full config, dataset
  SHA256s, split lists, seeds, commit SHA, PHYSICS_VERSION — committed before
  first result.
- `experiments/predictive_value/ledger.jsonl` — append-only; every run appends
  {timestamp, commit, config hash, results}. Never rewritten.
- Betas/W frozen to files + hashed before W6→W7 evaluation.
- No question dropping, no metric changes, no partition re-shopping (A5's
  on_failure clause already forbids it). Placebos reported regardless.
- Negative results are results. Production defaults change from NONE of this
  (freeze holds; a winning experimental branch earns a *registered build
  proposal*, nothing more).

## 9. All files that must change

**New (everything lives here):**
```
experiments/predictive_value/
  spec_freeze.py          # writes frozen/spec.json + hashes (run FIRST)
  frozen/spec.json        # generated, committed
  frozen/untouched_protocol.json
  frozen/dev_betas.json   # generated after W5→W6 fit, before evaluation
  baselines.py            # A-0, A-1, A-2, A-3 (A-3 = A6 fit, sign-constrained ridge)
  dev_channel.py          # FORMATIVE(c, y) callable + W fit + both placebos
  variants.py             # B / C / C−m tick-config table (data, not code paths)
  harness.py              # runs variant × benchmark × seed grid; appends ledger
  report.py               # renders REPORT.md from ledger (tables, CIs, failures)
  tests_semantic.py       # disabled-mechanism proofs + same-inputs proofs
  ledger.jsonl            # append-only
  REPORT.md               # generated
```
**Modified (minimal, each with a bit-identical flag-off proof before use):**
- `earth1/wvs_paired.py` — ADD `wave5` dicts to the 15 questions (data
  addition from published W5 aggregates; W6/W7 values untouched — file hash of
  the untouched portions verified by test)
- `earth1/generational.py` — add optional `formative_displacement=None`
  parameter (default None → bit-identical)
- `earth1/engine.py` — `settle_steps` pass-through (default → bit-identical)
- `earth1/advance.py` — forward `formative_displacement` + tick kwargs it does
  not already forward (default → bit-identical)

**Semantic/unit tests (tests_semantic.py):**
- flag-off bit-identity: pop_hash_full equal to pre-change engine for a 50K
  world advanced 12 ticks (all three modified files at defaults)
- B run: assert zero feedback trait deltas, adjacency hash unchanged (no
  rewire), coupling matrix empty, zero endogenous events, zero settle iterations
- all variants: identical t0 pop hash, identical calibration weight hashes,
  identical evaluation pair lists
- placebo integrity: shuffled WDI has identical sorted values per indicator
  (marginals preserved), zero fixed points above chance in the permutation

## 10. Execution order & cost

1. Freeze spec (hashes of everything currently in repo) → commit
2. Compile W5 aggregates → commit (training data lands AFTER the spec freeze
   so the spec can't have been shaped by it)
3. Modified-file changes + bit-identity proofs + semantic tests → commit
4. Fit A-3 β and Arm-2 W on W5→W6 → freeze → commit (no W7 touched yet)
5. Run the full grid on earth1-prime: 12 variants/baselines × 2 benchmark
   classes × 5 seeds ≈ 90 runs at 50K pop — parallel harness, ~est. 2-4h wall
6. `report.py` → REPORT.md with every number, every placebo, every failure
7. Ledger + report committed; STATUS gets one paragraph pointing at REPORT.md

**Stopping point: this plan. Nothing in §9-10 has been executed.**

---

## REQUIRED MISS-RESOLUTION PROTOCOL

> **Do not stop at "the model failed." Your job starts there.**

Every target, tier and gate in this plan is governed by
**BIBLE.md Part XI.A — NO DEAD-END RESULTS** (canonical text; also in
`CLAUDE.md`). A miss against any threshold in this document **starts**
the following cycle; it never ends the work.

```
MISS → VERIFY → DIAGNOSE → RESEARCH → IMPLEMENT
     → CALIBRATE → ABLATE → RETEST → PASS → FREEZE
```

1. **Record the result exactly.** Never hide, soften, delete, or rewrite a bad result.
2. **Verify the instrument first** — ground truth, provenance, units, leakage,
   implementation correctness, persistence, state continuity, metric visibility,
   benchmark design, and whether the tested code is actually the
   production/canonical path.
3. **Explain causally why**, tracing the output back through the code with
   file:line and quantifying which mechanisms, parameters, datasets or missing
   channels account for the error.
4. **Research before inventing** — peer-reviewed literature, authoritative
   technical reports, established simulators, government models, white papers,
   reference implementations, empirical datasets.
5. **Do not assume where established research exists.** Cite the methods
   considered; explain why the selected one applies to Earth-1.
6. **Implement the smallest defensible correction.**
7. **Ablate and run sensitivity** so we know what actually caused the change.
8. **Retest on TRAIN/DEV and iterate** until the predefined gate is met.
9. **Never tune on the final holdout.** Never move a threshold after seeing a
   result. Never manufacture a pass.
10. **Freeze only** after an untouched external holdout or prospective test.

A miss report is incomplete unless it carries: **RESULT → INSTRUMENT →
DIAGNOSIS → RESEARCH → IMPLEMENTATION → ABLATION → RETEST → STATUS**
(see BIBLE.md XI.A.2 for the required contents of each).

The only legitimate terminal exception is a hypothesis demonstrated false by
repeated clean experiments, correct implementation, literature-derived methods,
proper calibration and untouched external evidence — in which case the negative
evidence is preserved and the capability redesigned, never falsified into a pass.
