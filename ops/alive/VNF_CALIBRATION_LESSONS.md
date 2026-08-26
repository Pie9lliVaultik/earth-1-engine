# VNF CALIBRATION LESSONS — verified against `vivid-node-forge-main (43).zip` (2026-08-26)

Every claim checked against source; file:line cites from the zip. This is the
design source for a future BENCHMARK_A_PREREG_v2 — no v2 run is authorized here.

## Verified findings

| claim | verdict | evidence |
|---|---|---|
| 45–55 compression was engine, not ground truth | **VERIFIED** | `docs/GOQA40_POLARITY_AUDIT.md:53-55` — Q254 pride engine 46.7% vs truth 88.6%; Q187 bribery 54.7% vs 13.0%; Q180 casual sex 50.8% vs 9.7%; each marked "ground truth correct → engine compression" |
| Inverse readout solver: ridge in logit space, cohort design matrix of CENTERED trait means + political scalar | **VERIFIED** | `supabase/functions/_shared/inverse_solver.ts:1-77` — `logit(y_g) = β0 + Σ βi(x̄g,i − x̄i) + βp·P_g`, `β = (XᵀWX+λI)⁻¹XᵀWz` |
| Unpenalized intercept fix (+0.528 logit pooled bias) | **VERIFIED** | `inverse_solver.ts:92-97` — "intercept diagnostic (2026-07-12) showed pooled residual mean = +0.132 probability / +0.528 logit across 1,224 seed-country rows… Default lambdaBaseline is now 0" |
| Orthogonalize trait columns against the political axis | **VERIFIED** | `inverse_solver.ts:102-111` (Sprint 3.4) — residualize each centered trait on political_scalar so the dominant axis isn't smeared into alternating trait weights |
| Rank-deficient derived traits get zero columns | **VERIFIED** | `inverse_solver.ts:36-45` — fear/collective are exact linear combinations; excluded from the solve |
| Country culture offsets with LEAVE-ONE-OUT scoring | **VERIFIED** | `solve-inverse-weights/index.ts:426-444` — residual r_c = logit(y) − offset_old − fitted; LOO offset = mean of OTHER seeds' residuals; a question cannot calibrate itself |
| 1000-row silent cap bug → "verification not vibes" protections | **VERIFIED** | `docs/COVENANT_AUDIT.md:52,155-156`, `docs/FULL_SYSTEM_AUDIT.md:166` — PostgREST `.limit(N>1000)` false-guard pattern, partially fixed |
| Runtime regimes: survey-matched / reference-anchored / reference-anchored-dampened / live-grounded / forward-estimate | **VERIFIED** | `ground-question/index.ts:41,784-831,900-922` — dampened weight = solved × min(0.30, (sim−0.50)/0.35×0.30); PATH D live grounding when no defensible anchor |
| Post-hoc layers destroyed spread; publication trace + guard fix | **VERIFIED** | `_shared/compression_trace.ts` (raw_camp_vote → coherence → guard → anchor → published, spread destroyed per stage); `_shared/reasonableness.ts:55-73` — "re-centering is a large share of the 45–55% compression"; guards may no longer land answers inside 45–55 |
| Honest caveat: the old system never beat the LLMs | **VERIFIED** | `docs/BENCHMARK_HISTORY_AUDIT.md` — May runs unscored (no comparison existed); first real standoff 2026-07-12; on every scored run best LLM (0.02–0.05 MAE) beat Earthlings (0.123→0.071); the engine later timed out at RPC scope |

## Mapping to Benchmark A v1's misses

Benchmark A v1 asked Earth-1's structure to carry the LEVEL: national means
(lost to MRP by 5.6 pp), cohort levels (lost), raw joint marginals (lost
260×) — while the marginal-matched joints (level supplied externally) were
110× better than independence in the median country. That is the SAME
separation VNF converged on: **anchor the level in data; make the agents
explain who differs from whom.** The v1 hybrid failed for the exact
mechanism VNF documented twice: (a) the level was not given its own clean
degree of freedom (our sigmoid-averaged offset shifted the MRP mean — the
intercept-penalty class of error), and (b) nothing enforced
mean-preservation (no K).

## Benchmark-A-v2 design (for the next preregistration; not run)

Per (item, country, optionally cohort): logit P(Y_i=1) =
logit P_MRP(c,g) + Δ_i − K, with Δ_i = centered Earth-1 agent structure
(features orthogonalized against the axes the level model already
explains: country, age band, income — the political-axis lesson
generalized) and K solved numerically per cell so the weighted agent mean
EXACTLY equals the MRP level (VNF's unpenalized intercept, done per cell).
Earth-1 then earns value only through: above/below-mean identity, cohort
gradients, correlations/joints, tails, conditional structure, and event
response. Country offsets, if any, are LOO by construction. The
publication path must carry a compression trace (stage-by-stage spread)
and guards that cannot re-center. `calibration_source` is regime-tagged
(survey-matched / anchored / dampened / abstain), and absence of an
anchor → abstain, never a naked 50/50.

## What NOT to import
The Supabase/edge-function stack, the RPC engine (`compute_civilization_
answer_v4` — times out, superseded), the May-2026 narrative, and any
unverified aggregate estimates. Lessons transfer; code does not.
