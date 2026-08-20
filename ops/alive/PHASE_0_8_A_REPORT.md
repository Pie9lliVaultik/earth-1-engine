# 0.8-A REPORT — the pinned force field: diagnosis complete

Battery pre-registered in PHASE_0_8_A_FORCE_FIELD.md. All instruments
ran on prime clones/fresh worlds; production untouched. Artifacts:
`data/force_census_*.json`, `data/force_ablation_0_8/`,
`data/force_tau_0_8/tau_map.json`.

## A1 — state census (production day-1142 vs genesis)

| | production | genesis |
|---|---|---|
| ALPHA (conviction) mean | **0.9999** | 0.419 |
| agents with α > 0.99 | **100.0%** | 0.0% |
| FEAR | 0.974 (83% > 0.95) | 0.53, sd 0.11 |
| COLLECTIVE | 0.988 (91% > 0.95) | 0.65 |
| CULTURE | 0.883 (59% > 0.95) | 0.55 |
| IDENTITY | **0.0001 (100% < 0.05 — dead)** | 0.40 |
| TEMPERAMENT | 0.088 (33% at floor) | 0.48 |

Five of eight channels railed; every living agent at maximal
conviction.

## A3/A4 — endogeny and ablation (fresh 200k, no news, 365 days,
common seed, three arms)

- **The conviction ratchet completes in ~15 days** in every arm:
  α ≥ 0.9 by day 11, ≥ 0.99 by day 15-16 (baseline / decay-on /
  beta=1 identical to within one day).
- **The pre-registered decay arm does not arrest it.** Root cause is
  structural: the registered decay is isolation-scaled
  (`decay × 1/(1+degree)`); at typical degree ~25 its maximum bite is
  ~0.0008/day against a hardening gain of up to 0.06/day. It is ~75×
  too weak by construction, not by parameter value.
- **Endogeny confirmed**: with no news at all, channels rail on the
  same trajectory production shows — IDENTITY 77% at floor within a
  year (production: 100%), COLLECTIVE/CULTURE ~50% railed and
  climbing, FEAR 0.57 and rising (production, 2 years further along
  a 2026-GDELT fear diet: 0.97). News steers WHICH bound; the
  pinning itself is intrinsic dynamics.
- beta (1.0 vs 2.0) is irrelevant to the ratchet.

## A5 — restoring-force map (production clone, 100k-agent cohort,
±0.10/±0.20 per channel, paired controls, placebo)

**Half-life of any force perturbation: 0.5–1.2 days, every channel,
every direction.** <1% of any injection survives 10 days. Placebo
decay measured exactly 0.0 (the instrument cannot manufacture decay).
For comparison, the attitude-persistence literature puts real
opinion/affect shifts at weeks-to-months half-lives.

## Mechanism attribution — the full chain

1. `update_conviction` hardens α by `0.06 × (agreement − 0.5) × 2`
   per day. Genesis homophily ⇒ agreement > 0.5 nearly everywhere ⇒
   net positive drift ⇒ **α = 1 for the whole population in two
   weeks**. The designed counterweight (isolation decay) cannot act
   on connected agents; nothing else opposes the ratchet.
2. At α = 1, propagate's averaging term (`inv_a = 1 − α`) is
   EXACTLY zero: only pole-alignment dynamics remain — a source at
   0.61 pulls you toward 1.0, unanimously, at maximal weight.
3. Pole-only dynamics rail each channel to its initial-majority
   bound; sd collapses; agreement in a railed unanimous
   neighborhood = 1, which keeps α clipped at 1 — **an absorbing
   state**.
4. The designed pull (`life_force_target`, relax 0.25/day toward
   lived circumstances — whose own docstring warns: "a world with
   only the push saturates to the poles and freezes") erases
   individual perturbations in ~1 day but cannot unrail a channel
   whose push is unanimous.

This one chain explains every queued pathology: FEAR ceiling and the
dead opinion pole (probe + v1 study), shock erasure (v2/v3 + tau
map), "diffusion adds no value" (nothing left to diffuse),
"trait variance too narrow" (feedback residue of railed channels),
and IDENTITY's silent death.

## Fix program (proposal — for founder ruling; nothing implemented)

Standing rule honored: this is a structural defect with a documented
designer intent that the implementation fails to realize (the decay
exists but is scale-crippled; the docstrings assert dynamics the code
cannot produce). That is the "contradiction → fix it" class, not
architectural preference. Proposed program:

1. RESEARCH: conviction/stubbornness dynamics with empirical
   grounding — Friedkin-Johnsen susceptibility anchoring (α baseline
   tied to the agent's `doubt` trait), symmetric agreement measured
   on continuous force distance (pole-fraction agreement cannot
   register disagreement in a railed world), and a mean-reverting
   term −λ(α − α0_i) replacing the impotent isolation decay. λ and
   the law are selected by EVIDENCE: candidate laws A/B'd against
   external persistence moments (WVS wave-to-wave attitude
   stability), never hand-picked for pretty behavior.
2. IMPLEMENT the selected law behind the 0.8 A/B machinery
   (registered arms, production untouched until accepted).
3. ABLATE: re-run this exact battery (census, endogeny, tau map) on
   the candidate; the ratchet must not complete; channels must hold
   variance; shock half-lives must move toward evidence-scale.
4. RETEST: outcome probe rerun (does the opinion pole come alive
   when lived state changes?), then the chaos chapter (butterfly,
   FSLE, noise floor, consciousness profile) measured on the
   UNPINNED field — measuring chaos constants of a frozen field
   first would waste the compute and the claim.

Separately flagged, NOT bundled into this fix: relax = 0.25/day
(the ~1-day erasure speed) is a calibration question against
attitude-persistence evidence — one change at a time.
