# SBI SYNTHETIC-TWIN RECOVERY GATE — REPORT v1
2026-08-26/27. Prereg: THREE_TRACK_PREREG_v1 Track A (frozen 76238e9)
+ amendment A4.1 (pre-θ*, probe memory; first screen pass self-VOIDed
on the zero-memories cold-start defect and is archived).

## What ran
6 planted θ (relax, critical_fraction, conviction_gain_dyadic,
memory_press, hardship_mortality_gain, informal_floor_scale), priors
per A1, injection KAs 8/8 (incl. Standing-Rule-2 proof that the
regression fails a broken harness). Design-world screen: 98 sims, both
fidelities; S20=16 / S200=28 summaries frozen. Training: 3,000 sims @
20k×90d + 600 @ 200k×90d, 0 failures. Blinding: M=5 θ* drawn from
OS entropy AFTER screen freeze, sealed (chmod 400), SHA-256 bb6f3dab…
logged at plant time before inference and committed
(sealed/theta_star_v1.sha256); y_obs records carry no θ; unseal only
via dataroles final_scoring. Methods: ABC (top-1%), NPE (MDN K=8),
NRE (classifier ratio), all in prior-CDF u-space; SBC on 200 held-out
draws; 5 sealed exams × 3 obs seeds × both fidelities.

## Screen findings that stand on their own
- The cascade cliff is MEASURED: critical_fraction's one channel
  (cum_cascades) sign-flips between 20k and 200k (z −5.6 vs +9.5);
  conviction_gain/hardship_gain/informal_floor are observable ONLY at
  200k. A 20k-only twin would have silently inverted or missed 4/6 θ.
- Cold-start worlds generate zero chronicle memories in 90 d: any
  memory-coupled θ needs an event-bearing observation design (A4.1).

## Verdicts (registered tree A9; best method per θ; prior sd_u 0.289)
| θ | tree verdict | best evidence | posterior sd_u (contraction) |
|---|---|---|---|
| relax | **RECOVERED** | NRE: 5/5 exams, cov 0.95, SBC ok (both fidelities) | 0.017 (17×) |
| memory_press | **RECOVERED** | NPE 20k: 5/5, cov 0.89; NRE 200k: 5/5, cov 0.875 | 0.026 (11×) |
| critical_fraction | **RECOVERED** | NPE 200k: 5/5, cov 0.875 (real contraction via cum_cascades) | 0.19 (1.5×) |
| conviction_gain_dyadic | **RECOVERED (weak)** | NPE 20k 4/5 / NRE 200k 4/5, calibrated | ≈0.29 (~1×: calibrated prior) |
| hardship_mortality_gain | RECOVERED @20k by tree / ESTIMATOR_FAILURE @200k (3/5) | gates pass at 20k at PRIOR WIDTH | ≈0.29 (~1×) |
| informal_floor_scale | **OBSERVATION_DESIGN_FAILURE** @20k / ESTIMATOR_FAILURE @200k | screen z≈−3 (employment slope only) | ≈0.28 |

Honest gloss (reporting, not gate-moving): three verdicts carry near-
prior posteriors — "calibrated but weakly informative." hardship_gain
and informal_floor cannot yet constrain the ×4 mortality gain or the
floor scale; their signals exist (z 3–3.5 at 200k) but 600 training
sims and 90-day windows under-power them.

## Gates
- SBC: uniform (KS p>0.01) for every RECOVERED cell.
- Coverage: within [0.85,0.95] for every RECOVERED cell (ABC's
  failures are over-coverage 0.96–0.995 = conservative, not deluded;
  NPE's relax failure is 0.775–0.82 under-coverage with sd 0.011 —
  slight overconfidence, hence relax is banked on NRE).
- FALSE-CONFIDENCE: zero violations — no method contracted on an
  unobservable parameter. The stack does not invent certainty.
- Confounded control: predicted hardship×informal ridge did NOT
  materialize (posterior corr −0.28…+0.17 ≈ 0) — both parameters are
  individually weak rather than jointly confounded at 90 d.

## GATE: REAL_DATA_THETA_INFERENCE_ELIGIBLE = **YES (scope-limited)**
5/6 θ pass the registered tree. Eligibility extends to θ with a
validated estimator TODAY: relax, memory_press, critical_fraction
(NRE/NPE as tabled). conviction_gain rides along with calibrated-wide
posteriors. hardship_mortality_gain and informal_floor_scale are
BLOCKED pending a battery upgrade (registered candidates: 200k
training 600→2000 sims; 90→180-day windows; deprivation-distribution
and age-resolved death summaries) — exactly the two gain parameters
the Benchmark-B repair needs, so the upgrade is on the critical path.
Estimator-per-θ table above is FROZEN as the real-data default.
Artifacts: /opt/earth1-data/sbi/{screen_report,summary_sets_frozen,
infer_20000,infer_200000,battery_verdicts}.json; VOID pass archived at
screen_void_pass1/.
