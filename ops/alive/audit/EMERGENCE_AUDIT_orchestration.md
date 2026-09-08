# CLUSTER 6 — ORCHESTRATION AND CROSS-CUTTING (`earth1/alive.py` + composition)

All paths relative to `/Users/pietronovelli/Documents/GitHub/earth-1-engine`. Read-only audit; nothing changed.

---

## 0. The canonical order of operations, as the code actually executes it

`live_one_day` (`earth1/alive.py:219–577`). The docstring's numbered list (`alive.py:6–15`) is **not** the execution order; the real order is:

| # | step | file:line | writes that later steps read *this same tick* |
|---|---|---|---|
| 0 | snapshot rows dead at tick start | `alive.py:245–247` | `_frozen` (restored at 543) |
| 1 | `govern` | `alive.py:248` | `gov.welfare/policing/tax/legitimacy/at_war_with` |
| 2 | `apply_policy_and_war` | `alive.py:249` | `life.policy_net`, `civ.forces[FEAR,COLLECTIVE]` for warring countries, `life.firm_health`, kills |
| 3 | `advance_age` | `alive.py:257` | `civ.age`, `civ.age_bucket` |
| 4 | `life_tick(couple_forces=False)` | `alive.py:260` | `life.deprivation`, `wealth`, `employed`, `mental`, `addiction`, `relationship`, `social_need`, `firm_health`, `lost_idx/found_idx` |
| 5 | `health_tick` | `alive.py:265` | `health.alive/condition/declining`, `life.social_need/mental` (bereavement) |
| 6 | `class_tick` | `alive.py:268` | `klass.homeless/criminal`, `civ.country` (migration), `life.wealth`, `migrated_idx` |
| 7 | rehome (conditional) | `alive.py:275–292` | `fab.by_type`, `civ.adj` |
| 8 | build `adj_live` | `alive.py:300` | the living-graph view for 9, 11, 13, 18, 21 |
| 9 | `knowledge_tick` | `alive.py:301` | `kn.stock/status/global_stock`, `discoveries_today`, `works_today` |
| 10 | `weather_tick` | `alive.py:307` | `civ.forces[FEAR]`, `life.wealth/wage/firm_health`, kills |
| 11 | `flourishing_tick` | `alive.py:313` | `fl.hunger/thirst/hope/curiosity/meaning/belonging`, `life.physical`, kills |
| 12 | `life_force_target` | `alive.py:321` | `target` (8-channel restoring attractor) |
| 13 | homeless target override | `alive.py:326–330` | `target[FEAR] += .25`, `target[COLLECTIVE] −= .20` |
| 14 | `susceptibility.compute` | `alive.py:364` | `sus` — gain used by 15, 16, 17 |
| 15 | `propagate` (dyadic, k=3) | `alive.py:370–372` | `civ.forces`, `scratch` |
| 16 | `contagion_tick` + `shared_attention` | `alive.py:380–385` | `civ.forces`, `life.mental` |
| 17 | `mobility_tick` | `alive.py:390` | `civ.forces[CULTURE,EXPERIENCE]`, `life.relationship/cost`, `health.condition`, kills |
| 18 | `feed_tick` | `alive.py:397–399` | `civ.forces`, `scratch` |
| 19 | **relax toward target** | `alive.py:402` | `civ.forces` |
| 20 | `update_conviction` | `alive.py:403–404` | `civ.alpha`, zeroes `scratch` |
| 21 | `plasticity_tick` | `alive.py:412` | `fab.by_type["friends"/"weak"]`, `civ.adj` |
| 22 | `chronicle.tick` + `spread` | `alive.py:415–416` | `civ.forces`, memory scopes |
| 23 | cascade detector | `alive.py:419–524` | **only** `chronicle.cascade_residues` / `cascade_last_fired` / `cascade_episode_active` |
| 24 | trait feedback | `alive.py:527–533` | `civ.openness`, `civ.doubt`, `civ.desire_intensity` |
| 25 | restore deceased | `alive.py:542–543` | undoes 1–24 for rows dead at tick start |
| 26 | widow / de-employ the newly dead | `alive.py:546–552` | `life.partner`, `employed/in_lf/firm` |
| 27 | `_be_born` | `alive.py:553` | whole-agent reset via `rebirth.apply_rebirth` |
| 28 | mortality identity, `w.day += 1` | `alive.py:564–570` | `st["deaths"]`, `st["alive"]` |

---

