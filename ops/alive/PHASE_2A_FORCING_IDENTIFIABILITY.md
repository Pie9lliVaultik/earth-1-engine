# PHASE 2A — FORCING / DOSE IDENTIFIABILITY (registration; development-only)

Founder GO 2A. B-v1 is CONSUMED (development evidence). No Epoch-3
change, no C2 execution, no new mechanisms, lab worlds only.

## 0. SCORER UNITS DEFECT FOUND FIRST (2A step 1, before any sweep)
`genesis.census_weights` is normalized to MEAN 1.0, so every snapshot
global figure is in AGENT units (population-true shares × N_agents);
the B-v1 magnitude gate compared those to world-person anchors without
the persons-per-agent factor (8.3e9/200k = 41,500). The frozen B-v1
verdict (FAIL) stands unchanged; the magnitude DECOMPOSITION changes:

| channel | B-v1 reported | corrected (×41,500) | anchor | corrected log10 err |
|---|---|---|---|---|
| covid jobs FTE-year | 337 (agents) | **14.0M FTE** (CI −5.3M…32.8M) | 255M (ILO) | 1.26 LOW, noise-bound (placebo 17.8M same order) |
| gfc peak excess unemployed | 1,611 | **66.9M** | 30M (ILO) | **0.35 — near-right** (baseline 0.087 still closer) |
| covid destitution | 21,568 | **895M** | 80–97M (WB) | **1.0 OVERSHOOT** |
| covid excess deaths (hardship channel only) | 1,433 | **59.5M** | 14.9M (WHO) | 0.60 OVERSHOOT (with NO epi channel) |
| arab displaced | −19 | ≈0/negative | 1e6–1e7 | CHANNEL non-responsive |
The "4–6 orders" statement in BENCHMARK_B_REPORT_v1 is superseded by
this table (defect: scorer units, not physics). Key implication: jobs
LOW while destitution/deaths HIGH ⇒ no single dose scalar can repair
magnitude — the hardship-conversion gain is imbalanced (the IV.5
informal-buffer signature) and the jobs signal is variance-limited.

## 1. B-v1 error decomposition (per failed outcome)
| outcome | classification(s) | executable-path support |
|---|---|---|
| covid jobs magnitude | FINITE_SAMPLE_NOISE + INPUT_SCALE(?) | placebo FTE same order as treatment; one-shot firm_damage vs year-scale rolling closures (semantics table §2); dose-response decides |
| covid destitution overshoot | RESPONSE_GAIN + INPUT_SCALE(duration) | permanent trade_shock (+18 % cost forever, `branch.apply` has no reversal path) + static informal floor (`life.py INFORMAL`, no counter-cyclicality/saturation) |
| covid deaths overshoot | RESPONSE_GAIN + MISSING_CHANNEL | hardship mortality alone already ×4 the WHO total; the epi channel is absent as a scenario input (health/mobility infection machinery exists but no scenario trigger) — NOT input scale |
| gfc hope flat | RESPONSE_GAIN(psych) / UNKNOWN | forces press h=500d ⇒ near-constant; hope moved only under covid's larger dose |
| arab displacement ≈0 | CHANNEL under-exercised | migration exists (`institutions.class_tick` → calmest-list destinations) but is driven by deprivation/war, not by the scenario's psych forces — NOT input scale until proven |
| coverage 53 % | FINITE_SAMPLE_NOISE (heavy-tailed chaos) | FSLE +0.22/d; 5 repeats |
| geography | POPULATION_SUBSTRATE + FINITE_SAMPLE_NOISE | 0.8 noise-floor verdict |

