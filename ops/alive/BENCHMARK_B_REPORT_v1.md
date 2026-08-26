# BENCHMARK B — REPORT v1 (one shot after registered VOID+repair)

Prereg: BENCHMARK_B_PREREG_v1.md @29fa296 + VOID/repair addendum (frozen
before any repaired number). System: canonical Epoch-3 physics v4.1,
200k lab world, 90-day warm snapshot (hash dac2c960…), 30 paired-CRN
runs (5 repeats × {2 controls, covid, gfc, arab, placebo}). The first
scoring pass is archived as INSTRUMENT-DEFECTIVE
(`scoreboard_b_defective.json`): the placebo exposed a noise-rectifying
endpoint jobs statistic; repair = signed paired daily-path statistics
(FTE-year integral / peak excess), frozen pre-rescoring.

## BENCHMARK B RESULT (per event; effects are treatment − paired control, census-scaled persons)

| event | observed (primary source) | Earth-1 treatment effect (CI over 5 repeats) | placebo | direction | magnitude vs LOO-exposure baseline | geography | PASS/FAIL |
|---|---|---|---|---|---|---|---|
| covid_2020 | 255M FTE lost (ILO); +80–97M extreme poverty (WB); 14.9M excess deaths (WHO, diagnostic) | destitution **+21,568** (21,421…21,716); FTE-year +337 (−127…+790); peak excess jobs +1,362 (905…1,829); hope −0.1; excess deaths +1,433 (1,293…1,642); govs-at-risk 31 | destitution +22 (CI incl. 0); FTE-year CI incl. 0 | **4/4 correct** (jobs↓ poverty↑ hope↓ deaths↑) | FAIL — E1 log10-err 6.1 vs baseline 0.19 | REFUSED (repeat Spearman +0.04) | direction GOOD; magnitude FAIL |
| gfc_2008 | +30M unemployed (ILO GET); −1.7 % world GDP (WB) | destitution +1,298 (1,076…1,522); peak excess jobs +1,611 (712…2,509); FTE-year CI incl. 0; hope 0.0 | as above | 2/3 (hope flat = miss) | FAIL — 4.4 vs 0.09 | REFUSED (−0.02) | FAIL |
| arab_spring_2011 | 4 governments fell; displacement 1e6–1e7 (UNHCR) | govs-at-risk +14.8 (13.2…16.0); destitution +486 (255…711); displaced −19 (CI incl. 0) | as above | 2/3 (displacement miss — no net migration response) | FAIL — 6.5 vs 0.28 | REFUSED (−0.02) | FAIL |
| placebo | ≈ 0 | all repaired channels CI incl. 0 or < 5 % of smallest treatment | — | — | — | — | **PASS** |

Gates: direction 80.0 % pooled → **ACCEPT (≥75), not GOOD (<85)**;
magnitude **FAIL** (median log10-err 6.1 vs baseline 0.19);
proportionality: order covid > gfc > arab **CORRECT** on FTE-year and
overwhelming on destitution (21,568 ≫ 1,298 ≫ 486) but the frozen
min-gap>2σ criterion FAILS on the noisy jobs statistic → **FAIL**;
placebo **PASS**; coverage 53 % (<70) → **FAIL**; geography **REFUSED**
for all events (as the 0.8 noise floor predicted).

**BENCHMARK_B_OVERALL: FAIL** (2 of 5 gates; frozen criteria, no post-hoc changes).

## Does the evidence show Earth-1's dynamic machinery adds measurable value on real perturbations despite Benchmark A's static failure?

**Partially — a real causal channel exists, at the wrong amplitude.**
What no statistical baseline produces and Earth-1 demonstrably does:
placebo-clean, correctly SIGNED and correctly ORDERED cascades through
material hardship → destitution (covid ≫ gfc ≫ arab at ~1000:1 over
placebo, tight CIs), government legitimacy (31 at-risk under covid vs
0.8 placebo), and psychology (hope falls under covid only). That is
genuine event→consequence machinery. What fails: (1) AMPLITUDE — global
effects are 4–6 orders below the anchors (a trivial exposure baseline
crushes Earth-1 on magnitude); (2) the EMPLOYMENT channel is
indistinguishable from chaos noise at 200k/registry dose (FTE-year CIs
straddle 0 while localized high-dose probes like India show −24.8 pp —
the response exists but drowns at scenario dose); (3) known missing
mechanisms bound the score by construction: no epidemiological channel,
no informal-economy buffer (Bible IV.5's own named Phase-2 first move),
no displacement response (arab migration ≈ 0); (4) replicate noise is
heavy-tailed (coverage 53 %). Per the founder's interpretation tree this
is "B weak": failures plausibly originate in dose/scale calibration,
missing material channels, and population conditioning — not (on this
evidence) in the sign-structure of the dynamic laws, which passed every
attribution test the battery could pose.

## C2 READINESS

- Empirical conditioning data available: WVS-7 v6.0 microdata (97,220
  respondents, weights, cohort cells already built), GSS + ANES raw
  archives (untouched, in `rawdata/`), genesis census marginals +
  country context covariates (MRP frame).
- Permitted conditioning variables (gate-clean): age, education,
  income/material class, urban/rural, employment, social class,
  town size, country/locality.
- Banned/leaky: religiosity (Q164), ideology (Q240), marital,
  household_size, children, immigrant (adjacency-gate record); no
  benchmark-adjacent target-derived feature enters genesis.
- Existing genesis correlations: traits are conditioned on demography/
  culture/region at genesis (Grounding Stack layers), but measured
  age-gradients in psychological state are ~absent (Benchmark-A-v2
  cohort direction 50.5 %; R1/GSS cohort fit worse than persistence).
- Missing empirical correlations: P(psych/social/material state | age,
  education, income, urbanicity, employment, locality) with preserved
  within-cell heterogeneity; cross-item dependence beyond independence.
- Proposed conditional population model: estimate conditional latent
  DISTRIBUTIONS (not answers) from admissible TRAIN evidence; sample
  agents from them at genesis; keep stochastic individuality and
  endogenous evolution; adjacency gate as guardrail.
- Physics law changes required: NONE (population construction only) —
  but under VALIDATION_INHERITANCE_POLICY it is a **class-2 substrate
  change**: minimum validation = Stage-A health regression, KA that the
  dynamic laws are byte-identical, Benchmark-A-v2 development scoring on
  the new substrate, and dose-response regression before any epoch.
- C2 ready for preregistration: **YES**.

STOP — founder ruling point. /ask remains locked. Nothing was tuned
against Benchmark-B outcomes; Epoch 3 untouched.
