# C2+ POPULATION-SYNTHESIS BAKE-OFF — REPORT v1
2026-08-26. Prereg: THREE_TRACK_PREREG_v1 Track B (frozen 76238e9,
before any scored result). Data: WVS-7 microdata on prime (role TRAIN,
DEVELOPMENT/VALIDATION only — nothing here is E-class evidence).
65 countries ≥800 clean rows; leave-country-out; methods receive only
the held-out country's five 1-way margins; scored on withheld two-way
(10 tables) and three-way (10 tables) weighted joints.

## Instrument KA (Standing Rule 2)
Cell-shuffled M2 must lose to independence: PASSED in 65/65 countries
(median 6.37pp vs 0.99pp). The scorer can fail a broken method.

## Results (median across countries; MAE in percentage points)
| method | 2-way MAE | 3-way MAE | vs M0 (2w/3w) | beats M0 (2w) | beats M1 |
|---|---|---|---|---|---|
| M0 independence (true margins) | 0.988 | 0.715 | — | — | — |
| M1 incumbent genesis | 7.473 | 3.197 | −629% / −341% | 0/63 | — |
| **M2 IPF, equal-country pooled seed** | **0.753** | **0.544** | **+24.8% / +24.8%** | 60/65, p=2.4e-13 | 63/63, p=1.1e-19 |
| M3 GREG (respondent-pooled seed) | 0.754 | 0.544 | +24.4% / +24.8% | 60/65 | 63/63 |
| M4 chained conditionals | 0.815 | 0.576 | +19.5% / +20.4% | 61/65 | 63/63 |

Margin verification: every supplied constraint reproduced to ≤1e-6 per
cell by every method, verified individually (multi-margin raking; the
scalar-K theorem was NOT applied outside its single-margin domain).

## Incumbent decomposition (the important part)
- M1's own-margin product: 7.54pp ≈ its full 7.47pp error ⇒ the
  incumbent's deficit is almost entirely MARGIN error.
- Genesis joints RAKED to the true margins: 1.14pp — still worse than
  independence in 45/63 countries ⇒ genesis's joint structure
  contributes nothing beyond its margins (slightly negative).
- CANNOT_EXPRESS: genesis has NO sex attribute at all (scored as
  independence on that axis, per prereg — a substrate finding).
Honesty caveat: "truth" is WVS-7's weighted frame; part of M1's margin
error is frame mismatch (WVS Q288R income bands / Q275R education vs
genesis's census-derived schemes), not pure substrate error. The
frame-consistent comparisons (M2 vs M0 vs raked-genesis, all inside the
WVS frame) are unaffected: joint structure must come from a donor pool,
and the incumbent has none to offer.

## Gate (B6)
Best method M2 beats BOTH M0 and M1 on two-way AND three-way, sign-test
p << 0.01, relative reduction 24.8% ≥ 10%.
**C2_INJECTION_ELIGIBLE = YES** — meaning ONLY: eligible to enter the
class-2 substrate validation battery (Stage-A health regression,
byte-identical-dynamics KA, A-v2 development scoring on the new
substrate) under VALIDATION_INHERITANCE_POLICY. No injection, no
canonical change, no epoch. HOUSEHOLD_JOINTS and FINE_GEOGRAPHY_JOINTS
remain BLOCKED_ON_DATA (IPUMS is licence-prohibited; the unblock is
public NSO tables or a negotiated source).

What this eliminates: the possibility that Earth-1's initial-population
problem is subtle. It is not — margins are far off the survey frame and
joints carry no signal; a plain IPF over pooled donors already
reconstructs a quarter of the missing withheld structure from margins
alone. C2+ is buildable with boring, proven statistics.
Results: /opt/earth1-data/c2plus/bakeoff_results.json (65 countries,
200 bootstraps each); decomposition script in session scratchpad.