## 1. `earth1/alive.py` — the tick itself

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Execution order of the ten stages | `alive.py:219–577` | **DESIGNED** | Hand-sequenced. The header's claimed ordering (`alive.py:6–21`) does not match the body — governments run before aging, contagion/mobility/feed run between propagation and relax, and stages "9 CASCADE" and "10 FEEDBACK" are reversed in effect (cascade writes nothing). |
| `CANONICAL_DAY = beta 2.0, residue .02, critical_fraction .12, relax .045, layers 2` | `alive.py:99–100` | **DESIGNED** | Hand-set constants. |
| `beta` and `layers` are *live* knobs | `alive.py:220, 224` | **ASSERTED — refuted by code** | Neither identifier appears anywhere in the body (verified by scan of lines 219–577). `propagate` is called at `alive.py:370–372` without `beta`/`layers`, and `influence.propagate` swallows them in `**_ignored` (`influence.py:236`). Two of five keys in the "one authoritative declaration" are inert. |
| Relaxation toward a per-agent attractor at 0.045/day | `alive.py:402` | **DESIGNED** | Time constant ≈22 days. This is the strongest single term acting on `civ.forces` per tick (compare `MU_INFLUENCE=0.05 × 3` encounters, `influence.py:165–166`). |
| The attractor's base is each agent's **genesis** force vector | `life.py:398` (`force_baseline=civ.forces.copy()`), consumed `life.py:763, 791` | **DESIGNED** | Every agent is permanently pulled back toward its birth forces. The cross-sectional force distribution is therefore anchored at genesis plus a bounded material modulation — structurally the same trap as the wage-kurtosis error. **Measurement needed:** force-channel moments (variance, kurtosis, bimodality) at day 0 vs day 120 with the relax term at 0.045 vs 0.0. |
| Newborn attractor = ½ parent + ½ population mean | `rebirth.py:360–361, 411–412` | **DESIGNED (variance sink)** | `force_baseline[newborn] = own new forces` where forces are a 50/50 blend with the living mean. Baseline variance contracts by construction across generations. Any long-run claim of widening force distributions must be measured against this. |
| Deceased rows take no living-agent update | `alive.py:123–132, 147–160, 245–247, 542–543` | **DESIGNED** | Snapshot/restore of 32 named arrays. |
| `civ.age_bucket` is *not* restored for the deceased | `alive.py:124–125` (list omits `age_bucket`) vs `generational.py:140` | **DESIGNED defect** | `age` is restored, `age_bucket` is not; for a dead row crossing 30/45/60/75 the two disagree permanently. |
| "Ages every slot, dead ones included" | `generational.py:133–136` | **ASSERTED — false in composition** | True of the function in isolation; `alive.py:542–543` undoes it. |
| The living-graph view masks dead alters | `alive.py:135–144, 300` | **DESIGNED, and stale** | `adj_live` is built at line 300, *before* `weather_tick` (307), `flourishing_tick` (313) and `mobility_tick` (390) kill anyone. Agents killed by heat, want or roads still carry full edge weight in this tick's `propagate`, `feed_tick`, `update_conviction` and trait feedback. |
| The posthumous rule is applied uniformly | `alive.py:294–299` (comment) | **ASSERTED — partially false** | `health.py:358` and `mobility.py:131` compute bereavement over `civ.adj` (the stored graph, dead rows included), not `adj_live`. |
| Encounter randomness is "common random numbers" | `influence.py:151–156, 242`; `feed.py:173` | **DESIGNED** | Private `default_rng(920000 + day)` / `default_rng(930000 + day)`. **Consequence not stated in the docstring:** the influence and feed uniform streams are a pure function of the day index and are *identical across every seed, every world, every branch*. A seed-ensemble has zero variance in the influence channel's draws; seed dependence enters only through graph structure. Also, tie-stream(day d) ≡ feed-stream(day d−10000) — a stream collision for runs past 10 000 days. |
| Day index is inconsistent across the tick | encounters use `w.day+1` (`alive.py:371, 398`); cascade bookkeeping uses `w.day` (`alive.py:508, 522`); health uses `w.day` (`alive.py:265`) | **DESIGNED defect** | Residue `day` and encounter seed refer to different days for the same tick. |
| Tick return is a flat dict assembled by successive `st.update` | `alive.py:234, 248–553` | **DESIGNED** | Later writers silently overwrite earlier keys. Known collisions: `health_tick`'s `"alive"` (`health.py:376`) overwritten at `alive.py:568`; `"deaths"` (`health.py:374`) preserved as `"disease_deaths"` (`alive.py:564`) and redefined as the gross identity `alive_start − alive_end + births` (`alive.py:566–567`). Key set is conditional (`rehomed_*` at 280/292, `cascade_residue_active` at 464, rent/mental blocks at `life.py:731–744`). |
| Mortality identity closes exactly | `alive.py:564–568` | **DESIGNED** | An accounting identity, not a measured property. |

