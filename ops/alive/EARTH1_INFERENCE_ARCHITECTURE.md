# EARTH-1 INFERENCE ARCHITECTURE (planning only — nothing implemented; Epoch 3 untouched; /ask locked)

Governing model: x_{t+1} = F_θ(x_t, u_t, ε_t); y_t = H_φ(x_t) + η_t.
Earth-1 supplies F (the living transition engine — the expensive part).
The measured failures of Benchmarks A and B decompose exactly onto the
four inference objects the predictive-ABM literature names as the
unsolved surround: x₀ (latent population state), H_φ (measurement),
θ (dynamic parameters), u_t (forcing). This document plans those four
systems plus channels, assimilation, and the validation ladder.

## 1. WHAT EARTH-1 ALREADY HAS (mapped to the seven layers)

| layer | status | evidence in-repo |
|---|---|---|
| L1 population truth | **PARTLY BUILT** — 194 countries with census marginals, 443 regional profiles, households/firms/typed social fabric, income/education/urban axes, census weights | `genesis.py`, `regions.py`, `fabric.py`, `life.py`; floor-stratified sampling documented |
| L2 latent human state | **MISSING** — forces/traits drawn from country norms + noise; no inferred conditional structure (A-v2: cohort gradient 50.5 %) | `genesis.py` Grounding Stack; A-v2 scoreboard |
| L3 physics F_θ | **BUILT & mechanically validated** — canonical loop, posthumous invariant, episode-entry cascades, open-loop overlay; ~102 constants, ~52 unsourced (Bible R5) | Stage A/B/C, PF-DECAY-2, H-CASCADE-1, 0.8 Stage H; provenance registry |
| L4 forcing u_t | **CRUDE** — Scenario{forces, one-shot firm_damage, PERMANENT trade_shock}; semantics documented, never empirically mapped | PHASE_2A §2; dose-response sweep running (diagnostic) |
| L5 domain channels | epidemiology PARTIAL (infection/import machinery, no scenario channel); informal economy PARTIAL (static tier floors; not counter-cyclical, no saturation); displacement PARTIAL (migration exists, not scenario-driven); finance ABSENT; wealth brakes ABSENT | PHASE_2A §1; `life.py:102`, `mobility.py:177-193`, `institutions.py:346` |
| L6 assimilation | **DESIGN-ONLY** — `assimilate.py` has an unemployment likelihood; the 2015 timeline + GDELT driver table were never built | BIBLE §IV.8, Phase 5; `timeline.py` |
| L7 forecast machinery | **BUILT** — full-clone branches, CRN paired controls, ensembles, consequence extraction, placebo discipline | `branch.py`, `consequences.py`, Benchmark B harness |

Also already banked: the mean-preserving calibration layer with leakage
contracts (A-v2, mechanically E3), the validation-inheritance policy,
the adjacency gate, the frozen-holdout discipline, and one hard-won
negative each for "readout can rescue structure" (A-v2, R1/GSS) and
"one dose scalar can rescue magnitude" (2A units-corrected table:
jobs 1.26 orders LOW & noise-bound, destitution ×10 HIGH, deaths ×4
HIGH, GFC peak ~right — mixed signs ⇒ gain imbalance, not scale).

## 2. WHAT BENCHMARK A PROVED IS MISSING
x₀ and H: the population lacks empirical conditional structure
P(psych/social/material | demographics, geography) — age gradients at
coin-flip, joint dependence ≈ independence once marginals are fair,
zero-shot transfer nil — and the current H (26 linear features →
sigmoid) cannot conjure structure the state does not contain. The
calibration architecture (level from data, structure from agents) is
proven and keeps.

## 3. WHAT BENCHMARK B PROVED IS MISSING
u_t and parts of L5, plus θ amplitude balance: the causal chain exists
(placebo-clean, signed, severity-ordered — the part most ABMs never
demonstrate), but forcing is a hand-set scalar with wrong duration
semantics, hardship→destitution/mortality gains are imbalanced, the
employment response is variance-limited at 200k, and epi/displacement/
finance outcomes are absent by construction.

