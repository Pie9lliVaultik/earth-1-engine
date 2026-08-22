# CASCADE_IDENTITY_DIAGNOSTIC_1 — registered (Bible miss protocol, steps 1–3 only)

Status recorded per ruling:
    HIGHEST CONTIGUOUS FULLY COMPLETED BIBLE STEP: 0.4
    0.5 IMPLEMENTATION / CODE-PATH: COMPLETE
    0.5 LIVE-PRODUCTION EXIT CRITERION: PENDING EPOCH 2
    0.6: INDEPENDENTLY COMPLETE

Subject: the ledgered Stage C E3 DIAGNOSTIC CONCERN — effective
IDENTITY expression broad-and-persistent under cascade residues — on
the unified canonical implementation (02a9366 or clean descendant).
Engineering/development diagnostic: NOT a holdout, NOT an acceptance
threshold. NO physics parameter or rule changes. Scope is strictly
REPRODUCE → CAUSAL TRACE → SENSITIVITY/ABLATION; STOP before
literature, hypothesis, calibration, or modification.

## 1. Reproduce (canonical executable)
Re-run the frozen Stage C census instrument (`scripts/stageC_census.py`,
locked measure set, bins 0.05/0.20/0.45) on canonical `live_one_day`,
seeds 9501/9502, N=200k, 365d. Compare every reported quantity with
the committed development result (`data/acceptance_0_8/stageC/`).
Expectation (registered): identical to the lab result up to the
instrument (Program 2 proved the executables bitwise-equal).

## 2. Causal trace
From source anchors (thresholds.py:29-68; alive.py cascade block
:338-412; cascade_residue_levels :106; effective_forces :127-159):
trigger equations, scope, thresholds, level-vs-event semantics,
cooldown/re-arm/reset, amplitude, destination, decay, half-life,
stacking, clipping, cross-rule overlap, and whether an unchanged
condition re-fires after cooldown. Delivered as
CASCADE_IDENTITY_DIAGNOSTIC_1_REPORT.md.

## 3. Rule-attribution ablations (diagnostic twins; never production)
Same canonical physics, same seeds; the detector's rule list filtered:
  A  all five rules (canonical)
  B  identity_collapse suppressed only
  C  collective_surge suppressed only
  D  both suppressed
Implemented as an instrument-side rule filter (EARTH1_DIAG_SUPPRESS)
read by the census script, which passes a filtered rule list to the
detector; stored dynamics are provably invariant (open-loop) — the
eight stored-force health metrics are reported for every twin to
prove it. Reported per twin: firings, affected Earthlings, IDENTITY
displacement distribution, effective saturation, residues/person,
episode duration, year-end persistence.

## 4. One-factor structural sensitivity (no calibration)
Open-loop ⇒ the stored trajectory and the per-day trigger-opportunity
history are invariant to cascade parameters. The canonical run records,
every day, the set of "hot" (rule, locality) opportunities for each
threshold variant (pre-cooldown). An offline reconstruction then
simulates cooldown → residue → decay → superposition for each factor
variant and reports locality-level overlay metrics. KNOWN-ANSWER for
the reconstruction: at all multipliers 1.0× it must reproduce the
canonical run's recorded firings and residues EXACTLY.
Factors, each varied alone at {0.5×, 1.0×, 2.0×}:
  - cooldown_days (30 / 20 → 15, 30, 60 / 10, 20, 40)
  - amplitude (|−0.15| / |−0.10| → 0.075, 0.15, 0.30 / 0.05, 0.10, 0.20)
  - decay_half_life (60 / 30 → 30, 60, 120 / 15, 30, 60)
  - trigger threshold — bounded in [0,1], a raw multiplier is invalid;
    PREREGISTERED TRANSFORM: scale the margin from 0.5,
    thr' = 0.5 + m·(thr − 0.5) for ">" conditions. Transformed values:
      identity_collapse: FEAR>0.7 → {0.60, 0.70, 0.90};
                         COLLECTIVE>0.6 → {0.55, 0.60, 0.70}
      collective_surge:  COLLECTIVE>0.75 → {0.625, 0.75, 1.00 (unreachable)};
                         FEAR>0.6 → {0.55, 0.60, 0.70}
    (both conditions of a rule scaled together at the same m).
Declared approximation for sensitivity metrics: overlay magnitude is
reported PRE the per-agent [0,1] clip (locality-uniform shift); per-
agent effective saturation is reported only for the A–D twins (full
instrument). No parameter combinations; no replacement value selected.

## 5. Arithmetic decomposition
From measured firing cadence, cooldown, half-life, amplitude and
locality overlap, derive the expected simultaneous residues/person,
episode length and >0.20 displacement fraction; state whether the
Stage C numbers follow from the known equations alone.

## 6. Provenance inventory
Every involved constant labeled EMPIRICAL / DERIVED / AUTHORED /
UNKNOWN with registry pointers. No replacement research.

## 7. Stop
Commit/push registration, scripts, raw artifacts, report. STOP. No
physics change, no repair proposal, no literature-driven mechanism
selection, no 0.7/0.8/Stage D.