## 2. `earth1/alive.py` — the cascade / phase-transition block

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Local (per-locality, per-agent-conjunction) threshold detection | `alive.py:420–479` | **DESIGNED** | Locality key `country*1000 + region*2 + urban`; fires at `frac >= critical_fraction (0.12)` with `pop_l >= 10`. |
| `TRANSITION_RULES` thresholds, effects, cooldowns, half-lives | `thresholds.py:29–70` | **DESIGNED** | Ten hand-set thresholds, five effect vectors. |
| `thresholds.MIN_PARTICIPATION = 0.25`, "an external anchor, not a tuned value… registered before the run" | `thresholds.py:81–98` | **ASSERTED — and unused** | The canonical tick never calls `detect_transitions`/`detect_and_append`; it uses `critical_fraction = 0.12` from `CANONICAL_DAY` (`alive.py:99, 479`). The Centola/Granovetter anchor does not govern the production world. |
| A firing writes forces | `alive.py:512–523` | **DESIGNED — no such write exists** | The only effect of a firing is appending `{rule, loc, day, effects, h}` to `chronicle.cascade_residues`. |
| Cascade residues decay and are served as a read-time overlay | `alive.py:163–216` | **DESIGNED** | `effective_forces` is explicitly read-only (`setflags(write=False)`, `alive.py:195–200`) and consumed by the readout layer only. |
| "Events modify forces, which may trigger further thresholds, creating emergent cascading dynamics" | `thresholds.py:1–5` | **ASSERTED — false on the canonical path** | The loop is severed by construction (PF-DECAY-2, `alive.py:332–339`). It exists only under `EARTH1_TEST_CLOSED_LOOP=1` (`alive.py:346–360`). **The cascade subsystem is an observer, not a dynamical component.** |
| Episode-entry semantics for `identity_collapse` / `collective_surge` | `alive.py:113, 448–498` | **DESIGNED** | Cold→hot transition only; hot→hot suppressed. |
| `cascades_fired` counts genuine collective transitions | `alive.py:511, 524` | **EMERGENT (as a statistic)** | The *count* arises from the interaction of the force dynamics with a fixed threshold and is not set anywhere. But it has no downstream effect, so it cannot participate in emergence — it can only report it. |

## 3. `earth1/alive.py` — demography

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Births come from "partnered people of fertile age" | `alive.py:585–587` (docstring) vs `alive.py:603–605` (code) | **ASSERTED — code disagrees** | The code tests `life.relationship > 0.55`, a continuous scalar. `life.partner` is explicitly inert: "STATE ONLY: no dynamics read it" (`partnership.py:4–5`). |
| Fertility hazard `tfr/(25·365)·0.5` | `alive.py:599–607` | **DESIGNED** | Calibrated per-country TFR. |
| "When births outrun deaths the population grows" | `alive.py:587–588` vs `alive.py:592, 608, 611` | **ASSERTED — false** | `free = flatnonzero(~alive)`; `n_new = min(conceived.sum(), free.size)`. Births can only occupy slots freed by death. Population is hard-capped at `civ.n` forever and a run with zero deaths has zero births. Growth is bounded above by the genesis array size. |
| Trait heritability 0.45, blended with the living mean | `alive.py:580`, `rebirth.py:347–349` | **DESIGNED** | Explicit contraction toward the population mean each generation. |
| Newborn forces = ½ parent + ½ living mean | `rebirth.py:360–361` | **DESIGNED** | See §1 variance-sink note. |
| Widowing on death | `alive.py:546–547`, `partnership.py:44–56` | **DESIGNED** | State only; nothing reads `partner`. |