## 4. EMPIRICAL POPULATION PLAN (C2+ → Layer 1)
Data available now: WVS-7 microdata (97,220 × weights, on prime), GSS
1972–2024 and ANES 2024 archives (untouched, `rawdata/`), genesis
census marginals + country context frame, regional profiles, ILO/WB
aggregates already in genesis tables. Method ladder to evaluate on
TRAIN geography: current floor-weighting (baseline) → IPF/raking on
{age × education × income × urbanicity} per country → GREG/calibration
weighting → combinatorial/annealing synthesis for small units;
selection by held-out marginal + joint reproduction (never by
benchmark items). Output: agents whose OBSERVABLE joints are real.
Physics change: NO (genesis construction). Affected: `genesis.py`,
new `earth1/popsynth/`. Burden: hours per world at 200k–4M.
Validation: class-2 substrate change — Stage-A regression, dynamics-
unchanged KA, A-v2 dev rescoring, dose-response regression.
Improves: A (directly), B (indirectly via heterogeneity of exposure).

## 5. LATENT-STATE INFERENCE PLAN (Layer 2 — the missing breakthrough)
Design: z_i ~ P(z | country, age, education, income, employment,
household, urbanicity); answers ~ P(a_q | z, country, time). Estimate a
categorical latent-factor/IRT layer on WVS/EVS (+GSS/ANES for US
depth), with explicit country/time non-invariance terms (partial
invariance; item intercept/loading shifts). Map z → Earth-1 state ONLY
through registered semantic bridges (e.g. z-dimension "insecurity" →
FEAR baseline; "traditional–secular" → CULTURE offset), never item-wise.
Gate discipline unchanged: no benchmark-adjacent axis enters genesis.
Holdouts: questions (frozen A-v2 confirmation stays consumed → new
sealed items), respondents, countries, and the final wave. Physics
change: NO (state initialization + measurement layer). Affected:
new `earth1/latent/`, `calibration.py` (H becomes the registered z-map).
Burden: model fitting on ~1M response rows — cheap next to sim time.
Validation: A-v2-style dev scoring on the new substrate + held-out
generalization; the gates finally have a substrate that could pass them.
Improves: A (directly), B (psych-channel amplitudes).

## 6. DYNAMIC PARAMETER INFERENCE PLAN (θ — Layer 3)
First: inventory the calibratable subset vs structural constants
(start: relax, dyadic μ/k/gain, memory press 0.02 & half-lives,
cascade slopes (already AUTHORED-flagged), informal floors, recovery
drifts, hardship-mortality gain — est. 15–25 parameters; the other ~80
stay structural/frozen). Method ladder: moment-matching ABC on banked
cross-sectional + event-response moments (available NOW without a
timeline) → neural posterior/ratio estimation on historical trajectory
windows (REQUIRES the driver table + timeline) → active/sequential
acquisition for sample efficiency → multi-fidelity: 20k (0.13 s/day)
for search, 200k (4 s/day) for inference, 4M (28 s/day) for
confirmation — with a REGISTERED scale-transfer test at each promotion
(our own evidence: genesis hashes differ across machines at 4M, the
noise-floor slope, and the literature's warning that agent count is not
accuracy). Output: p(θ | D) — an ensemble of plausible physics, ending
hand-picked configurations. Physics change: NO new laws; parameter
values become posterior-driven (each adoption = a registered candidate
under the inheritance policy). Burden: the dominant compute line
(thousands of 200k-world runs; prime-sized). Improves: B (amplitude
balance), A (secondary).

## 7. REAL-EVENT FORCING PLAN (u_t — Layer 4)
Registered exposure→forcing adapters per domain, INPUT/EVALUATION
separation enforced by the leakage contract already built for A-v2:
pandemic: OxCGRT stringency path + mobility → time-varying closure
schedule (firm_damage/day and cost path with REVERSAL — the permanent
trade_shock semantics is a documented defect of the current adapter);
financial: credit/bankruptcy indices → firm_health shock distribution;
conflict: UCDP/ACLED intensity → war/displacement forcing; contention:
MEC/ACLED onset (the cascade benchmark preregistration already frozen).
The running dose-response sweep (A1–A8) is the diagnostic that bounds
what adapters must deliver: it will state, per channel,
DOSE_CALIBRATABLE / RESPONSE_UNDERPOWERED / CHANNEL_ABSENT.
Physics change: NO (adapters produce inputs). Improves: B directly.

