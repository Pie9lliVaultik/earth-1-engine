# BENCHMARK CAMPAIGN v1 — registered 2026-08-31

Founder ruling 2026-08-31: benchmarking starts today, in parallel with the c-SHOCK
mechanism cycle (Option B, narrowly). All work below is TRAIN/DEV. Standing invariants:
HOLDOUT/PROSPECTIVE readable only under final_scoring, never during this campaign; no
frontier-LLM baselines; misses reported as misses; every fix is one named change per
XI.A.2 cycle; fetch-and-hash or BLOCKED_ON_DATA; production Epoch 3 untouched.

## Track 1 — Opinion (Benchmark A, all five tasks, candidate substrate)

Not just level. Runner: `scripts/benchmark_a/run_v2.py` with `EARTH1_SUBSTRATE=c2plus_v1`,
separate `EARTH1_AV2_OUT` (frozen v2 artifacts never overwritten).

1. Country means vs MrsP, tier table.
2. Cohort cells on the reliability-weighted readout, with coverage.
3. Joint distributions — Wasserstein vs independent-marginal baseline.
4. Held-out question generalisation.
5. Cross-wave deltas (WVS-6→7; Pew wave pairs where fetched).

Estates: WVS held-out countries; Pew-frame dev set (469 items,
`data/concordance/goqa_dev.json`); GOQA-dev. **Gallup: founder purchase decision
pending** — enters the day the microdata lands; it is the fourth estate.

## Track 2 — Simulated events (register expansion)

The GDELT-verified protest set stays. Expand `ops/alive/EVENT_REGISTER_DEV.json` with
resolved rate decisions, referendums, and market-panic cascades inside the horizon, all
scored under the §12 metric set. Goal: grow event count until the CI on pooled ΔBrier is
meaningful. Calibration (ordering right, probabilities flat) is a readout-layer
temperature problem — fix in the readout, not the physics, as its own cycle.

## Track 3 — Attitude level gap (~5.1pp to ACCEPT)

Region-copy (10.31/9.70) is the bar. The named cycles from the 2026-08-31 scoreboard
decomposition run as this track's fix loop — one change per cycle, tiers as the gate,
top-3 error cells first.

## Track 4 — Prospective register

Grows daily (`ops/alive/PROSPECTIVE_REGISTER.jsonl`). 29/30 abstain-by-design is the
abstention discipline working AND a named build: the **election question adapter**, so
the register is not protest-only by October. Registered as a build item, not a physics
change.

## Sequencing

c-SHOCK (mechanism cycle) has the box first; Track 1 launches when it clears; Tracks 2
and 4 are data/register work that needs no compute. Freeze tag, 4M pilot, Epoch 4, and
any holdout spend wait for the founder's explicit word after c-SHOCK reports.

## Imports from VNF (registered, founder-ruled 2026-09-01)

Full audit: ops/alive/VNF_MECHANISM_AUDIT_2026-09-01.md. Four imports, nothing else:
1. **Multiverse pattern → the single typed question adapter** (all classes, not
   elections only): real Earth-1 branches via null_branch() (never logit shifts),
   force-distance readout (k-outcome softmax over −d(present, world_i), per-class
   FITTED temperature), abstention when branch ≈ control (noise floor), p_model the
   ONLY scored field (asserted in the scorer), market blend product-layer only.
   BIBLE v4.2.2 refinement 9. Module: earth1/adapters/multiverse.py.
2. **Keyless market endpoints** (Polymarket gamma public-search, Kalshi elections
   API, browser UA, jurisdiction/year/liquidity disqualifiers, immutable first-seen
   price) → prospective-register adapter.
3. **Ground-question ladder → ledger only** (EARTH1_GROUND_LADDER=v1): live-web rung
   writes hash-chained NewsItems (URL + snippet sha256), NO seed minting into judged
   corpora; forward-estimate rung returns Abstain at the type level; relevance rule
   "no seed match ⇒ R=0 for every force" adopted verbatim. No cron before XI.A.2.
4. **c3 confirmed** by VNF's premise/entity machinery; the never-abstaining legacy
   door is the registered anti-pattern.