## 4. Composition surfaces — what each subsystem contributes to the tick

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Governments read *yesterday's* mean FEAR as "unrest" | `institutions.py:154–155`, called `alive.py:248` | **DESIGNED coupling** | The single force→institution channel; only FEAR is read. |
| Welfare/policing regime switch at `legitimacy > 0.28 & tax > 0.22` | `institutions.py:165–170` | **DESIGNED** | Hard bifurcation. Which side of it a country sits on, and for how long, is **EMERGENT** (legitimacy is a state variable driven by dep/unrest relative to adapting norms, `institutions.py:176–189`). |
| Habituating norms `unrest_norm`, `dep_norm` (a = 0.002/day) | `institutions.py:176–189` | **DESIGNED** | Removes the steady-state legitimacy drain by construction. |
| War onset from unrest × illegitimacy | `institutions.py:194–196` | **DESIGNED hazard**, closure **EMERGENT** | Rate is designed; the fact that a war raises the fear that raises the next war's hazard is a real closed loop (L3). |
| Nuclear deterrence / escalation | `institutions.py:65–68, 206–217, 260–267` | **DESIGNED** | Fixed country list; no proliferation dynamics; one-way. |
| Correlated hardship: firms fail, everyone inside is laid off together | `life.py:459–463` | **DESIGNED mechanism**, resulting hardship correlation **EMERGENT** | Correlation across a firm's members is not drawn; it follows from shared `life.firm`. |
| Deprivation gradient form | `life.py:620–633` | **DESIGNED** | `HARDSHIP_MODE == "gradient"`; the comment at 621–628 is a historical measurement claim (30.5% at ~1.0) — **ASSERTED**. |
| Durable spending gated by FEAR | `life.py:593–605` | **DESIGNED coupling**, loop **EMERGENT** | The only force→household-budget channel in the engine (loop L1). |
| `couple_life_to_forces` — "material condition becomes force state" | `life.py:846–872`, called only when `couple_forces=True` | **ASSERTED — disabled** | `alive.py:260` passes `couple_forces=False`. The whole docstring describes a function that never runs in the canonical world. |
| Synthetic bereavement hazard | `life.py:674–675` | **DESIGNED noise** | An exogenous per-agent draw independent of any actual death, running *in parallel* with the real graph-mediated bereavement at `health.py:357–363` and `mobility.py:130–136`. The reported `"bereaved"` counter is designed; `"bereaved_by_death"` is emergent. Do not conflate them. |
| Age-dependent mortality (Armitage-Doll t⁵, falls 2×/decade, Gompertz) | `health.py:146–163, 198–212, 293–342` | **DESIGNED** | Fitted/parameterised hazards; the GM path normalises RR to mean 1 within age bins so "the age curve belongs to the life table by construction" (`health.py:312–317`) — explicitly designed, not emergent. |
| *Who* dies within a cohort | `health.py:309–341` | **EMERGENT** | RR = f(deprivation, illness, addiction), all of which are dynamical states. The composition of the dead is emergent; the count and the age curve are designed. |
| Fall→decline→isolation→further mortality cascade | `health.py:222–246`, feeding `weather.py:145–147`, `susceptibility.py:66` | **EMERGENT** | Interaction of health, life (`social_need`, `relationship`, `in_lf`) and weather frailty. Not set anywhere as an outcome. |
| Knowledge learning suppressed by deprivation | `knowledge.py:120` | **DESIGNED coupling** | |
| Status = f(wealth, occupation, stock, degree) | `knowledge.py:126–130` | **DESIGNED** | Recomputed as a level each tick; not accumulated. Its Gini is a derived statistic of designed inputs, not an emergent inequality process. |
| `global_stock` ratchet | `knowledge.py:140–147` | **DESIGNED (monotone by construction)** | +2.5e-6 per discovery, `min(1.0, …)`; can never fall. |
| Flourishing writes forces | `flourishing.py:250–260` | **ASSERTED — removed** | Comment is accurate: flourishing no longer writes forces; the terms moved into `life_force_target` (`life.py:823–842`). Any prose citing "flourishing_tick writes forces" is stale. |
| Susceptibility as a multiplicative gain on every influence move | `susceptibility.py:42–78`, applied `alive.py:364, 372, 382–385, 399` | **DESIGNED form**, its population distribution **EMERGENT** | Eleven hand-set coefficients over age, alpha, mental, addiction, social_need, hunger/thirst, hope. |
| Emotional contagion (locality mean + gathering mean) | `contagion.py:57` `CONTAGION_GAIN = 0.0`; applied `contagion.py:207–239` | **ASSERTED — inert** | Both passes evaluate `clip(col + 0·(mean − col))` — algebraic no-ops. The 40-line module docstring (`contagion.py:1–40`) describes a mechanism that does nothing. **Only** the crowd/riot block (`contagion.py:241–272`) writes. |
| Crowds and riots | `contagion.py:244–272` | **EMERGENT** | Fires on the conjunction of `forces[FEAR] > 0.82`, `deprivation > 0.35`, `gathering >= 0`, at ≥38% of a locality of ≥20. Three subsystems (influence/target dynamics, life's deprivation, contagion's gathering draw) must interact. **Measurement needed:** riot rate vs the historical claim "mean fear sits near 0.85" (`contagion.py:76–79`) — that is a pre-canonical measurement and the target map has changed since. |
| Shared national attention (sport) | `contagion.py:107–146` | **DESIGNED** | Poisson national events, fixed ±0.05/0.035 writes. |
| Weather as correlated place-shock | `weather.py:114–190` | **DESIGNED, exogenous** | `cl.anomaly`/`cl.soil` are driven purely by `rng`; **nothing in the world writes back to climate**. One-way forcing. |
| Cultural mixing via flights | `mobility.py:161–174` | **DESIGNED** | Described in-code as "the sole source of genuine mixing"; every other channel is convergent. |
| Fuel-price budget shock | `mobility.py:148–151` | **DESIGNED — dead** | Gated on `fuel_price != 1.0`; `alive.py:390` never passes it. |
| Imported infections are never treated | `mobility.py:184–185` sets `diagnosed_day = -1.0`, vs `health.py:250–251` requiring `diagnosed_day == day` | **DESIGNED defect** | Imported cases bypass the treatment gate entirely and resolve on `SURVIVE_UNTREATED`. |
| The feed is a homophily machine | `feed.py:59–106`, built once at `alive.py:74` | **DESIGNED at genesis** | Edges are drawn by sorting on the **genesis** `IDENTITY − FEAR` axis (`feed.py:73`) and the graph is never rebuilt. Opinion change never re-sorts the feed. Per-tick dynamics is one dyadic encounter (`feed.py:174–178`). |
| `feed_tick_legacy` (pole-alignment, β×2.2) | `feed.py:109–150` | **ASSERTED — off the canonical path** | Explicitly `LEGACY_COMPARISON_ONLY` (`feed.py:158–160`). Its docstring reads as live physics. |
| "The fix — people do not average, they ALIGN… turns the operator from a contraction into an expansion" | `influence.py:13–34` | **ASSERTED — describes retired code** | That law is `propagate_meanfield_legacy` (`influence.py:46–99`), explicitly `LEGACY_COMPARISON_ONLY` (`influence.py:158–162`). The canonical `propagate` (`influence.py:232–248`) moves each agent `mu` toward a **partner's value** — a *contraction* toward the partner, with no pole term. The polarisation-by-alignment argument at the top of the file does not describe the operator the world runs. |
| Conviction is a ratchet | `influence.py:102–135` (legacy) vs `influence.py:251–269` (canonical) | **ASSERTED — superseded** | Canonical conviction is a log-odds update with symmetric asymptotes (0.02, 1.0), explicitly "not a ratchet" (`influence.py:257–258`). |
| Tie plasticity (agreement strengthens, disagreement weakens, rewire to force-nearest) | `plasticity.py:97–155`, recompose `plasticity.py:159` | **DESIGNED law**, resulting network structure **EMERGENT** | See §5, L5 — this is the one place opinion writes the graph. |
| Memory presses on forces | `memory.py:76–98`, called `alive.py:415` | **DESIGNED** | But nothing in `live_one_day` ever calls `chronicle.remember` — the world never generates its own memories. Cascades, wars, riots and deaths do **not** become `Memory` objects. The chronicle is an external injection port. |

