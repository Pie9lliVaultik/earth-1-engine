# 0.8 EMPIRICAL TARGET REGISTRY — conviction/force-persistence evidence

Deliverable B (founder ruling). FROZEN before any candidate-law
result is inspected. Every target records source, construct,
timescale, moment, uncertainty, Earth-1 mapping, limitations, and
role (CALIBRATION = the law is fit against it; VALIDATION = the law
is scored against it out-of-fit; QUALITATIVE = structural constraint).
Timescales are kept separate; no daily coefficient may be inferred
from multi-year waves.

## T1 — persuasion-effect decay (DAYS→WEEKS) — CALIBRATION

- Source: dynamic-persuasion literature (Coppock and colleagues;
  partisan-media decay studies, Cambridge PSRM).
- Population/context: US adults, survey experiments + field ads.
- Construct: policy/candidate attitude shift after a persuasive
  message (informational shock, no lived-state change).
- Moment: effects decay to ≈50% of their initial size over ≈10 days,
  then plateau (detectable to ≈1 month). Uncertainty: half-life
  band 5–15 days; plateau fraction 30–60%.
- Earth-1 mapping: A5-style tau map for INFORMATION-ONLY force
  perturbations (feed/news-mediated, no material change): admissible
  population half-life 5–15 days with a nonzero residual at day 30
  (0.2–0.6 of initial).
- Limitations: US-centric; survey attitudes ≠ 8-channel forces;
  message-scale shocks only.

## T2 — collective fear after a major threat event (WEEKS→YEARS) —
VALIDATION

- Source: post-9/11 population studies (NEJM 2001 national survey;
  NYC longitudinal PTSD series; reviews PMC3386850, PMC8533613).
- Construct: population prevalence of acute stress / fear symptoms
  after a collective threat.
- Moment: acute symptom prevalence falls ≈2/3 within the first
  1–3 months (17%→6% between months 2 and 3); a long tail then
  halves over 1–3 years (9.6%→4.1% over ~3y; ~89% of baseline cases
  remit by year 4). Uncertainty: fast-phase half-life 3–8 weeks;
  tail residual 15–45% of peak at 1 year.
- Earth-1 mapping: FEAR-channel population response to an event-scale
  shock (memory/chronicle-mediated): two-component decay — fast
  weeks-scale component plus a persistent tail; NEITHER 1-day
  erasure NOR permanent saturation is admissible.
- Limitations: symptom prevalence ≠ mean fear level; single-event
  literature; western samples.

## T3 — lived-state shock persistence: unemployment (MONTHS→YEARS,
incomplete) — VALIDATION

- Source: Lucas, Clark, Georgellis & Diener 2004 (SOEP, 15y,
  24k persons); Lucas 2007; bereavement SOEP series.
- Construct: subjective well-being after job loss (a MATERIAL shock,
  not an informational one).
- Moment: large immediate drop; recovery toward baseline over 2–5
  years; adaptation INCOMPLETE — the set point shifts permanently
  (a substantial fraction of the initial drop, order 20–50%,
  persists even after re-employment). Bereavement: near-full
  adaptation over ~1–5 years.
- Earth-1 mapping: outcome-probe class experiments — force/mental
  response of a shocked cohort must persist at month scale, recover
  over model-years, and retain a residual; maps through
  mental/mental_setpoint and the FEAR/DESIRE channels of hit
  cohorts.
- Limitations: SWB ≠ force channels; German panel; annual waves
  cannot resolve sub-month shape (T1/T2 own that regime).

## T4 — within-person attitude stability (YEARS) — VALIDATION

- Source: Ansolabehere, Rodden & Snyder 2008 (multi-measure
  correction); Freeder et al. 2018 reanalysis.
- Construct: policy-attitude test-retest across panel waves.
- Moment: single-item wave-to-wave r ≈ 0.43; measurement-corrected
  multi-item index r ≈ 0.61 (rising toward 0.7–0.8 with more items)
  over 2–4 years. Uncertainty band for the latent construct:
  r ∈ [0.55, 0.85].
- Earth-1 mapping: within-agent force-channel autocorrelation at a
  1–2 model-year lag in a no-news world: r ∈ [0.5, 0.9] on
  non-railed channels.
- Limitations: political attitudes only; panels condition on
  survival/response.

## T5 — population opinion variance stability (YEARS→DECADES) —
QUALITATIVE (hard constraint)

- Source: GSS/WVS repeated cross-sections (opinion distributions
  maintain interior mass and stable spreads across decades; no item
  drifts to unanimity absent real social change).
- Earth-1 mapping: in a 365-day no-news world, per-channel sd must
  not collapse (>50% loss) or explode (>100% gain) from genesis, and
  saturation shares (>0.95 or <0.05) must stay bounded (< 20% per
  channel) — measured by the exact 0.8-A census.
- Role: the anti-railing constraint. QUALITATIVE because the mapping
  from survey scales to force units is loose; the DIRECTION is not.

## T6 — attitude certainty moves BOTH ways (DAYS→WEEKS) —
QUALITATIVE (hard constraint)

- Source: attitude-strength literature (Petty & Krosnick tradition;
  consensus/repeated-expression experiments raising certainty;
  counter-argument and ambivalence manipulations lowering it).
- Earth-1 mapping: α must be observably reducible by disagreement
  exposure in-model (an agent moved into a disagreeing neighborhood
  must show falling α within weeks), and no absorbing state at
  either bound may exist in a 365-day run.

## T7 — social influence exists and averages (MINUTES→DAYS lab
scale) — QUALITATIVE

- Source: Friedkin–Johnsen small-group validation experiments;
  Lorenz et al. 2011 (social information narrows estimate variance);
  Moussaïd et al. opinion-influence experiments.
- Earth-1 mapping: the averaging/social-learning term must remain
  ACTIVE for typical α (contribution bounded away from zero for the
  population median agent); heterogeneous susceptibility across
  agents is expected structure.

## T8 — depolarization-intervention decay (WEEKS) — supporting T1

- Source: depolarization megastudy literature (intervention effects
  on affective polarization persist partially at ~2–4 weeks).
- Earth-1 mapping: consistent with T1's transient class; no separate
  band registered (avoid double-counting).

## Registered scoring rule

Candidates are FIT only against T1 (and optionally T2's fast phase).
T2 tail, T3, T4 are out-of-fit VALIDATION scored after freezing each
candidate's coefficients. T5–T7 are pass/fail structural constraints
via the 0.8-A battery. A candidate that requires refitting after
seeing validation results is a NEW candidate and must re-register.
Acceptable-uncertainty bands above are final as of this commit.

Sources: [Cambridge PSRM dynamic persuasion](https://www.cambridge.org/core/journals/political-science-research-and-methods/article/dynamic-persuasion-decay-and-accumulation-of-partisan-media-persuasion/51C59694004133240B7B91032831A48A) · [NEJM 9/11 stress survey](https://www.nejm.org/doi/full/10.1056/NEJM200111153452024) · [PTSD post-9/11 review](https://pmc.ncbi.nlm.nih.gov/articles/PMC3386850/) · [Lucas et al. 2004 SOEP unemployment](https://journals.sagepub.com/doi/abs/10.1111/j.0963-7214.2004.01501002.x) · [Lucas 2007 set-point](https://journals.sagepub.com/doi/abs/10.1111/j.1467-8721.2007.00479.x) · [Freeder et al. 2018 attitude stability](https://calgara.github.io/Pol157_Spring2019/Freeder%20et%20al.%202018.pdf)