## 2. Forcing semantics (registered; nothing changed)
| parameter | unit/semantics | target | duration | recurrence | state changed | downstream consumers |
|---|---|---|---|---|---|---|
| `forces{...}` | Memory with force signature; daily press = salience×sig×0.02 | scenario scope | decays 2^(−t/persists_days) (covid h=900 ⇒ ~constant over 365d) | one memory, rehearsable | stored forces of scope | psychology → targets → everything |
| `firm_damage` | ONE-TIME subtraction from firm_health | firms in hit countries | instantaneous; recovery drift +0.004·(0.8−h)/day (~months) | none | firm_health → failure hazard → layoffs | jobs → wealth → deprivation |
| `trade_shock` | cost-of-living multiplier | scope | **PERMANENT (no reversal exists)** | none | life.cost | deprivation → destitution/mortality |
Real events by contrast: rolling multi-month closures (OxCGRT), transient
trade/cost disruption, epidemic mortality. The one-shot/permanent
mismatch is documented; historical plausibility is what §3–4 test.

## 3. Exposure anchors (INPUT vs EVALUATION; a number never serves both)
- INPUT/CALIBRATION: OxCGRT stringency duration (~9–12 months of high
  stringency 2020) → forcing schedule length; ILO working-hours PATH
  shape (quarterly 2020: −5.4 %, −18.2 %, −7.2 %, −4.6 %) → dose
  schedule shape ONLY (labelled INPUT; its annual total 8.8 % ≈ 255M
  FTE remains EVALUATION and is never fit); GFC: US business
  bankruptcies +~50 % 2008–09 and world trade −12 % 2009 → firm_damage/
  trade scale class (INPUT).
- DOWNSTREAM/EVALUATION (sealed from calibration): 255M FTE total,
  +80–97M poverty, 14.9M excess deaths, +30M unemployed, displacement.
- Not independently calibratable: Arab-Spring psych forcing magnitude
  (no external exposure unit for "identity +0.40") — recorded as such.

## 4. Dose-response experiment (development; frozen before running)
Warm snapshot dac2c960… (reused); 180-day horizon; repeats r=0..2 with
CRN seeds 977·13+r; controls = the existing B-v1 control365 daily paths
truncated to 180d (same seeds, same snapshot). Arms (covid-family
material channel; scenario schedule driven by the dev harness on
UNCHANGED physics inputs):
  A1 one-shot firm_damage 0.10 · A2 0.35 (=B-v1) · A3 0.70
  A4 sustained: 0.35 total as daily 0.35/90 over 90 d
  A5 sustained: 0.70 total as daily 0.70/180 over 180 d
  A6 trade transient: registry covid but cost ×1.18 reverted at day 90
  A7 forces-only (no material shock)
  A8 full registry covid (B-v1 replica, 180 d window)
Measured per arm: affected population, jobless path (FTE + peak),
destitution, wealth median, FEAR/hope, legitimacy, cascade firings,
clamp/saturation, recovery slope after forcing ends, monotonicity in
dose, placebo reference. Output: Y=f(D) curves per outcome family →
per-channel verdict {DOSE_CALIBRATABLE | RESPONSE_UNDERPOWERED |
CHANNEL_ABSENT}. Scale-vs-bias discipline: repeats reduce variance
only; no scale claim without measured scaling.

## 7. Benchmark-B-v2 candidate events (identified, outcomes SEALED)
Ukraine war 2022 (conflict/energy), Türkiye–Syria earthquake 2023
(disaster), Sri Lanka 2022 default (sovereign/economic), COVID vaccine
rollout 2021 (recovery-side), 2014–16 oil crash (commodity). ≥2 new
domains available. No outcome figures fetched or stored in this repo;
they enter only inside a future frozen v2 prereg.

## 5. DOSE-RESPONSE RESULTS AND VERDICTS (24 runs complete; data/benchmark_b/dose_*.json)

180-day arms, 3 CRN repeats, persons = weighted-agents × 41,500. FTE vs the paired control path; destitution/hope are arm end-levels (forces-only arm A7 is the material-channel reference).