---

## 5. CLOSED LOOPS — traceable A→B→A in code

| # | loop | trace |
|---|---|---|
| **L1** | FEAR → durables → wealth → deprivation → FEAR | `life.py:595` (reads `forces[FEAR]`) → `life.py:598–605` (`durable_spend`, surplus) → `life.py:607–608` (wealth) → `life.py:632–633` (cushion → deprivation) → `life.py:794–795` (`target[FEAR] += 0.25·dep`) → `alive.py:402` (relax). Lag: 1 tick on the forces→durables leg. |
| **L2** | FEAR → unrest → legitimacy/welfare → `policy_net` → income → deprivation → FEAR | `institutions.py:154–155` → `165–172, 186–189` → `institutions.py:245` → `life.py:556–563` → `life.py:630–633` → `life.py:794–795` → `alive.py:402`. **Positive** below the `legitimacy > 0.28` gate (`institutions.py:165`): falling legitimacy → welfare cut → deeper deprivation → more fear → less legitimacy. The regime switch is the loop's bifurcation point. |
| **L3** | unrest + illegitimacy → war → FEAR + firm damage → unrest | `institutions.py:194–217` → `institutions.py:279–282` (direct force write) and `251–267` (firm_health) → `life.py:459–463` (failures/layoffs) → `life.py:630–633` → `institutions.py:154–155`. |
| **L4** | **The trait-residue ring** — forces → local deviation → traits → force *baseline* → forces | `alive.py:527–528` (`dev = forces − adj_live·forces/deg`) → `alive.py:529–533` (`openness += .02·dev[CULTURE]`, `doubt += .02·dev[FEAR]`, `desire_intensity += .02·dev[DESIRE]`) → `life.py:771–781` (`drift = traits − trait_baseline`; `base[CULTURE/FEAR/DESIRE] += TRAIT_MEMORY·drift`, `TRAIT_MEMORY = 1.0` at `life.py:204`) → `alive.py:321, 402`. **Positive, self-reinforcing, unit-gain**, on 3 of 8 channels only. Bounded solely by `clip[0,1]` on traits and forces. |
| **L5** | opinion → tie weights → graph → encounters → opinion | `plasticity.py:97` (edge distance from `civ.forces`) → `106–117` (strengthen/weaken/prune) → `133–138` (rewire to force-nearest of 8) → `plasticity.py:159` `_recompose_adj` → `civ.adj` → next tick `alive.py:300` → `influence.py:186–202` (tie-**weighted** partner sampling) and `alive.py:527–528`. **Positive**: agreement raises the weight, which raises the sampling probability, which produces more agreement. |
| **L6** | fear + deprivation → crowd → riot → FEAR & mental → deprivation pressure → fear | `contagion.py:244–249` → `256–259` → `267–272` (`FEAR += 0.10`, `mental −= 0.02`) → `life.py:664, 704–709` → `life.py:809–810` (`target[FEAR] += 0.30·(1 − mental)`) → `alive.py:402`. |
| **L7** | FEAR → curiosity → DESIRE/EXPERIENCE target → forces | `flourishing.py:221–223` (`× (1 − 0.5·forces[FEAR])`) → `life.py:833–835, 841–842` → `alive.py:402`. |
| **L8** | deprivation → hunger/thirst → susceptibility gain → size of every influence move → forces → deprivation | `flourishing.py:164–174` → `susceptibility.py:69–76` → `alive.py:364` → `alive.py:372, 382–385, 399` → L1/L2. A **multiplicative gain loop**: want does not add force, it changes how far any force moves you. |
| **L9** | mental health ↔ mortality ↔ bereavement | `life.py:704–709` (`mental`) → `health.py:186–188` (CVD hazard `× (1 + 0.5·(1 − mental))`) → `health.py:284–291` (deaths) → `health.py:357–363` (bereavement over ties: `social_need +0.15`, `mental −0.08`) → `life.py:704`. |
| **L10** | knowledge ↔ culture (weak, second-order) | `knowledge.py:108–121` (learning ∝ `civ.openness`) → `kn.stock` → `flourishing.py:218–231` (curiosity, meaning) → `life.py:839–840` (`target[CULTURE]`) → `alive.py:402` → `alive.py:527–529` (`dev[CULTURE]` → `openness`) → `knowledge.py:116`. |
| **L11** | deprivation → migration → country composition → country-mean deprivation → migration | `institutions.py:333–345` (`country_dep`, `better`, destination = calmest 25) → `civ.country[idx]` rewritten → `alive.py:275–292` rehome → graph → `institutions.py:336` next tick. Also closes through the graph into L5. |

