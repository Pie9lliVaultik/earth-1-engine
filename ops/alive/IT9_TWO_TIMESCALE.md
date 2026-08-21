# 0.8 IT9 — TWO-TIMESCALE PERSISTENCE (pre-registered)

IT8 (dcf2b2f) accepted: 0/2; slow-uniform-relax persistence is
structurally incompatible with bounded impulses and diversity
(writer displacement ∝ rate/relax). IT9 tests the two-timescale
hypothesis: fast transient response + slow adaptation of the
person's baseline.

## Frozen base candidate

Exact IT8 Candidate-B system with relax RESTORED to 0.045:
k=3, μ=0.0167, dyadic conviction (gain 0.003), flourishing
level-map, cascade cooldown, dyadic feed, contagion ambient off,
event impulses UNCHANGED (no retuning), 200k, 120d, fresh-seed
evaluation (seed 8901), clustered day-90 fork.

## The one new mechanism — adaptive baseline

Semantic verification (registered): `life.force_baseline` is the
documented setpoint ("an agent who has lived through something does
not return to who they were" — life.py) and feeds life_force_target
as the base of every channel. It IS the state being modeled; no
overloading of unrelated fields.

LAW (derived, one candidate):
    b ← clip(b + λ_adapt · (F − T), 0, 1)   applied once per day,
    all 8 channels, where T = life_force_target(civ, life).

REGISTERED DERIVATION NOTE: the ruling's nominal form λ(F − b)
violates its own KA3 constraint BY CONSTRUCTION — with T = b +
circumstance offsets, a stationary world gives F−b ≈ offsets ≠ 0
and the baseline ratchets unboundedly (computed: 0.45 drift/30d at
λ=0.05 with a 0.3 offset — the flourishing-bug pattern reborn).
The (F − T) form is stationary-stable (F≈T ⇒ no drift), signed,
bounded, symmetric, and captures exactly the UNEXPLAINED deviation
(shocks), which is the semantic intent. This choice is forced by the
registered constraints, not aesthetic.

λ_adapt derivation (frozen; discrete dynamics, measured fast rate
r = ln2/5 from the corrected system's tau): day-30 residual targets
{0.2, 0.4, 0.6} ⇒ λ ∈ {0.0396, 0.1072, 0.2414}. The single scored
candidate is the registry-center point λ* = 0.1072. The band-edge
values are the documented evidence bracket, NOT a search grid.

## Adaptation-specific known-answer controls

KA1 λ=0: must reproduce the fast-transient/insufficient-residual
     failure (resid ≈ 0.07–0.14 at relax 0.045).
KA2 λ×10 (=1.072, clipped meaning near-instant capture): must FAIL
     by over-persistence (resid > 0.6 and/or tau > 15).
KA3 stationary: unshocked world, |mean Δb| over days 90–120 must be
     < 0.01 on every channel (no drift, no random walk).
KA4 sign: matched ±0.15 impulse forks must shift the cohort baseline
     in matching directions with |Δb+| ≈ |Δb−| (ratio ∈ [0.5, 2]).
KA5 transient vs sustained: a 1-day impulse vs a 15-day sustained
     exposure of equal magnitude — the sustained exposure must leave
     a materially larger durable baseline shift (≥ 2×).

Plus the full standing battery (zero/instant/pull/frozen/degtgt/
fastmix/ratchet/KAdis set). Any KA misbehaving ⇒ VOID.

## Two-timescale reporting (never collapsed into one tau)

Per scored arm: fast half-life; day-30 residual; cohort baseline
displacement Δb; fraction of terminal force change carried by
baseline vs live force; recovery trajectory after driver removal
(sustained-fork release phase).

## Acceptance — all standing gates unchanged

tau [5,15] + resid [0.2,0.6] · clustered ring1 [0.006,0.15],
ring2 ≥ 0.0005, ring3 > 0 · sat < 20% all channels · sdr ≥ 0.5 ·
unanimity < 50% · α interior/heterogeneous · KAdis behaviors ·
no-news stability. A good persistence curve excuses nothing else.

## Stop rule / advancement

Fail → STOP; no tuning of λ, relax, impulses, or dose; diagnose
(law form / baseline semantics / transient-vs-sustained failure /
another writer / target mismatch). Qualify → FREEZE the exact
system, no further force-law tuning, advance unchanged to the full
chain (365-day endurance, adversarial battery, census, two-timescale
map, transmission validation, India recession rerun, opinion causal
receipt, canonical chaos remeasurement) → only then Epoch-2
eligible. Production untouched.
