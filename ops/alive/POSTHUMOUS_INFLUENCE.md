# POSTHUMOUS INFLUENCE — founder physics ruling 2026-08-23

Principle: DEATH ENDS ACTIVE AGENCY, NOT LEGACY OR CAUSAL INFLUENCE.
Code: `main` (this commit). `PHYSICS_VERSION` → `0.8-candidate-v4/posthumous-invariant`.
NOT DEPLOYED: Epoch 2 runs `0.8-candidate-v3/39994f0-canonical`; by
EPOCH_POLICY a deployed physics change ⇒ new epoch, and Bible 0.8 is
being measured on Epoch 2's physics right now. Deployment = Epoch 3,
by ruling only.

## 1. Decomposition — every path from a deceased row to the living (canonical `main` before this change)

| pathway | source | class | what happened after death |
|---|---|---|---|
| dyadic propagation | `influence.propagate` ← `civ.adj` (no alive mask) | ACCIDENTAL_NUMERICAL_CARRYOVER | dead rows sampled as partners while any typed edge to them survived; `plasticity_tick` prunes `alive[erows]&alive[ecols]` only for the tie types it rewrites that tick, so edges into the dead persisted for days (1,897 edges into 124 dead at 20k/day 200) |
| relaxation toward today's target | `alive.py` relax step (all rows) | ACCIDENTAL | dead rows kept reacting to today's circumstances |
| conviction | `influence.update_conviction` (scratch evidence, all rows) | ACCIDENTAL | dead hardened/softened from encounters |
| susceptibility | `susceptibility.compute` (transient, all rows) | ACCIDENTAL (harmless: only gates the row's own move) | — |
| media feed | `feed.feed_tick` ← `w.feed` (no alive mask; hubs are agent rows) | ACCIDENTAL | a dead hub kept broadcasting; dead rows kept consuming |
| neighbourhood feedback (traits) | `alive.py` step 10 `civ.adj @ forces` | ACCIDENTAL | dead neighbours entered living agents' local mean; dead traits kept drifting |
| material life | `life.life_tick` (no alive mask anywhere in `life.py`) | ACCIDENTAL | dead rows stayed employed, drew wages, paid costs, accrued wealth/deprivation, mental/physical/relationship/political state kept evolving, counted in firm payrolls and in `/world` unemployment |
| ageing | `generational.advance_age` (all rows) | ACCIDENTAL | the dead aged |
| cascade detector | `alive.py` step 9: `met` over all rows, `pop_l` over all rows | ACCIDENTAL | dead residents counted in locality fractions (both numerator and denominator) |
| memory press | `memory.Chronicle.tick` writes forces for `scope` incl. dead | HISTORICAL_RECORD_ONLY (effect on the dead row is meaningless) | — |
| bereavement | `health.health_tick`: ties of the newly dead get social_need +0.15, mental −0.08 (computed from `civ.adj @ died` on the death day) | POSTHUMOUS_LEGACY (explicit) | unchanged |
| memories including the deceased | `Chronicle.events[].scope`; `Chronicle.spread` along `civ.adj` of scope members | POSTHUMOUS_LEGACY (explicit) | unchanged — a memory persists, presses living scope members and spreads along their ties regardless of the deceased row's dynamics |
| inheritance | `rebirth.apply_rebirth` from a LIVING parent | POSTHUMOUS_LEGACY (generational) | unchanged |
| household membership | `fabric.household` | HISTORICAL_RECORD_ONLY | unchanged (never erased) |
| typed social edges | `fabric.by_type` pruned by `plasticity_tick` when a tie type is rewritten | **GAP** (pre-existing 0.7 contract): relationship existence IS eventually erased by pruning | NOT changed here (no redesign); recorded |
| institutions / class / knowledge / flourishing / weather / mobility / contagion | each takes `alive=` | already living-only | — |
| rebirth / slot reuse | `alive._be_born` → `rebirth.apply_rebirth` (complete reset) | correct | unchanged |

## 2–3. Implementation (minimal; `earth1/alive.py` only)

1. `_snapshot_deceased` at tick start for rows dead at tick start;
   `_restore_deceased` at tick end (before births): `civ.forces, alpha,
   openness, doubt, desire_intensity, age` and 26 `life` arrays — the
   last living state (end of the death day) is preserved and inspectable;
   no ordinary living-agent update touches it again.
2. `_living_view(adj, alive)`: a per-tick view of the graph with every
   edge INTO a dead row zero-weighted (`eliminate_zeros`), used by
   `propagate`, `update_conviction`, the trait feedback, and the feed.
   The stored graph is untouched — no edge deleted.
3. Cascade detector: `met` and `pop_l` over living residents only.
4. Release at death (idempotent, after restore): `employed=False,
   in_lf=False, firm=-1` — a death ends employment.
No parameter changed; no new posthumous physics; rebirth untouched.

## 4. Memory system as the legacy channel
- Memories associated with deceased Earthlings persist: YES (`Memory.scope` is a mask; nothing removes the dead from it; salience decays on its own half-life).
- Living Earthlings keep carrying/spreading them: YES (`Chronicle.tick` presses living scope members; `Chronicle.spread` samples ties of scope members).
- Does any posthumous influence require the corpse row to be dynamically active: NO — bereavement is computed on the death day; memory/spread read scope, not the row's current forces; inheritance reads living parents.
- Would masking destroy legitimate effects: NO — test C shows a memory that includes the deceased still moves the living with the invariant on.

## 6. Acceptance tests — `tests/test_posthumous.py` (6/6 PASS; estate 1,100 pass / 6 skip)
A no continued agency · B no ordinary peer action (perturbing dead rows leaves the living bit-identical) · C legacy survives (bereavement; memory incl. deceased still acts) · D relationship history (household + final state + cause of death preserved; edge-pruning gap recorded) · E rebirth contract intact · F persistence (save/load + deepcopy).
Trajectory pin `test_perf_equivalence` re-pinned 6b289fb1… → 8d44efb5… under this ruling.

## Magnitude (20k, day 200, 30 days, invariant vs corpse-active twin)
dead 0.62%; living stored forces |Δ| mean 0.0007, max 0.060; population means equal to 3–4 dp. Small now; grows with the dead fraction (Epoch 1 ended at 17% dead).

## 7. Result
ACTIVE AGENCY AFTER DEATH CURRENTLY PRESENT: YES (before this change)
EXPLICIT POSTHUMOUS INFLUENCE PATHS: bereavement at death (health_tick); chronicle memories whose scope includes the deceased (press + spread); inheritance at rebirth from living parents; household membership record
ACCIDENTAL CORPSE-INFLUENCE PATHS: dyadic propagation partners via unpruned edges; feed broadcasting/consumption; neighbourhood-mean trait feedback; relaxation; conviction; life_tick (employment, wages, wealth, needs, mental/physical state); ageing; cascade locality fractions
DOES LEGITIMATE POSTHUMOUS INFLUENCE REQUIRE CORPSE FORCE UPDATES?: NO
IMPLEMENTATION CHANGE MADE: freeze-and-restore of deceased rows' living-agent state per tick; living-only graph view for propagation/conviction/feedback/feed (no edge deleted); living-only cascade fractions; release of employment at death. PHYSICS_VERSION 0.8-candidate-v4/posthumous-invariant on main; NOT deployed (Epoch 2 unchanged; Epoch 3 by ruling).
LEGACY/MEMORY INFLUENCE PRESERVED: YES
TEST RESULT: 6/6 acceptance PASS; full estate 1,100 passed, 6 skipped
GAP RECORDED: typed edges to the deceased are eventually pruned by plasticity (pre-existing), so relationship EXISTENCE is not durable beyond household membership; a historical-relationship store would be new design — not done.
