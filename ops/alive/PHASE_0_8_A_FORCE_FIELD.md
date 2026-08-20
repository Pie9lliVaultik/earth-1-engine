# 0.8-A — the pinned-force-field investigation (pre-registered battery)

First 0.8 deliverable (founder ruling, 2026-08-20). Hypothesis under
test, assembled from three independent evidence lines (FEAR ≈ 0.978
in production; −0.20 shocks ~98% erased in 3 days; audit findings
"diffusion adds no value" and "trait variance too narrow"):

    H-PIN: the force field is pinned — some combination of the
    conviction ratchet (decay disabled), the pole-expansion
    propagation law, relaxation, and the news diet holds force
    channels at their bounds and erases perturbations far faster
    than social dynamics plausibly should.

Standing rule applies: no parameter changes to obtain desirable
behavior. This battery DIAGNOSES; any fix must then pass
evidence → diagnosis → research → implementation → ablation → retest.

## Instruments (all on prime, disposable clones/worlds; production
untouched)

A1. STATE CENSUS — production day-1142 snapshot, no simulation.
    Per-channel force mean/sd/deciles, pole share, saturation shares
    (>0.95, <0.05); alpha (conviction) distribution + ratchet check;
    trait (openness/doubt/desire) variance; the same census on a
    fresh genesis world for contrast.

A2. SATURATION HISTORY — the same census on every dated Storage Box
    backup epoch available (relayed via the box), locating WHEN each
    channel pinned in world history.

A3. ENDOGENY TEST — fresh 200k world, NO news, 365 days, daily force
    means/sds/saturation shares + alpha trajectory. If saturation
    reproduces with no information stream, the cause is endogenous
    dynamics, not the 2026 news diet.

A4. MECHANISM ABLATION (fresh 200k worlds, 120 days, common seeds),
    factorial arms — diagnosis clones, never production:
      a. baseline (CANONICAL_DAY);
      b. conviction-decay ON — the PRE-REGISTERED 0.8 A/B arm B
         (earth1/influence.py `_experimental_decay_0_8_ab=0.02`,
         registered at 0.1 and never taken in production);
      c. beta=1.0 (alignment weight linear — the old reduced-system
         value) vs the canonical beta=2.0;
      d. no-memory-pressing (empty chronicle — automatic in a no-news
         world; arm kept for completeness at 0 cost).
    Readouts: per-channel trajectories, saturation shares, alpha
    trajectory, and shock-recovery tau (−0.2 FEAR to 25% of agents at
    day 60; erasure half-life).

A5. RESTORING-FORCE MAP — production-snapshot clones: inject ±0.10
    and ±0.20 on each of the 8 channels for a random 100k-agent
    cohort; measure the perturbation L2 decay daily for 10 days →
    per-channel, per-direction half-life map. Quantifies "excessive
    restoring" as a number, not an anecdote.

## What would falsify H-PIN

Census showing channels well inside bounds with healthy variance;
tau half-lives of order weeks; A3 fresh world NOT saturating; A4
arms indistinguishable. Every instrument can fail (Standing Rule 2):
A5's placebo is a zero-magnitude injection whose measured decay must
be exactly 0; A3/A4 share seeds so arm differences are attributable.

## Deliverable

0.8-A baseline report: the census, the history, the tau map, the
ablation attribution — and a diagnosis stating WHICH mechanism(s)
pin the field, with effect sizes, before any fix is proposed.