## 6. COUPLINGS THAT READ AS LOOPS IN THE PROSE BUT ARE ONE-DIRECTIONAL

| # | claimed loop | why it is not one |
|---|---|---|
| **O1** | **Cascades → forces → more cascades** (`thresholds.py:1–5`) | Detector reads `civ.forces` (`alive.py:467, 474–476`); the *only* write is `chronicle.cascade_residues.append` (`alive.py:520–523`). Residues are consumed by `effective_forces` (`alive.py:206`), which is readout-only and returns a write-locked view (`alive.py:195–200`), and by expiry (`alive.py:462–463`). Closed only under `EARTH1_TEST_CLOSED_LOOP=1` (`alive.py:346–360`). |
| **O2** | **Emotional contagion spreads affect between bodies** (`contagion.py:1–40`) | `CONTAGION_GAIN = 0.0` (`contagion.py:57`) makes both passes identity operations (`contagion.py:207–239`). |
| **O3** | **Climate ↔ society** (`weather.py:1–30`) | `cl.anomaly`, `cl.soil`, `cl.tropical` are written only from `rng` (`weather.py:114–127`). No societal quantity writes climate. Pure exogenous forcing. |
| **O4** | **The feed as an adaptive homophily machine** (`feed.py:10–32`) | `build_feed` runs once (`alive.py:74`) on the *genesis* force axis (`feed.py:73`) and is never rebuilt. Opinion change does not re-wire the feed. |
| **O5** | **Memory as living collective feedback** (`memory.py:1–29`) | `chronicle.remember` is never called from `live_one_day`. The world generates no memories of its own; the chronicle only decays and presses whatever was injected from outside (`memory.py:80–90`). |
| **O6** | **Material condition becomes force state** (`life.py:846–872`) | `couple_forces=False` at `alive.py:260`. The function does not run. |
| **O7** | **Partnership → births** (`alive.py:585–587`) | `life.partner` is inert (`partnership.py:4–5`); `_be_born` uses `life.relationship > 0.55` (`alive.py:604`). |
| **O8** | **Bereavement as a social consequence of mortality** | Two channels: one genuinely graph-mediated (`health.py:357`, `mobility.py:131`, part of L9), one an exogenous synthetic hazard unconnected to any death (`life.py:674–675`). The `"bereaved"` counter reports the synthetic one. |
| **O9** | **Crime as a social process** | `cls.criminal` / `crimes_committed` (`institutions.py:322–324`) are read by nothing except the `criminal_share` statistic. Terminal state; no back-edge. |
| **O10** | **Status / knowledge inequality as a compounding process** | `kn.status` is recomputed from scratch each tick as a weighted level (`knowledge.py:129–130`); it never accumulates and never feeds wealth. `status_gini` is a statistic of designed inputs. |
| **O11** | **Population growth** | Capped at `civ.n`; births require prior deaths (`alive.py:592, 608`). |
| **O12** | **Fuel-price shock** | Never invoked (`mobility.py:148` vs `alive.py:390`). |

