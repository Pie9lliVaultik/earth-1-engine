# ERRATUM — the religiosity injection was target leakage (2026-08-18)

## VOID results (do not cite, do not build on)

| Claim made | Status |
|---|---|
| GOQA 10.59 → 9.42pp, 36/40 (200K, religiosity) | **VOID — leakage** |
| GOQA 9.19pp, 37/40 (30K, +ideology, +social_class) | **VOID — two leaked features** |
| "rank-18 ceiling broken by construction" | **VOID — unsupported** |
| "B1 target hit at first attempt" | **VOID — hit by contamination** |
| "cell degradation = ecological fallacy" | **WRONG DIAGNOSIS** — it is leakage's fingerprint: a feature that carries country-level TARGET information and no genuine within-country signal moves the graded quantity while degrading the ungraded one |

## What happened

`religiosity_priors.py` defined religious as **Q164 ≥ 6** ("How
important is God in your life?"). **Q164 is item #2 of the 40 GOQA
benchmark questions.** The injected per-country prior correlates
**+0.983** with its own benchmark target (mean |diff| 5.5pp) and
exceeds |0.5| against **16 of 40** targets, |0.7| against 7. The
"improvement" is the answer key for ~40% of the exam.

The gate found a second leak the review had not named: **ideology
(Q240) is also a GOQA item** (|corr| 0.783 with its own target,
18 targets above 0.35). The "best configuration" contained two leaked
features. `marital` (Q273) fails the correlation rule (0.554 vs Q71)
without being an item.

Verified banned: **religiosity, ideology, marital**.
Verified clean: **employed** (max |corr| 0.364), **social_class** (0.437).

## Honest re-measurement, clean features only (30K)

| | GOQA CV MAE | Wins |
|---|---|---|
| Baseline, no injection | 0.1094 | 33/40 |
| employed + social_class | 0.1095 | 35/40 |

**NO MEASURED EFFECT.** MAE +0.01pp = nothing. The 33→35 win count is
NOISE, not a directional hint: the win criterion has a ±0.005 dead band
and fold noise at this scale is ~0.6pp, so two questions crossing the
threshold is exactly what reshuffling produces. Recorded as "no
measured effect" deliberately — "wins improved but unconfirmed" is the
phrasing that gets quoted later without its caveat, which is how 6.1pp
survived for weeks.

**What this positively establishes:** employment and social class,
injected as genuine within-country joint structure, do NOT improve
country-level prediction. The rank-18 bound now holds under an honest
test with clean features — stronger evidence than yesterday's argument
from arithmetic. Country-level accuracy is not where within-country
structure pays. That small true number replaces a large false one.

The within-country cell metrics are unchanged by the clean injection
(cell-MAE 0.3945 in both flag-on runs) — because the clean features
were already near-orthogonal to the graded targets.

## The permanent fix (in force now)

`scripts/feature_adjacency_gate.py` — MANDATORY before any new genesis
input is measured. Rules: (R1) source variable id must not appear as a
GOQA item; (R2) |corr| with any single target ≤ 0.50; (R3) at most 4
targets above 0.35. Writes `data/feature_adjacency.json`, exits nonzero
on violation.

`calibration._banned_features()` — reads the gate report and **removes
banned features from the design matrix regardless of EARTH1_INJECT**.
**Fails CLOSED**: no gate report on disk ⇒ no injected feature enters.

## Process lesson (recorded)

The 90-minute measure→fix→remeasure→commit loop let a contaminated
feature reach a committed headline inside one cycle. Replication would
NOT have caught it — replication confirms a leaked number as reliably
as a real one. The fix is an **adjacency check before the feature
enters**, not verification after the number lands. That check is now a
loop gate, not a review step.

Standing numbers are unchanged by this erratum: **GOQA 10.59pp vs
naive 12.64, 34/40** (corrected truth, pinned folds) remains the
headline. B2 cohort results (14.35 → 11.24pp, gradients 31% → 80%)
stand — they come from cohort-level CALIBRATION TARGETS, not from an
injected feature, and their truth source (age-bucket cells) is not a
benchmark item.
