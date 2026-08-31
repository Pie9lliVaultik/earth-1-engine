# CYCLE c000-HG — hardship gradient (deprivation cliff → depth-of-shortfall × reserve cushion)
_Retroactive XI.A.2 report owed under BIBLE.md v4.2 §4.2.3. Pre-cycle structural
change of 2026-08-27, predates the numbered CALIBRATION_CYCLES.md table; the
gradient flag enters the canonical cycle flag set from c002 onward
(`MODE=gradient`, CALIBRATION_CYCLES.md rows c002+)._

## RESULT
| field | value |
|---|---|
| gate(s) exercised | crude death rate, deprivation shares (>0.99 / >0.5 / 0.05–0.5), cascade count, poverty $3.00/$4.20/$8.30, unemployment |
| number(s) | CDR 2.24%→1.24%/yr; deprivation>0.5 33.1%→8.1%; cascades 2168→1077; starvation deaths 108→22 (20k×180d, LIVING_BASELINE_20K_REALDATA.md). At 20k×90d: dep>0.99 30.5%→0.0%, deaths/yr 2.07%→0.99% (HARDSHIP_GRADIENT_IMPACT.md). Seed σ: TODO-VERIFY (single-seed runs; no σ on disk) |
| target | real CDR 0.76%/yr all-ages (WB 2024, data/anchors_worldbank.json); extreme poverty ~9–10.4% ($3.00). Prereg hash: TODO-VERIFY (change predates the gate-table prereg) |
| gap | CDR after − real: +0.48pp/yr (1.6×, adult-only caveat); dep>0.5 8.1% vs $3.00 headcount 10.4% (not a like-for-like observable — see INSTRUMENT) |
| agents / seeds | 20000 × 1 (90d and 180d batteries); 20000 × 3 owed |
| flag set | EARTH1_HARDSHIP_MODE=gradient (default `cliff`, canonical v4.1); Epoch 3 untouched |
| hashes | anchors sha registered in EVALUATION_OUTCOME per LIVING_BASELINE_20K_REALDATA.md; cycle-table hashes from c002: t:256fe63229 a:39d484d65f i:1db1b15de3. Tree/constants hash for the 08-27 runs: TODO-VERIFY |
| host / commit / wall-clock | TODO-VERIFY (runner stamp absent from the 2026-08-27 evidence docs) |

## INSTRUMENT
Ground truth: data/anchors_worldbank.json, fetched from the World Bank open
indicator API (WLD aggregate, series ids + URLs + vintages recorded, latest =
2024, sha registered): poverty $3.00 10.4%, $4.20 18.9%, $8.30 46.1% (2021 PPP);
CDR 7.551/1000. Units: deaths/yr population-weighted; Earth-1 is adult-only
(18+) so its CDR is not directly comparable to the all-ages anchor (caveat
carried in LIVING_BASELINE_20K_REALDATA.md). Leakage: anchors are the test —
HARDSHIP_GRADIENT_IMPACT.md records that no constant was tuned against any
target. Canonical path: the gradient runs on the unified loop behind the
shipping env flag (earth1/life.py:150), not a script-level assembly.
Failure case this instrument reports, demonstrated: the earlier claim
"severe hardship 7.9% ≈ real ~9%" was caught and struck as a correction of
record — it compared an Earth-1 latent threshold (deprivation>0.5) to a
monetary poverty rate, with the ~9% written from memory; superseded by
H_poverty (earth1/poverty.py) scoring the fetched series. Known instrument
limitation registered before deployment: the dep>0.99 bucket is empty by
construction under the gradient, so `destitute_share` is not comparable across
the two forms until its observation operator is re-anchored (>0.5 = severe).

## DIAGNOSIS
Causal path: earth1/life.py:567 `covers = income >= life.cost` is a hard step —
99% of cost scores identically to zero income — and the cliff form
(earth1/life.py:583-585) `deprivation = where(covers, 0, clip(1 − wealth/DESTITUTE_BUFFER, 0, 1))`
with DESTITUTE_BUFFER=3.0 days (earth1/life.py:146) empties immediately,
pinning every uncovered agent at ≈1.0: measured 30.5% of the world at dep>0.99
and only 0.5% anywhere in (0.5, 0.99). Every downstream consumer — mortality
hazards ×(1+k·dep), cascade entry via deprivation-driven forces — read
"universal catastrophe". Attribution (2×2, LIVING_BASELINE_20K_REALDATA.md):
ΔGRAD −1.00pp/yr of crude death vs ΔC2 +0.55pp and interaction −0.62pp; ΔGRAD
−25.1pp of dep>0.5 and −1091 cascades — the gradient dominates every
hardship/mortality improvement while moving monetary poverty only +1.4pp.
Miss class: (d) structural — the transfer function itself was binary; no
mortality parameter was touched yet CDR halved, so no parameter could have
carried this movement.

