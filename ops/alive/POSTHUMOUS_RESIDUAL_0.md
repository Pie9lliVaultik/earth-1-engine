# POSTHUMOUS-RESIDUAL-0 — causal audit of the six unmasked `civ.adj` consumers (v4, main 9b7dd67)

Method: 3k world, day 5; living ego with a connected alter; alter killed and
frozen for one tick (edge ego→alter weight 2.0 still present); deterministic
counterfactual = identical world + RNG, only the dead alter's relevant field
changed, one consumer update executed, living ego's next state compared.

| consumer | read path | dead alter in neighbour set? | dead state read | living state affected? | persistence or agency? | violation |
|---|---|---|---|---|---|---|
| `life.life_force_target` (canonical, every day) | `shared = (adj @ deprivation)/deg` → COLLECTIVE target `+0.40·(dep_ego·shared − REF)` | YES | frozen `life.deprivation` of the dead | **YES** — ego dep 0.5: COLLECTIVE target 0.50166 → 0.54872 (Δ +0.047) when the dead alter's deprivation is 0 vs 1 (insensitive only when the ego's own deprivation is 0) | the dead person's frozen *personal material state* acts as today's "shared hardship" on a living psyche — **current social agency** | **YES** |
| `knowledge.knowledge_tick` | `nb = (adj @ stock)/deg` → learning gap; `peers` counts scientists restricted to `live` | YES (nb); NO (peers) | frozen `knowledge.stock` | yes, small (Δ stock 2.1e-5 per day) | what a person knew keeps circulating among those who knew them — **informational persistence** (the model's explicit artifact channels `living_works`/`global_stock` are separate and unaffected) | NO (flag: mediated by a personal field; acceptable under the informational-persistence clause) |
| `flourishing.flourishing_tick` | `near_knowing = (adj @ stock)/deg` → curiosity target; `art_flow = (adj @ works_made>0)/deg` → art_received/meaning | YES | frozen `stock`, `works_made` | yes (curiosity Δ 4.3e-4; art_received Δ 2.4e-3) | works made in life keep being received; knowledge nearby persists — **informational/artifact persistence** | NO |
| `institutions.class_tick` | `deg = adj.sum(axis=1)` used only for `alone` when `life.relationship is None` (never in canonical) | YES (degree) | nothing (count only) | NO (Δ 0 with alter wealth −500 / dep 1) | inert | NO |
| `memory.Chronicle.spread` | `exposure = (adj @ scope)/deg`; a memory held by the dead can reach their living ties (exposure 0.235 for the ego) | YES | `scope` membership (a memory that happened to the dead) | yes (probabilistic catch) | stories of the dead travel to those who knew them — **memory/relational persistence** (explicit legacy channel, ruling 2026-08-23) | NO |
| `life.couple_life_to_forces` | same `shared` term | YES | frozen deprivation | NOT REACHED — `live_one_day` calls `life_tick(couple_forces=False)`; function is not on the canonical path | inert (legacy) | NO |

## Verdict
**POSTHUMOUS_RESIDUAL_0: VIOLATION** — one path: the shared-hardship term of
`life_force_target` (GEO-1 COLLECTIVE law, slope 0.40) treats a dead alter's
frozen deprivation as today's hardship of the ego's circle. Under v3 the same
term read the dead alter's *drifting* deprivation (dead rows kept living
material lives), so this is not new in v4 — v4 left it untouched. It is the
only remaining path by which a deceased person's personal psychological/
material state acts on a living person as a current social input.

## Minimum correction (NOT applied — reported for ruling)
In `alive.live_one_day`, compute `shared` over living alters only: pass the
already-built living view into the target law —
`life_force_target(civ, life, w.flourishing, adj=adj_live)` with
`shared = (adj_live @ dep) / max(deg_live, 1)` (one optional keyword argument
on `life_force_target`, default = `civ.adj` so every other caller and the
GEO-1 KA battery are unchanged). No threshold, slope or reference constant
changes. Living-only `deg` also removes the dead from the "lonely" fallback
denominator. Blast radius: Stage A (COLLECTIVE target every day), C (cascade
substrate), H — all already inside the 16 targeted regressions; the GEO-1 KAs
inherit (they plant neighbourhoods of living agents). Expected magnitude:
bounded by 0.40 × dep_ego × (dead share of tie weight × dead deprivation) —
below 0.01 at 1–2 % dead, material at Epoch-1-like 17 % dead.

## Bookkeeping correction
Escalation reserve = **+8 actual runs** (A +2, C +1, FSLE remaining +5), not +4.

## Closure (founder ruling: one semantic correction, minimal patch)
Rule applied: **current social computation uses living neighbours; explicit legacy substrates persist.**
Membership-ablation check (dead edge present vs excluded, same world/RNG): knowledge and flourishing respond to membership alone (Δ 8e-6 / 2.6e-4); `class_tick` inert; `life_force_target` responds to the dead alter's state when the ego is deprived (Δ +0.047).
Patch (v4.1 RC): one living view built per tick after deaths/rehoming and passed to `knowledge_tick` (neighbour stock + scientist peers), `flourishing_tick` (near-knowing, art_flow — durable works persist through `living_works`/`global_stock`), `life_force_target` (shared hardship; optional `adj=` kwarg, default unchanged), propagate/conviction/feedback/feed (already); plus two more same-bug manifestations found by the invariant test: `mobility` flight mixing drew a random host from ALL rows (now living hosts), and `institutions.govern` aggregated national deprivation/FEAR over all rows (now living; the institution's state persists). `Chronicle.spread` unchanged (explicit memory substrate); `couple_life_to_forces` unchanged (inert). No coefficient, reference, half-life or ontology change.
Invariant test G (`tests/test_posthumous.py`): perturbing every personal field of 40 deceased rows (forces, alpha, deprivation, wealth, stock, works, traits) leaves every living row's next state bit-identical across forces, alpha, knowledge, flourishing, life; a memory held only by the dead still spreads to the living. Estate 1,107 pass.
