# UKR-2022 FOOD-PRICE NATURAL EXPERIMENT — PREREGISTRATION
_Frozen 2026-09-01, BEFORE any outcome data is fetched or seen._

## The experiment
The 2022 post-invasion food-price spike, run through the structured consequence
report. First scored counterfactual on a real event in real units (founder chase,
2026-09-01).

## Scenario (registered dose)
Global `trade_shock = 0.20` (founder-specified 20% food-price spike class, same dose
family as the five-scenario battery's MENA config, applied globally as the real 2022
shock was). forces {fear 0.10, economics −0.10} (mild direct channel — the shock is
primarily material), firm_damage 0, persists 180d.
**Dose-provenance caveat (recorded):** FAO FPI / IMF food-index verification is
BLOCKED_ON_DATA tonight (FAO endpoints moved, FRED blocks both networks, WB GEM
retired). The 0.20 is a registered founder spec, not a fetched calibration; the FPI
fetch stays on the retry queue and, when it lands, is reported BESIDE the result,
never used to re-run.

## Protocol
200k × 16 seeds (report-grade per the hard rule) × 180d horizon, CRN-paired vs
null_branch. Ledger-cut limitation (recorded): the engine has no calendar state —
this is a class-dose retrodiction in the RETRODICTION_v1 tradition, scored on
GEOGRAPHY and MAGNITUDE, never timing.

## Pre-committed metrics (scored when outcome anchors fetch; never tuned on)
- **M1 magnitude:** scaled ORDER-2 Δhungry (persons) vs the real-world increase in
  acutely food-insecure people 2021→2022 (WFP/FAO GRFC-class source, to be fetched
  and hashed). Gate: within 5× either way (founder framing).
- **M2 geography:** Spearman rank correlation of per-country Δhungry vs real
  per-country increases on the overlap set. Gate: ρ > 0; value reported.
- **M3 top movers:** count of model top-5 countries appearing in the real top-5.
  The founder's prior: Egypt, Lebanon, Syria led in reality.
Model outputs are committed BEFORE any outcome fetch; scoring is one pass, no reruns.