| arm | forcing | FTE-180d | destitution end | hope end | cascades |
|---|---|---|---|---|---|
| A1 | one-shot fd 0.10 | −2.4M (noise) | 3.50e9 | 0.584 | 9,805 |
| A2/A8 | one-shot fd 0.35 (= B-v1) | +10.0M | 3.51e9 | 0.582 | 9,799 |
| A3 | one-shot fd 0.70 | +8.7M | 3.52e9 | 0.575 | 9,827 |
| A4 | 0.35 spread over 90 d | +13.1M | 3.50e9 | 0.575 | 9,797 |
| A5 | 0.70 spread over 180 d | +9.3M | 3.51e9 | 0.573 | 9,798 |
| A6 | registry covid, cost REVERTED at d90 | +15.4M | **2.69e9** | 0.628 | 8,913 |
| A7 | forces only (no material shock) | +4.3M | **2.66e9** | 0.641 | 8,120 |

Findings:
1. **The employment response is DOSE-FLAT.** Firm damage 0.10 → 0.70,
   one-shot or sustained, moves FTE only within the noise band
   (−2.4M…+15.4M); even the largest sustained dose yields ~9M FTE vs
   the 255M anchor. Y=f(D) is saturated at ~1.3 orders below reality:
   the firm→layoff→rehome chain re-absorbs labour too fast for ANY
   plausible dose. **Verdict: RESPONSE_UNDERPOWERED (+ FINITE_SAMPLE_
   NOISE)** — not dose-calibratable.
2. **Destitution is a cost-of-living phenomenon, not a firm-damage
   one.** Removing the permanent trade_shock (A6 vs A2) removes
   ~0.82e9 of destitution — the entire material-arm delta — while firm
   damage contributes ≈ nothing (A1≈A2≈A3). The PERMANENT cost
   multiplier is an input-semantics defect worth roughly the whole
   material overshoot. Residual overshoot lives in the hardship-
   conversion gain (static informal floors). **Verdict: INPUT_SCALE
   (duration semantics) + RESPONSE_GAIN.**
3. **The psych forcing alone (A7) sustains a large hardship state**
   (destitution 2.66e9 end-level, hope −): with B-v1's placebo-clean
   attribution this says the FEAR/ECON memory press couples strongly
   into material life; its gain is part of the θ-inference target, not
   a dose knob. **Verdict: RESPONSE_GAIN (θ).**
4. Deaths: RESPONSE_GAIN + MISSING_CHANNEL (epi absent) — unchanged.
   Displacement: **CHANNEL_ABSENT as a scenario response** (≈0 under
   every dose). Coverage/geography: FINITE_SAMPLE_NOISE + substrate.

## ANSWER — how much of B's magnitude failure is repairable by legitimate forcing calibration alone?
**A minority.** One semantics fix (transient instead of permanent cost
shock) removes most of the destitution overshoot; nothing in the
plausible dose range repairs the jobs shortfall (dose-flat), the
hardship gains, the missing death channel, or displacement. This
confirms the founder's caution and the inference-architecture ordering:
adapters fix u_t semantics; θ-posterior inference fixes gain balance;
channels must be built where absent; the population substrate carries
the rest. Phase-2A complete; nothing tuned; Epoch 3 untouched.

## PHASE 2B READINESS
informal buffer: PARTIAL (static floors; counter-cyclicality/saturation
missing) · wealth brakes: ABSENT · epidemiology: PARTIAL machinery, no
scenario channel · displacement: PARTIAL mechanism, unresponsive to
scenarios · response laws to investigate under θ-inference: rehome
re-absorption rate, hardship→destitution/mortality gains, memory-press
material coupling.

## C2 READINESS (design only)
status: designed at architecture level (EARTH1_INFERENCE_ARCHITECTURE
§4–5); data: WVS-7 microdata + GSS/ANES archives + census frames;
axes: age, education, income, employment, household, urbanicity,
locality (gate-clean); executable: NO (awaiting founder ruling).

## FUTURE BENCHMARK B v2
candidates identified across ≥2 new domains (Ukraine 2022, Türkiye–
Syria 2023, Sri Lanka 2022, vaccine rollout 2021, oil crash 2014–16);
outcome data sealed: YES (never fetched into the repo); adequate
domains: YES.
