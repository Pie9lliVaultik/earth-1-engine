# LIVING BASELINE — 20k vs REAL DATA (first rung of the ladder)
2026-08-27. Founder ruling: benchmark against real data; 20k → 200k →
full scale; fix what we find and run again.

## Anchors — FETCHED, not authored
data/anchors_worldbank.json, World Bank open indicator API, WLD
aggregate, series ids + URLs + vintages recorded, sha registered
EVALUATION_OUTCOME. Latest = 2024. Poverty $3.00 **10.4%**, $4.20
**18.9%**, $8.30 **46.1%** (2021 PPP); CDR 7.551/1000; CBR 16.273/1000;
LE 73.482 yr; unemployment 4.806%.
**Correction of record:** the earlier "severe hardship 7.9% ≈ real ~9%"
claim was NOT a measurement — it compared an Earth-1 latent threshold
(deprivation>0.5) to a monetary poverty rate, and the ~9% was written
from memory. Superseded by H_poverty (earth1/poverty.py) scoring the
fetched series. Hand-written mortality age-share constants have been
DELETED; that comparison is BLOCKED_ON_DATA (UN WPP / WHO life tables;
WHO GHO API unreachable 2026-08-27).

## Result (20k × 180d, population-weighted)
| line | REAL (WB 2024) | inc/cliff | inc/grad | C2+/cliff | C2+/grad |
|---|---|---|---|---|---|
| $3.00 | **10.4%** | 35.1% | 36.5% | 40.3% | 41.1% |
| $4.20 | **18.9%** | 57.4% | 58.4% | 63.3% | 63.9% |
| $8.30 | **46.1%** | 90.3% | 90.8% | 92.1% | 92.2% |
Earth-1 is 2–3.5× too poor at every line.

## 2×2 decomposition (Δ_C2 / Δ_gradient / interaction)
| metric | inc/cliff | inc/grad | C2/cliff | C2/grad | ΔC2 | ΔGRAD | inter |
|---|---|---|---|---|---|---|---|
| crude death /yr | .0224 | .0124 | .0279 | .0117 | +.0055 | **−.0100** | −.0062 |
| pov$3 headcount | .351 | .365 | .403 | .411 | +.052 | +.014 | −.006 |
| deprivation>0.5 | .331 | .081 | .388 | .116 | +.057 | **−.251** | −.021 |
| cascades | 2168 | 1077 | 2500 | 1067 | +332 | **−1091** | −342 |
| starvation deaths | 108 | 22 | 151 | 16 | +43 | **−86** | −49 |
Reading: the gradient dominates every hardship/mortality improvement
and does essentially NOTHING for monetary poverty (+1.4 pts). C2+
modestly worsens hardship metrics; the interaction is real but small.
**Two separate defects, now cleanly separated:** (1) the deprivation
transfer function was binary — gradient repairs it; (2) the income
distribution is genuinely too poor — untouched by either change.

## NEW REGISTERED MISSES (quantified today)
**M-INCOME-SCALE.** Earth-1 welfare deciles vs the quantiles the WB
headcounts imply: required multiplier 1.80 (p10), 1.93 (p19), 2.38
(p46) — mostly a ~2× scale error plus a compression component (the
upper half is relatively more depressed). Earth-1 median $3.68/day
= 1.23× the survival cost; the real median sits near 2.9× the extreme
line. That ratio is an empirical quantity, not a free knob.
**M-MORTALITY-AGE.** Mean age at death 43.7 (cliff) / 47.9 (gradient)
against life expectancy 73.5. Earth-1 kills adults ~25 years too young.
Age-structure scoring is BLOCKED_ON_DATA; the mean-vs-LE gap is
already decisive enough to register the miss.
**Caveat carried:** Earth-1 is adult-only (18+), so its crude death
rate is not directly comparable to the all-ages CDR; the adjustment
needs the same missing age series.

## NEXT (fix, then rerun 20k → 200k → full)
1. M-INCOME-SCALE: calibrate the wage/subsistence ratio and dispersion
   to the empirical median-consumption/extreme-line ratio and real
   income dispersion — a registered ratio, not a fit-to-outcome.
2. Rerun this battery; then A-v2 DEV; then 200k.
3. M-MORTALITY-AGE after income (deprivation-driven young-adult deaths
   are expected to fall with the income repair; re-measure before
   touching any hazard).
