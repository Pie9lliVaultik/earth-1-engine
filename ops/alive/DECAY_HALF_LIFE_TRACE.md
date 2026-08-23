# decay_half_life — contract trace (COMPLETE; semantics RECOVERED)

The dead field's history, from git:

1. BORN in f933c59 ("Builds 16-25: Emergence architecture"), where it
   was FULLY CONSUMED: `detect_transitions` honored `cooldown_days`
   per (rule, key) via a last_fired map, and passed
   `decay_half_life` into a `WorldEvent`.
2. The legacy `EventLog` applied events as a READ-TIME DECAYING LEVEL
   SHIFT: `effective_deltas_vectorized` summed
   `force_deltas × 2^(−Δt/half_life)` for active events and the
   engine added the result as a projection shift — a pure LEVEL
   contribution, never integrated into stored forces. The
   architecture's own "LEVEL MAP, NOT ACCUMULATION" law, correctly
   implemented in the legacy event system.
3. The 0.2-unification port of cascades into alive.py kept the
   dataclass but ported only conditions + INSTANT PERMANENT force
   writes — losing BOTH the cooldown (repaired in probe 1, founder
   contract, flag-gated) AND the decaying-residue semantics (this
   field).

## Resolution class: SEMANTICS RECOVERABLE → implement exactly

A fired cascade should contribute a decaying level term
`effects × 2^(−Δt/decay_half_life)` for its locality, read-side
(naturally: a term in life_force_target for affected agents),
starting at fire time, alongside the honored cooldown. NOTE
(founder's no-merge instinct vindicated): Chronicle presses are
integrator-form (equilibrium-bounded via relax); the legacy event
shift is pure level — same decay mathematics, DIFFERENT application
semantics. They remain separate mechanisms.

## Next step (per ruling; not bundled into IT12)

Implement the recovered semantics exactly in an isolated
experimental branch with contract tests (fire → shift present at
declared magnitude → halves at declared half-life → cooldown
interplay → restart-persistent), then a targeted regression/ablation
against the frozen candidate before the full 0.8 battery, since
activating it materially changes cascade dynamics (events become
fading pressures rather than permanent instant writes — likely
REDUCING their long-run footprint).
