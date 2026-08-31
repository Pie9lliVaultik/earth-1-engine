# EXPERIENCE LOOP v0.2 — PREREG (frozen before any cycle runs)
2026-08-31. Founder GO with one binding condition: the baseline set
includes an INFORMED NON-LEARNER — the learner's observation access,
no update rule. Beating that arm is the demonstration.

## Changes vs v0.1 (each mapped to a v0.1 failure)
1. POWER: 16 well-specified + 4 misspecified sealed truths (seeds
   9201–9220; MIS = 9217–9220 with β=3.0, hardship_gain=2.0). v0.1's
   17% naive-blind win was underpowered at 8 worlds.
2. COVERAGE DIAL: observation-noise inflation halved (offsets scaled
   0.5×) — v0.1 overshot 0.74→0.99 against a ≤0.97 band.
3. G7 RE-SPEC: paired experiential-vs-placebo log-CRPS (CI excludes 0
   favouring experiential). v0.1's coded form wrongly punished the
   placebo for beating frozen.
4. SHARP SHOCKS: the registered memory-probe shocks were smoothly
   decaying and a smoother tracked them. v0.2 forcing = branch-engine
   scenario at days 240 and 480 (firm_damage 0.25, trade_shock 0.15,
   forces {fear +0.2}, persists 60 d), applied identically to truth
   and every simulated world (known u_t). G8 unchanged: experiential
   must beat naive-blind on shock cycles {8, 9, 16, 17}.
5. NEW ARM — INFORMED NON-LEARNER ("filter", the founder condition):
   identical particle machinery and observation access as the
   experiential arm, but NO persistent update: per cycle, weights are
   computed fresh from THAT window's observation distance only (no
   multiplicative accumulation, no resampling, θ fixed at prior draws
   forever). It may condition on what it just saw; it may not learn.
   PRIMARY GATE G1c: experiential beats filter on late cycles, paired
   log-CRPS CI excluding 0. This isolates parameter learning from mere
   state conditioning.
Everything else identical to v0.1 (24×30d cycles, 20k, eligible θ =
relax/memory_press, receipts, replay, blinding, G2/G3/G4/G6).
EXPERIENTIAL_LEARNING_DEMONSTRATED = YES iff
G1 ∧ G1b(naive-blind) ∧ **G1c(filter)** ∧ G7' ∧ G8 ∧ G2 ∧ G6.
Compute: 20 worlds × (3×64-particle arms + frozen) ≈ 2.5–3 h at
~60 slots on idle prime.
