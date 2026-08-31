# MOMENTS_v1 — the pre-registered joint moment set (BIBLE VII.1)
Declared 2026-08-31, BEFORE the next calibration cycle, per v4.2 §4.2.3.
Serial fixed-point iterations remain permitted as DIAGNOSTIC steps; the
FREEZE package carries ONE joint MSM fit over this set with the full
parameter vector and provenance classes.

## Moment set (all anchors fetched; ids/vintages/sha in
## data/anchors_worldbank.json and gompertz_world.v1.json)
| m# | moment | anchor | source series |
|---|---|---|---|
| m1 | median daily welfare (household-pooled, 2021 PPP) | 9.27 | PIP WLD interpolated (fetched headcount curve) |
| m2 | mean/median welfare ratio | 2.332 | PIP WLD mean 21.6153 / m1 |
| m3 | $3.00 headcount | 0.104 | SI.POV.DDAY 2024 |
| m4 | $8.30 headcount | 0.461 | SI.POV.UMIC 2024 |
| m5 | crude death rate (adult-world band declared) | 0.00755/yr | SP.DYN.CDRT.IN 2024 |
| m6 | mean age at death vs own-pyramid GM expectation | ratio = 1.0 | derived (gompertz_world.v1 + genesis pyramid) |
| m7 | 65+ share of adults | 0.1355 | SP.POP.65UP/0014 2024, adult denominator |
| m8 | unemployment (ILO defn, via H_unemployment when registered) | 0.0481 | SL.UEM.TOTL.ZS 2024 — PENDING operator |
| m9 | cascade rate ratio vs canonical 20k reference | [0.3, 3.0] sanity | internal reference (full cascade benchmark separate) |

## Parameter vector θ_MSM (provenance class)
WAGE_LEVEL (FITTED, per-substrate) · WAGE_LOG_SD (FITTED) ·
GM A,B,c (DERIVED from fetched aggregates; upgrade on WPP table) ·
GM_OTHER_SHARE (FITTED, fixed-point-seeded) · WANT_RR (FITTED via m6) ·
HARDSHIP gradient form (STRUCTURAL, no free constant) ·
INFORMAL floors (SOURCED, ILO-derived tiers — untouched).

## Fit protocol (freeze prerequisite)
Simulated-moment vector at 20k × ≥4 seeds per evaluation; weighted
least squares in standardized moment space (weights = anchor
precision, seed-noise adjusted); Nelder-Mead over θ_MSM seeded at the
serial-fixed-point values; convergence + Jacobian rank reported; final
θ frozen with this file's hash in provenance.
