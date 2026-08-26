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
