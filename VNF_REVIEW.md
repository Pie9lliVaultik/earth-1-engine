# vivid-node-forge Review — Keep / Trash Verdict (2026-08-18)

Deep review of the old TypeScript engine (1,047 source files, ~150 edge
functions) against Earth-1's frozen physics and measured verdicts.
Method: three parallel deep-readers (solver machinery / data provenance
/ mechanisms+product) + first-hand reads of the load-bearing files.
Every claim in the underlying reports cites file:line. No assumptions.

## KEEP — ranked by value to Earth-1 today

1. **The real-data aggregation pipeline** (`imported_vnf/scripts/`):
   `aggregate_wvs.py` (official WVS7 v6.0 microdata → weighted country
   + cohort seeds, spot-check-gated), `aggregate_wvs7_full.py` (DuckDB,
   every Q-variable, beyond the GOQA subset), `wvs7_labels.py` (141
   variable labels validated at r>0.90 vs published items),
   `aggregate_gss.py` (GSS 1972–2024), `aggregate_anes.py` (ANES 2024),
   `build_goqa_corpus.py` (full 2,556-item bank). THIS is the
   provenance fix for Wave 7 — reproducible, weighted, honest.
   Caveat: raw microdata not in the zip (re-download W7 v6.0 CSV, GSS
   .dta, ANES CSV — WVS/NORC accounts needed → Pietro). Wave 5/6 have
   NO real replacement anywhere in the old repo; the same pipeline
   pattern extends to their official files.
2. **Bundled real ground truth**: `data/benchmark/vnf_ground_truth_v2.json`
   (the polarity-audited GOQA-40 — used TODAY to find that Earth-1's
   copy carries the uncorrected Q222/Q65 binarization errors);
   `data/gss_cohort_seeds_v1.csv` (real GSS aggregates by political ×
   age cohort — immediate material for the inheritance-A/B cohort
   court and distribution-level validation).
3. **Cohort-axis methodology**: the old system aggregated ground truth
   by age bucket (Q262) and left-right (Q240) and FIT calibrations at
   cohort level (sim_solver on cohort targets). Earth-1 validates only
   at country level — this is the designed path to the
   distribution-fidelity era.
4. **Solver refinements** (docs_external/vnf_reference/sim_solver.ts):
   per-parameter-class ridge (traits/political/baseline), box caps,
   warm start, clip-gates-gradient, Adam(0.05, 800); plus
   inverse_solver's political-axis orthogonalization, leave-one-out
   country offsets, sqrt(n) cohort weighting, clamp-before-transform.
   Mining list for estimator-B v2 — not wholesale adoption.
5. **Identity + render substrate (product tier)**: name/city/occupation
   banks (LLM-free identity), Schmitt/Hofstede/loss-aversion trait
   formulas (backfill-souls), and the engine-firewalled "meet an
   earthling" surface (living card API, life-tick with ±0.05 bounded
   deltas that never touch prediction, feed, observatory, claim flow).
   The consumer product Earth-1's dashboard lacks; observe-only by
   design so it cannot contaminate measured accuracy.
6. **world-pulse ingestion front-end**: GDELT DOC + 11 RSS feeds +
   market priors with domain/region classifiers — a real news-sourcing
   layer for the perception channel.
7. **Honest history to reconcile**: the old benchmark docs record
   GPT-5 at 0.031–0.055 MAE beating the old engine on every standoff —
   while Earth-1's leaderboard prints "GPT-5: 0.1810 (from VNF)".
   Contradiction registered → live LLM re-benchmark queued. Also the
   old pinned gate floors and the +0.528-logit intercept-bias
   diagnostic that justified an unpenalized baseline.
8. **Per-agent knowledge wallet (design only)**: knowledge_entries
   schema (depth/confidence/inheritance lineage) + salience-ranked
   retrieval (0.25·depth + 0.35·confidence + 0.40·overlap) +
   expertise recompute. Keep as the DESIGN for individual memory —
   history warns the LLM-per-agent version scored 26.4pp GOQA;
   port the structure, not the cost.

## TRASH — with reasons

- **SQL estimator branches v1/v3/v4/v5** incl. the hard-threshold
  "residual projection" v4: lost their own ablations; v2 won and its
  spec is already Earth-1's conceptual ancestor. Keep v2 constants as
  reference only.
- **agent-explore** (serendipity, social posts, friend-sharing): the
  same emergent-social family Earth-1's grid measured as
  accuracy-subtracting; narrative machinery without predictive value.
- **All self-chaining orchestration** (sprint-orchestrator,
  chain-watchdog, agent-generation-tick, EdgeRuntime.waitUntil
  plumbing): artifacts of edge-function timeouts; systemd supervisor
  supersedes wholesale.
- **run-campaign** (website-feedback product), **readout.ts** LLM
  narration plumbing, admin/auth/billing edge functions,
  Supabase-specific everything.
- **country_priors.ts / backfill-demographics literals**: authored
  round-number distributions — same category as census.py, no new
  provenance value.

## Immediate actions taken with this review

- Q222/Q65 ground-truth corrections ported →
  `data/benchmark/goqa_ground_truth_corrected.json`; corrected-truth
  benchmark rerun queued (headline will shift; both engine and naive
  are re-scored on the same corrected truth).
- Keepers imported under `imported_vnf/` + `docs_external/`.
- Queued: LLM-standoff reconciliation; W7 microdata re-download
  (Pietro: WVS account) → run `aggregate_wvs.py` → verified W7 truth;
  GSS cohort seeds into the A/B cohort court.
