# 2010–11 FOOD-PRICE SPIKE — SEALED JUDGE (registered 2026-09-02)
_The 2022 judge is OPENED and therefore DEV: fix on it, never claim on it. This is
the claim judge for the food-shock family. Outcome VALUES are unfetched as of this
registration; sources are registered by name and location only._

## Exposure series (DEV-usable, defines the dose)
FAO Food Price Index, June 2010 → February 2011 (+~35% per the public record; the
exact series to be fetched and hashed at run time from FAO/FRED/mirror — exposure is
not outcome).

## SEALED OUTCOME ESTATE (role HOLDOUT — no fetch until the model output is frozen)
- FAO SOFI prevalence-of-undernourishment changes 2010→2011 by country
  (FAOSTAT FS domain / SOFI annex tables).
- WFP / FEWS NET country assessments 2011 where available.
Registered locations only; no value from these sources may enter any calibration,
transfer function, FIT-half, or conversation before the freeze. Fetch happens ONCE,
after the F1–F4-adopted model's 2010 run is committed.

## Pre-committed metrics (identical spirit to UKR-2022)
- M1: scaled Δhungry (GRFC/SOFI-frame beside worldwide) vs real Δundernourished
  2010→2011; gate within 2× (the post-damper standard, per F3's gate).
- M2: Spearman of per-country Δhungry (hungry_by_country, F1) vs real per-country
  changes; gate ρ > 0.3 on the full set (no FIT-half here — this judge fits nothing).
- M3: model top-5 ∩ real top-5 ≥ 2/5.
- Composed-scenario grounding for 2010–11 (Russian export ban, La Niña harvests,
  MENA import shock) uses EXPOSURE-side sources only, hashed.

## Rules
Every fitted constant used in the 2010 run carries its FIT-half hash from the 2022
DEV work; anchors bitwise unchanged; one output freeze; one judge fetch; one scoring
pass. 2022 appears in any report as the DEV case that named the mechanisms.