## 8. MISSING-CHANNEL PLAN (Layer 5 — 2B queue, not built now)
epidemiology: PARTIAL → scenario-triggerable outbreak using existing
infection machinery (new channel = physics, class 2); informal economy:
PARTIAL → counter-cyclical + saturating + 2020-mode (IV.5; class 2);
displacement: PARTIAL → conflict/deprivation-driven flows with
corridors (class 2); finance: ABSENT (class 3 when attempted); wealth
brakes: ABSENT (class 2). Each gets its own registration, dose-response
and inheritance analysis; none proceeds because a test wants green —
only because reality has the pathway and a B-v2 event exercises it.

## 9. DATA-ASSIMILATION PLAN (Layer 6)
Prerequisite: the GDELT/macro driver table + 2015 timeline (Phase 5,
never built) so there is a y_{1:t} to assimilate. Ladder: ensemble
Kalman on aggregate continuous state (unemployment first — the
`assimilate.py` likelihood exists) → particle/hybrid where
non-Gaussian → likelihood-based latent recovery where H is tractable
(the PNAS-Nexus split: DA for aggregates, likelihood for individual
latents). Hard separations, registered: STATE correction (allowed,
logged, epoch-preserving) ≠ PARAMETER learning (θ program, §6) ≠
PHYSICS change (epoch policy). Never fabricates individual histories:
corrections act on ensemble weights/aggregate nudges, not on named
agents' pasts. Improves: the "synthetic present" cap on every claim.

## 10. MULTI-FIDELITY COMPUTE PLAN
Measured costs: 20k ≈ 0.13 s/day · 200k ≈ 4 s/day · 4M ≈ 28 s/day
(uncontended, prime/CCX33). Budget shape: θ-inference dominates
(≈10³–10⁴ × 200k-world-years → weeks on prime; active designs cut it);
population synthesis and latent fitting are cheap; assimilation is a
daily 4M step + ensemble (fits the 60 s daemon period at ~10-member
ensembles on prime). Scale-transfer is TESTED at every promotion, never
assumed.

## 11. UNTOUCHED VALIDATION PLAN
Consumed forever: GOQA-40 + the 98-item A-v2 confirmation set; COVID/
GFC/Arab-Spring outcomes; the v1 question holdout. Sealed and
available: B-v2 events (Ukraine 2022, Türkiye–Syria 2023, Sri Lanka
2022, vaccine-rollout 2021, oil crash 2014–16 — outcomes never fetched
into this repo); WVS/EVS Trend + next wave (licence-gated); GSS/ANES
archives (in estate, untouched); future MEC/ACLED windows (cascade
benchmark prereg frozen). The ladder becomes ROLLING-ORIGIN once the
timeline exists: calibrate on window → freeze at T0 → ensemble futures
→ reveal T1 → score vs baselines; before then, event-based one-shot
confirmations with sealed outcomes remain the instrument.

## 12. MINIMUM BUILD ORDER (each step registered, one-shot validated)
1. **2A verdicts land** (running) — closes the forcing diagnosis with
   no build. 2. **C2+ population synthesis + latent layer (L1+L2)** —
   the substrate everything else initializes from; A-v2 dev rescoring
   is its meter. 3. **Forcing adapters (L4)** for pandemic + financial
   with input/eval separation — B's cheapest legitimate repair.
   4. **θ moment-matching posterior (L3, phase 1)** on banked moments —
   no timeline needed. 5. **Driver table + 2015 timeline (Phase 5)** —
   unlocks trajectory SBI + assimilation + rolling-origin validation.
   6. **Assimilation loop (L6)** — unemployment first. 7. **2B channels
   (L5)** as B-v2 events demand them. 8. **B-v2 one-shot** on sealed
   events; then the rolling-origin ladder replaces event benchmarks.

## FINAL ANSWER — shortest technically defensible path
Build the inference surround, in this order: empirically synthesized
population with an inferred latent human-state layer (fixes x₀ and H —
what A measured), registered exposure→forcing adapters (fixes u_t —
what B measured), a posterior over the ~20 genuinely calibratable
parameters via multi-fidelity simulation-based inference (fixes θ's
amplitude balance), then the historical timeline + data assimilation so
the world tracks reality instead of drifting from a synthetic genesis —
validated at every step by the rolling-origin ladder on sealed, untouched
outcomes. Earth-1's engine already passed the tests that kill most
ABMs (attribution, placebo, ordering, mechanical calibration); what it
lacks is not another force law but knowledge of where the real world
is, who is actually in it, and how hard reality pushes. That is an
inference problem, every component has an established method, and the
estate already contains the data, the discipline, and the compute to
build it.