## RESEARCH
Two established approaches for measuring deprivation given a poverty line:
1. **Headcount-style binary indicators** — the incumbent cliff is the headcount
   form. Sen (1976, "Poverty: An Ordinal Approach to Measurement",
   Econometrica) established its defects: insensitive to the depth of poverty
   (violates monotonicity) and to distribution among the poor (violates the
   transfer axiom) — exactly the failure measured here (a household at 99% of
   cost scored as zero income).
2. **Poverty-gap / graded-deprivation measures** — Foster, Greer & Thorbecke
   (1984, "A Class of Decomposable Poverty Measures", Econometrica): the FGT
   family P_α with normalized shortfall g = (z − y)/z; α≥1 grades deprivation
   by depth. Watts (1968) is the earlier graded (log-gap) form.
Selected: the FGT α=1 normalized shortfall as `gap`, multiplied by a reserve
cushion `(1 − wealth/buffer)` — assets buffer a consumption shortfall,
consistent with buffer-stock saving (Deaton 1991, Econometrica). Headcount-only
rejected on Sen's monotonicity grounds; Watts rejected as the log form diverges
at zero income where Earth-1 needs a bounded [0,1] hazard multiplier input.

## IMPLEMENTATION
Smallest defensible change — one formula swap, same inputs, same zero point,
same maximum: earth1/life.py:568-581, behind EARTH1_HARDSHIP_MODE
(earth1/life.py:150), **default OFF** (`cliff` = canonical v4.1):
`gap = clip((cost − income)/cost, 0, 1)`; `cushion = clip(wealth/DESTITUTE_BUFFER, 0, 1)`;
`deprivation = where(covers, 0, gap · (1 − cushion))`.
Constants: none introduced. DESTITUTE_BUFFER=3.0 reused unchanged (pre-existing,
ASSUMED). The functional form is DERIVED (FGT structure); nothing FITTED — no
constant was tuned against any target (HARDSHIP_GRADIENT_IMPACT.md). Not
substrate-dependent. Classified Class 3 — foundational — before deployment.

## ABLATION
Paired evidence on disk: the 2×2 decomposition table in
ops/alive/LIVING_BASELINE_20K_REALDATA.md (incumbent/cliff, incumbent/gradient,
C2+/cliff, C2+/gradient at 20k×180d) isolates ΔGRAD from ΔC2: crude death
−1.00pp/yr, dep>0.5 −25.1pp, cascades −1091, starvation deaths −86 attributable
to the gradient alone, with small interaction terms (−0.62pp, −342). The 90d
config table in ops/alive/HARDSHIP_GRADIENT_IMPACT.md is a second ON/OFF pair.
Missing: raw per-run artifacts and paired-CRN confirmation for these four cells
are not on disk (no data/cycles/*.json exists for the 08-27 battery), and all
runs are single-seed so no σ accompanies the deltas. **Owed: one paired-CRN
rerun, incumbent+cliff vs incumbent+gradient, 20k×180d × 3 seeds, emitting raw
run artifacts, so the −1.00pp CDR delta carries a σ.** Sensitivity of the gate
to a new constant: n/a (no constant introduced). Regression screen: poverty
+1.4pp and unemployment 8.44%→9.69% moved adversely; without σ the >2σ VOID
test cannot be evaluated — covered by the owed rerun.

## RETEST
TRAIN/DEV, unchanged gates, same 20k battery (LIVING_BASELINE_20K_REALDATA.md),
canonical cliff → gradient: poverty $3.00 35.1%→36.5% (real 10.4%); $4.20
57.4%→58.4% (18.9%); $8.30 90.3%→90.8% (46.1%); median $/day 3.97→3.93 (9.27);
CDR 2.24%→1.24%/yr (0.76% all-ages); mean age at death 43.7→47.9 (LE 73.5);
cascades 2168→1077; unemployment 8.44%→9.69% (4.81%). Poverty is untouched by
design — the income distribution defect (M-INCOME-SCALE, then M-LOWER-TAIL) is
a separate registered miss repaired in its own change. Benchmark B DEV event
retest and A-v2 DEV under the gradient: owed before promotion, per
HARDSHIP_GRADIENT_IMPACT.md. 200k rerun: owed (movement ≥0.3pp; "next rung:
rerun this battery at 200k once prime frees").

## STATUS
**ITERATING** — the mortality gate is not met (1.24% vs 0.76%/yr, adult-only
caveat pending age tables) and PASS is barred by open obligations: seed σ and
paired-CRN artifacts (ABLATION), destitute_share observation-operator
re-anchoring, Benchmark B DEV + A-v2 DEV retests, 200k rerun. Flag remains
default OFF; no HOLDOUT touched. Next hypothesis (one line): the residual fat
lower tail is weak income floors — fetch ILO social-protection
coverage/adequacy and repair SAFETY_NET/INFORMAL floors (M-LOWER-TAIL).
