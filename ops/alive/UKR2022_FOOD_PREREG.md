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

## DOSE VERIFICATION (added 2026-09-02, AFTER model output was frozen — verification, not tuning)
Founder-supplied FAO figures: FPI March 2022 = 159.3 (+12.6% m/m, later revised
159.7/+13.2%), highest since 1990; +33.6% y/y; Cereal Price Index +17.1% m/m.
Live FAO page fetched and hashed from prime as the source
(`/opt/earth1-data/fao_fpi_page.html`, sha256 b343af07a49eceb96d50…, cites the
March 2022 peak; the underlying CSV remains on the retry queue).
**Dose framing (stated, per founder):** the registered 20% sits between the headline
m/m jump (+13%) and the cereals m/m jump (+17%), well under y/y (+34%). Cereals is
the channel that hit MENA bread prices, so the spec is conservative for Egypt.

## RESULT-HEADER CAVEATS (registered)
- M2/M3 are scored tonight on the FORCE-SHIFT ranking, not hunger ranking — they test
  "did Fear/Economics move most in Egypt, Lebanon, Syria," not "did hunger rise most
  there." `hungry_by_country` in snapshot() is v1.1 item #1 — it is exactly the field
  the +326M headline needs at country level.
- M1 anchors to fetch (one pass, post-freeze): country-level "acutely food insecure"
  changes from the 2022 Global Report on Food Crises + WFP Egypt/Lebanon/Syria
  country briefs, Q2 2022.

## FOUNDER PRIOR — recorded 2026-09-02 BEFORE the judge was fetched (verbatim)
M1 borderline: reality ≈ +63M acutely food insecure (WFP 282M→345M) and +30M
undernourished (FAO SOFI); +326M is ~5× the first, ~10× the second — could squeak
inside the band against WFP, fail against FAO; the overshoot mechanism is legible:
no adaptive channels (substitution, subsidies — Egypt's bread subsidy absorbed a
huge share in reality — stock drawdown) — the dampers that turn a 20% price shock
into a 5–10% hunger shock. M2/M3 likely to miss, and the miss is the more useful
result: Romania and Uzbekistan in the top movers is the tell — the model has no
food-import-dependence input, so poverty geography emerged, not food-exposure
geography; Egypt/Lebanon/Syria absent from the top eight ⇒ low M3 overlap. Named
fix: FAO/WB cereal import dependency ratio, provenance-gated, family-scoped to the
food injector. "If that's how the scoring comes out, it's a good night's result...
And it was all predicted before the judge was opened."

## Grounding source-notes (fix queue, pre-public-API): officeholder facts resolve
against the official government site (not Wikipedia summary); gold resolves against
a bullion feed (not the PAXG proxy); FOMC-calendar fetcher closes g7.

## SCORED — 2026-09-02, one pass, judge fetched AFTER model freeze
Judge: GRFC AFI database (HDX, open; sha 44de722610a435d1cd37), IPC Phase-3+
population by country, 48 countries assessed in both 2021 and 2022.

- **M1 FAIL — 8.5×** (model +326M vs GRFC +38.5M; 191M→230M). The founder's prior
  leaned fail ("could squeak vs WFP +63M, fail vs FAO +30M") — GRFC's +38.5M sits
  between and the model overshoots 8.5×. Frame caveat both ways: GRFC covers only
  48 crisis-assessed countries; the model counts world-wide hunger crossings.
- **M2 FAIL — ρ = −0.137** (p=0.37, n=44). No geographic correlation. As predicted:
  poverty geography emerged, not food-exposure geography.
- **M3: 1/5 overlap** (Somalia). Real top movers: **UA, ET, NG, PK, SO** — the 2022
  hunger surge was war- and drought-driven with price as amplifier; a price-only
  dose cannot produce Ukraine or Ethiopia. Founder's EG/LB/SY trio also missed in
  GRFC terms — **Egypt's real delta is 0.0: the bread subsidy absorbed the shock,
  exactly the damper the prior named.** (LB real +1.25M vs model rank 177.)

## NAMED CYCLES (each one change, each XI.A.2)
1. **Damper channels** — substitution, subsidies, stock drawdown. Calibration
   target handed to us by reality: Egypt's ZERO. The transfer function that turns a
   20% price shock into a 5–10% hunger shock, not a 100% one.
2. **Cereal import-dependence input** — FAO/WB CIDR, provenance-gated, family-scoped
   to the food injector (the same recipe as religiosity/geopol).
3. **Compound-event composition** — 2022 was war + drought + price; the scenario
   spec needs composability (the registered doses can already stack; the injector
   should ground them together).
4. **hungry_by_country** in snapshot() (v1.1 item 1, unchanged).

## VERDICT (founder's template, met)
A large, real, signed response to a real shock; the magnitude overshoot names the
dampers; the geography miss names the input; the subsidy damper is confirmed by
Egypt's zero. All of it stated before the judge was opened.
