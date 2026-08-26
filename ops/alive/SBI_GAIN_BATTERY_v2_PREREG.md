# SBI GAIN BATTERY v2 — PREREG (frozen before any v2 sim runs)
2026-08-27. MISSION v2 parallel track 2: determine whether hardship
mortality response (and the other 2A gain parameters) can become
ELIGIBLE EXPERIENTIAL-LEARNING PARAMETERS rather than hand-tuned
constants. v1 verdicts stand (hardship/informal weakly identified at
90 d / 600 sims); v2 upgrades the observation design and sim bank —
"if a parameter cannot be identified from current observables, design
better observables."

## Changes vs v1 (registered)
- Fidelity: 200k ONLY (the cliff requires it for the gains), horizon
  90 → 180 days.
- Training bank: 600 → 2,000 sims (SBC 200 held out ⇒ fit on 1,800).
- New candidate summaries (harness-side only, no canonical change):
  deprivation_p10_end, deprivation_p90_end, cum_starved,
  cum_weather_deaths, cum_war_deaths, deaths_late_half (cumulative
  deaths in days 91–180 — gain effects compound with deprivation),
  deprivation_late_slope; plus every v1 candidate.
- Same 6-θ surface and priors (A1); same probe (A4.1) at day 10.
- Fresh sealed θ* v2 bundle (5 truths, OS entropy, hash committed
  before inference); v1 truths are consumed and never reused.
- Screen: same OAT design at 200k×180d (13 configs × 3 CRN seeds +
  10-seed noise pool); single-pop scoring freezes S200_v2 directly;
  harness KA-2 VOID assertions retained for critical_fraction and
  memory_press. Sensitivity of hardship/informal is the QUESTION, not
  an instrument KA — no VOID on their outcome.
- Inference/gates: identical machinery and gate battery as v1
  (ABC/NPE/NRE, SBC uniformity, coverage 0.85–0.95, false-confidence,
  5 sealed exams, verdict tree A9).

## Gate
MORTALITY_GAIN_LEARNING_ELIGIBLE = YES iff hardship_mortality_gain is
RECOVERED (tree A9) with posterior contraction < 0.7 × prior sd in the
banked method. informal_floor_scale and the employment/deprivation
responses are reported on the same standard. A NO is reported with the
failure class (observation vs estimator) and the next registered
design candidate.

## Compute (gate)
Screen 49 × 720 s ≈ 10 h serial ≈ 25–30 min at 20 slots (concurrent
with the running Experience Loop; prime has 96 cores). Bank 2,000 ×
720 s ≈ 400 h serial ≈ 8–9 h at 45 slots — overnight. y_obs 15 × 720 s
≈ 12 min. Worlds: reuses the existing 200k pool (genesis-only,
horizon-independent). Total ≈ overnight, no new worlds.
Constraint honoured: no fitting against live Epoch-3 drift — this
battery is synthetic-twin identifiability only. First earn
identifiability.