---

## 7. Strongest genuinely-emergent findings in this cluster

1. **The trait-residue ring (L4) is the engine's only structural variance *amplifier*, and it runs on exactly three channels.** `alive.py:529–533` writes the agent's deviation from its living neighbourhood into `openness`/`doubt`/`desire_intensity`; `life.py:771–781` feeds that drift back into the agent's own force *baseline* at unit gain (`TRAIT_MEMORY = 1.0`, `life.py:204`), and `alive.py:402` then relaxes the agent toward that shifted baseline. An agent above its neighbours on CULTURE raises its own CULTURE attractor, which raises its deviation, which raises the attractor again. Nothing sets this; it exists only because the feedback step and the target function were written in different modules and compose. It is bounded only by `clip[0,1]`. **This is the load-bearing emergence claim available in this cluster** — and note it acts on CULTURE/FEAR/DESIRE only, so IDENTITY, COLLECTIVE, ECONOMICS, EXPERIENCE and TEMPERAMENT have no analogous amplifier. TEMPERAMENT in particular is written by nothing except encounter diffusion and is otherwise a genesis constant.

2. **Force-based network assortativity is genuinely emergent, and this is the one place the engine avoids the genesis-injection trap.** The *operative* graph is the fabric (`alive.py:64`, `fabric.py:117–214`), which is built on **demographic** homophily — household, firm, locality, country×education×age_bucket — with no force term anywhere. (Genesis' own force-homophilous graph, `genesis.py:538–544`, is discarded at `alive.py:64`.) The only writer of opinion structure into the graph is `plasticity_tick` (`plasticity.py:97–155`). So opinion-assortativity ≈ 0 by construction at day 0 and any measured value at day *N* is produced by L5. **Contrast the feed** (`feed.py:73`), whose homophily *is* injected at genesis and frozen. A paper can claim emergent echo chambers for `civ.adj`; it cannot for `w.feed`. **Measurement:** force-assortativity of `civ.adj` at day 0 vs day 120, plus the same for `w.feed` (which must be flat by construction).

3. **The legitimacy regime switch (L2) is a genuine multi-component bifurcation.** The `spend` gate (`institutions.py:165`) is designed, but which side of it a country occupies is the joint product of the force dynamics, the deprivation calculation, and the habituating norms — three modules, no fitted outcome. It is the clearest candidate for a qualitative, hysteretic emergent behaviour in the engine.

4. **Riots (L6)** require the conjunction of an opinion state (FEAR > 0.82), a material state (deprivation > 0.35), a stochastic co-presence draw, and a locality-level count crossing 38% — four components, three modules. Nothing sets a riot rate. Caveat: because `CONTAGION_GAIN = 0.0`, riots are *not* preceded by any local mood amplification; they fire directly off the target-driven force field.

5. **Cause- and age-composition of death (L9)** is emergent even though the mortality *level* and *age curve* are designed by construction (`health.py:312–317`).

## 8. The most misleading docstring claims found

1. **`thresholds.py:1–5`** — "events modify forces, which may trigger further thresholds, creating emergent cascading dynamics." In the canonical world, a threshold firing writes *nothing* into any dynamical quantity (`alive.py:520–523`); the decayed level is a read-only overlay for the readout layer (`alive.py:184–216`). The phenomenon this file is named for cannot occur. Any paper sentence containing "cascade" plus "emergent" must be rewritten: `cascades_fired` is an **instrument reading**, not a mechanism.

2. **`contagion.py:1–40`** — forty lines arguing that emotional contagion fills a structural hole, above `CONTAGION_GAIN = 0.0` (`contagion.py:57`). Both contagion passes are algebraic no-ops. Only crowds and riots survive.

3. **`influence.py:13–34`** — "people do not average, they ALIGN… turns the operator from a contraction into an expansion." That describes `propagate_meanfield_legacy`, explicitly retired (`influence.py:158–162`). The canonical `propagate` (`influence.py:232–248`) moves each agent a fixed `mu = 0.05` toward a *partner's value* with **no pole term** — a contraction. The variance-expansion argument at the top of the file does not apply to the operator the world runs, and this is precisely the kind of "mechanism creates phenomenon" claim that the wage-kurtosis error came from.

4. **`life.py:846–872`** (`couple_life_to_forces`) — a full defence of four "structural claims about people… none of them fitted to a target", for a function the canonical tick disables (`alive.py:260`, `couple_forces=False`).

5. **`alive.py:87–98`** — "Every entry point now consumes THIS dict." Two of the dict's five keys (`beta`, `layers`) are accepted by `live_one_day` and referenced nowhere in its body.

6. **`alive.py:585–588`** (`_be_born`) — "Children are CONCEIVED, not conjured to replace the dead… When births outrun deaths the population grows." Births are drawn *only* into slots freed by death (`alive.py:592, 608`) and the population is hard-capped at the genesis array size. This is exactly the mechanism the docstring says was removed, re-expressed as a capacity constraint.

7. **`alive.py:6–21`** — the ordered stage list at the top of the tick does not match the body (governments run before aging; contagion, mobility and the feed are unlisted; the "9 CASCADE / 10 FEEDBACK" pair is inverted in effect since cascade writes nothing).

8. **`generational.py:133–136`** — "Ages every slot, dead ones included." True in isolation, undone by `alive.py:542–543`.

## 9. Cross-cutting caveats a paper must state

- **Seed-independent influence randomness.** `influence.py:242` and `feed.py:173` seed private generators from the *day index alone*. Every world, at every seed, draws the identical encounter uniforms on day *d*. An ensemble over seeds does not sample the influence channel's randomness at all — it samples only graph structure. Any Monte-Carlo error bar on an opinion observable is understated in an unquantified way. Additionally, `ENCOUNTER_SEED_TIE − ENCOUNTER_SEED_FEED = −10000`, so the two streams alias for runs longer than 10 000 days.
- **The living-view is one stage stale.** `adj_live` (`alive.py:300`) predates the weather, want and road killers (`alive.py:307, 313, 390`); those decedents still influence and are influenced in the same tick.
- **Within-tick lags.** `life.deprivation` is fixed at `life.py:633` before weather's heating bill (`weather.py:166`), storm losses (`weather.py:190`) and wealth compounding (`institutions.py:330`) modify wealth — so deprivation always trails those channels by one day.
- **Two orchestrators exist.** `earth1/tick.py:103` (`world_tick`) is a second, structurally different loop — it *does* call `thresholds.detect_and_append` (`tick.py:225`), `feedback.opinion_feedback` (`tick.py:203`) and `graph_dynamics.update_graph` (`tick.py:244`), i.e. it closes the cascade loop the canonical world severs. It is still imported and used by `g5.py:36`, `living.py:33` and `advance.py:19`. `earth1/__init__.py:3–4` and `chaos.py:3` declare `alive.live_one_day` the only Earth. Any published number must state which loop produced it.
