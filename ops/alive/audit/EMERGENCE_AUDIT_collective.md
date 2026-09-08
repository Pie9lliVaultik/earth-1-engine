# CLUSTER 4 — COLLECTIVE DYNAMICS: DESIGNED vs EMERGENT vs ASSERTED

**Scope:** `earth1/thresholds.py`, `contagion.py`, `event_log.py`, `mobility.py`, `partnership.py`, plus the code that actually executes them (`alive.py`, which re-implements the cascade detector inline).

**Measurements I ran** (read-only, scripts in scratchpad, canonical `birth_world`/`live_one_day`, world seed 42 / rng seed 7). Cited below as M1/M2/M3:
- **M1** pop 4,000 × 30 days
- **M2** pop 6,000 × 60 days, canonical **and** a `shared_attention` ablation twin
- **M3** pop 6,000 × 120 days

**Scaling caveat, stated up front:** at pop 6,000 there are ~800 localities holding ~30 living agents each; at production pop 200,000 the repo's own census (`ops/alive/H_CASCADE_1.md:14-20`) records 869 eligible localities at ~230 agents each. Participation-fraction sampling noise is ~4× larger in my runs, so my *hot-locality counts* are inflated relative to production. Every finding below that depends on a **count** is flagged; findings that depend on **reachability** (a gate no agent can pass), **wiring** (open loop, dead constants) or **direction of drift** are population-independent.

---

## 1. THE SINGLE MOST IMPORTANT STRUCTURAL FACT

`thresholds.py` is **not the live cascade detector**. `alive.py` imports only the `TRANSITION_RULES` list (`alive.py:419`) and re-implements detection inline at `alive.py:470-523` with **different locality, different critical fraction, different firing semantics, and no feedback**. `detect_transitions`, `detect_and_append`, `_participation`, `_check_condition` and `MIN_PARTICIPATION` are reachable only from `tick.py:225` — the legacy question-answering stack. The live `World` dataclass (`alive.py:33-48`) has **no `event_log` field at all**, so `event_log.py` is entirely absent from the living civilization (`earth1/__init__.py:4`: "`earth1.alive.live_one_day`. That is the only Earth.").

| | `thresholds.py` (documented) | `alive.py` (executed) |
|---|---|---|
| locality | country (`thresholds.py:152-153`) | `country×1000 + region×2 + urban` (`alive.py:420-422`) |
| critical fraction | `MIN_PARTICIPATION = 0.25` (`:98`) | `critical_fraction = 0.12` (`alive.py:99`) |
| effect of firing | appends a `WorldEvent` that overlays forces (`:172-179`) | appends a decaying **residue** consumed only by the readout (`alive.py:512-523, 184-216`) |
| re-arming | cooldown only (`:158`) | cooldown **+** episode-entry for 2 of 5 rules (`alive.py:113, 480-508`) |
| dead agents | not masked | masked (`alive.py:473`) |

---

## 2. `earth1/thresholds.py`

| behaviour | mechanism (file:line) | verdict | note / measurement needed |
|---|---|---|---|
| The five transition rules (names, force conditions, thresholds, effect magnitudes, cooldowns, half-lives) | `thresholds.py:29-70` | **DESIGNED** | Every number is a literal. No fit, no provenance file cited for any of the 10 thresholds or 8 effect deltas. |
| "events modify forces, which may trigger further thresholds, creating emergent cascading dynamics" | `thresholds.py:3-5` | **ASSERTED — and false in the canonical engine** | The live path is explicitly **open-loop**: `alive.py:443-445` "nothing here writes stored forces"; the residue is a read-time overlay (`alive.py:184-191`) consumed only by `answer_living.py:50`, `history.py:148`, `api/readouts.py:103`. A firing therefore **cannot** cause a second firing. The only closed-loop path is `EARTH1_TEST_CLOSED_LOOP=1`, a deliberately broken test twin (`alive.py:346-360`). Cascades do not cascade. |
| Firing is per-agent AND-of-conditions over a locality, not a mean test | `thresholds.py:101-118`; live equivalent `alive.py:473-478` | **DESIGNED** | Correct as described. This is a genuine improvement over the mean test, and the mean test is retained under `mode="national"` (`:165-169`). |
| "MIN_PARTICIPATION is an external anchor, not a tuned value" (Centola 2018 / Granovetter) | `thresholds.py:92-98` | **ASSERTED — contradicted by the repo's own artifacts** | (a) The live engine does not use it; it uses 0.12 (`alive.py:99`). (b) `scripts/sbi/theta.py:14` lists `critical_fraction` as one of six **calibratable** parameters with prior `[0.06, 0.24]`. (c) The pre-registered sweep the docstring points to recorded **`"verdict": "FAIL: knife-edge on the free parameter"`** (`data/fix1_local_thresholds.json`), and the docstring omits this. |
| Firing count is a steep function of the free parameter | `data/fix1_local_thresholds.json` sweep, pop 200k, country scope | **DESIGNED (measured)** | fired = 104 / 27 / 14 / 4 / 0 / 0 at min_participation 0.10 / 0.15 / 0.20 / 0.25 / 0.30 / 0.40. A 26× swing across the "10–25% literature band" and extinction at 0.30. The engine's 0.12 sits at the steep end. |
| `decay_half_life` field on `TransitionRule` | `thresholds.py:26` | **DESIGNED**, and **unconsumed in `thresholds.py`** | Passed to `WorldEvent.create` at `:176` (legacy stack only). In the live stack it is consumed at `alive.py:523` as the residue half-life. `alive.py:437-439` records it as an unresolved contradiction — that comment is now stale for the live path. |
| Global-scope rules | `thresholds.py:181-205` | **DEAD CODE in the live path** | `alive.py:471-472` `continue`s on any rule whose `region_scope != "regional"`. All five shipped rules are regional, so no behavioural difference today — but a global rule added to `TRANSITION_RULES` would be silently ignored by the live engine. |
| `polarization_lock` (IDENTITY>0.8 & CULTURE>0.7) and `economic_boom` (ECONOMICS>0.8 & FEAR<0.3) fire | `thresholds.py:46-61` | **DESIGNED-UNREACHABLE (measured)** | M2/M3: 0 hot localities at genesis **and** at day 60 and day 120, even at a relaxed 0.05 bar. `data/threshold_reachability.json` independently records `panic_cascade` and `identity_collapse` as unreachable in *national* mode at genesis. Two of the five rules are inert. |

---

## 3. `earth1/contagion.py`

| behaviour | mechanism (file:line) | verdict | note / measurement needed |
|---|---|---|---|
| **Emotional contagion (both passes)** — the module's entire stated reason to exist | `contagion.py:51` `CONTAGION_GAIN = 0.0`; consumed at `:211` and `:232` | **DESIGNED-OFF — the mechanism is an exact no-op** | Every gain is `0.0 × …`. M1/M3 confirm: `contagion_moved = 0.0` on **every one of 150 measured days**. The 39-line docstring (`:1-39`) describing chemosignal / mimicry / prosody / synchrony describes a channel that transmits nothing. The comment at `:48-50` ("this gain … dwarfs the opinion-propagation rate") describes the *legacy* value 0.30 and is now inverted. |
| `Presence.density` — "cities are dense, and that is most of what being urban means physically" | `contagion.py:159-170` | **DESIGNED, then INERT** | Density is the only genuinely computed quantity here (place occupancy normalised at p95, ×1.6 urban / ×0.5 rural). Its **sole** consumer in the engine is `contagion.py:211`, i.e. multiplied by zero. Verified by grep: other hits are `rebirth.py:472` / `rehome.py:195` (copy on slot reuse) and `api/readouts.py:226` (display). There is **no density term anywhere in the disease model** (see §5). |
| Gathering assignment (who is at work/transit/market/worship/stadium today) | `contagion.py:62-69, 193-202`, `OUT_AMONG_PEOPLE = 0.72` (`:93`) | **DESIGNED** | Shares renormalised to partition exactly 72% of the population. The only surviving effect of this computation is that it gates `pres.gathering >= 0` in the crowd test. |
| **Crowds and riots** | `contagion.py:241-272`; `CROWD_AROUSAL=0.82`, `CROWD_GRIEVANCE=0.35`, `CROWD_FRACTION=0.38`, `RIOT_ESCALATION=0.02` (`:84-87`) | **DESIGNED-UNREACHABLE — zero crowds, zero riots (measured)** | M1 (30 d) and M3 (120 d): `crowds_today = 0` and `riots_today = 0` on every day. Cause: `CROWD_AROUSAL = 0.82` sits **above the 99th percentile of FEAR**. M2 measured FEAR p99 = 0.7917 and, in the `shared_attention`-ablated twin, **max FEAR across all 6,000 agents = 0.7935** — i.e. with the national-sport injector removed, *no agent in the world can ever satisfy the arousal gate*. Requiring 38% of a locality on top of that is structurally impossible. |
| "mean fear sits near 0.85 — so almost every locality cleared the bar almost every day" (the stated reason 0.82 was chosen) | `contagion.py:71-83` | **ASSERTED — false of the current world** | Measured mean FEAR: 0.535 at genesis, 0.590 (d30), 0.632 (d60), 0.650 (d120). The threshold was calibrated against a fear distribution the engine no longer produces, and was never re-checked. |
| "AND THAT IS THE STRUCTURAL HOLE THIS FILLS… a model with only the first cannot produce crowd behaviour at all" | `contagion.py:33-38` | **ASSERTED — false** | The hole is not filled. The model still produces no crowd behaviour: 0 crowds in 120 measured days. |
| Riot escalation as a stochastic tail of crowds | `contagion.py:262-263` | **DESIGNED** | A flat Bernoulli `p = 0.02·dt` per crowd-locality-day. Given `n_crowd`, riots are a designed rate, not an emergent outcome. Moot at `n_crowd = 0`. |
| **`shared_attention`** — national mood shocks | `contagion.py:109-146`; `NATIONAL_EVENT_RATE_YR=14`, `ATTENTION_REACH=0.55`, `WIN_IDENTITY=0.05`, `LOSS_FEAR=0.035`, win probability hard-coded 0.5 (`:127`) | **DESIGNED — and a materially large writer** | Expected 194 × 14/365 = 7.44 events/day; M1/M3 measured 7.87–7.90/day. Each writes IDENTITY +0.05·g and COLLECTIVE +0.04 to 55% of a country on a coin flip. **Ablation (M2): removing it cuts total cascade firings 192 → 148 (−23%) and `collective_surge` hot localities 99 → 77 over 60 days.** It is also the *only* mechanism that pushes any agent's FEAR above ~0.79. A designed exogenous injector is supplying roughly a quarter of the "cascade" activity. |
| Crowd-fraction denominator counts dead rows | `contagion.py:184` (`np.bincount(pres.locality)` over all rows) vs. numerator masked live at `:244` | **DESIGNED (latent defect)** | Dilutes the fraction by the dead-slot share. Currently harmless (rebirth recycles slots fast; and the gate is unreachable anyway), but it would bias the crowd rate if `CROWD_AROUSAL` were ever recalibrated. Same issue in pass 1's `local_mean` (`:209-210`), which averages in deceased agents' frozen forces. |

---

## 4. `earth1/event_log.py`

| behaviour | mechanism (file:line) | verdict | note / measurement needed |
|---|---|---|---|
| Exponential residue decay `2^(-Δt/h)` | `event_log.py:91-97` | **DESIGNED** | Closed-form law. `h <= 0` ⇒ factor 1.0 (permanent), not zero. |
| Active-set pruning at 0.01 on both factor and `max|delta|·factor` | `event_log.py:115-124` | **DESIGNED** | |
| Read-time overlay: sum active events per matching agent, clip total to ±0.5 | `event_log.py:167-221`, clip at `:220` | **DESIGNED** | The ±0.5 cap is the only nonlinearity and is a bare literal with no stated provenance. |
| The whole module is live | — | **NOT IN THE LIVE ENGINE** | `World` (`alive.py:33-48`) has no `event_log`. Consumers are `tick.py:156`, `engine.py:107,169`, `g5.py:184,549`, `legacy_benchmark.py:114` — the legacy question stack only. |
| The same semantics, re-implemented for the live path | `alive.py:163-181` (`cascade_residue_levels`) + `alive.py:184-216` (`effective_forces`) | **DESIGNED (duplicated)** | Byte-for-byte the same law: `2^(-Δt/h)`, `h<=0 ⇒ 1.0`, 0.01 pruning, ±0.5 clip, then clip to [0,1]. Two copies of one physics; a change to one silently diverges from the other. |
| Overlay is strictly derived, never fed back | `alive.py:189-191`, `:194-201` (returns a write-protected view) | **DESIGNED** | This is the clean, defensible part of the design and it is honestly documented. It is also what falsifies the `thresholds.py` cascade claim. |
| "integer enum keys silently produced ZERO event vectors — G5 runs #3-#6 event legs injected no-op shocks" | `event_log.py:60-64` | **ASSERTED** | A historical measurement about past runs. The *code property* is verifiable and true today: `_canonical_deltas` (`:58-79`) normalises `Force`/int/digit-string/name and raises on anything else. The claim about G5 #3-#6 is unverifiable from code — settle it by re-running those legs and diffing the injected force vectors against zero. |
| `_matches_region` / `_matches_demographics` | `event_log.py:138-165` | **DEAD CODE** | Never called anywhere in `earth1/` or `tests/`. `effective_deltas_vectorized` re-implements region matching inline (`:183-196`) with different logic (the `f"{iso2}-X"` probe at `:194`). Two matchers, one unused, no test pinning them equivalent. |

---

## 5. `earth1/mobility.py`

| behaviour | mechanism (file:line) | verdict | note / measurement needed |
|---|---|---|---|
| Flights per capita, car ownership, road-death rates, commute minutes by income tier | `mobility.py:53-65` | **DESIGNED (externally anchored)** | WHO-style tier tables; the gradients are asserted-from-literature but the values are directly imposed. |
| Car ownership follows money as well as country | `mobility.py:95-96` | **DESIGNED** | `own_p × (0.5 + 0.5·wage/median)`, capped 0.97. A parameterised interaction, not an emergent stratification. |
| Road-death age profile peaking at 24 | `mobility.py:118-124` | **DESIGNED** | `1 + 1.8·exp(-((age−24)/12)²)` is a hand-written Gaussian bump multiplied into a tier base rate. The "leading killer of the young" pattern is imposed, not produced. |
| Bereavement spillover from a road death onto graph neighbours | `mobility.py:131-136` | **EMERGENT (weakly)** | Interaction of {`civ.adj` fabric topology} × {who dies}. *Who* is bereaved and *how many* is not set anywhere — it is the degree distribution of the fabric composed with a hazard draw. The per-event magnitudes (+0.12 social need, −0.06 mental) are designed. Measured incidence is tiny: M3 recorded 2 road deaths in 120 days at pop 6,000. |
| **"the countries hit first are the most CONNECTED ones rather than the nearest ones"** | `mobility.py:176-187`; host draw at `:167-168` | **ASSERTED — and contradicted by the code** | The traveller's host is `living[rng.integers(0, living.size, …)]` — a **uniform draw over every living agent on Earth, including agents in the traveller's own country**. There is no destination country, no route network, no distance, no connectivity structure whatsoever. It is a mean-field draw. The only country-varying quantity is *flight volume* (wealth-graded), so the claim reduces to "rich countries import more", which is true but is not the connectivity claim made. |
| Disease import produces pandemics | `mobility.py:180-187`, per-contact probability 0.10 (`:181`) | **DESIGNED-INERT (measured)** | M1 and M3: **0 imports** across 2,666 simulated flights in 120 days. Prevalence of `condition == 3` measured at 0.0007 (M2, day 60), so expected imports ≈ 22 flights/day × 7e-4 × 0.10 ≈ 0.0015/day. |
| An import can *become* an outbreak | `health.py:189-191` | **NO SUCH MECHANISM** | The infection hazard is `INFECT_BASE[tier] × (1+1.2·HARDSHIP_GAIN·dep) × (1+0.8·(age>65))` — a per-agent independent Poisson draw with **no contact term, no neighbour term, no locality term and no density term**. `civ.adj` appears in `health.py` only at `:358`, for bereavement. There is no person-to-person disease transmission in Earth-1 except the mean-field flight draw, and no onward local spread from it. The module docstring's COVID framing (`mobility.py:11-17`) describes epidemiology the engine does not implement. |
| **Cultural mixing — "the sole source of genuine mixing… every other channel is homophilous and therefore convergent"** | `mobility.py:163-172`, `CULTURAL_MIXING = 0.020` (`:67`) | **DESIGNED mechanism; the *claim of uniqueness* is the interesting, checkable part** | The move is a designed 2% pull toward a randomly-sampled agent's CULTURE. The *anti-convergence* consequence — that the CULTURE channel's cross-country variance stops collapsing — would be genuinely emergent (interaction of {flight rate ∝ wealth} × {global mixing} × {homophilous fabric}). **Measurement needed:** run canonical vs. `CULTURAL_MIXING = 0` and compare between-country CULTURE variance and its trend over ≥2 years. I did not run this ablation. Note the mechanism is wealth-biased by construction (`:97-98`), so it mixes HIC agents ~80× more than LIC agents. |
| Commute as "a direct tax on the ties everything else needs" | `mobility.py:138-145` | **DESIGNED — magnitude computable in closed form** | A constant drag of `0.0008 × hours/day` on `life.relationship`, against a restoring pull of rate 0.02/day toward `relationship_setpoint` (`life.py:695-698`). Steady-state displacement = drag/relax = `0.04·hours` — about **−0.05 for a typical 1.3 h urban commute**. Not emergent; it is an analytically predictable offset. |
| Commute writes are not masked on `alive` | `mobility.py:138-145` | **DESIGNED (latent defect)** | `life.relationship` is repaired by `DECEASED_FROZEN` (`alive.py:126-131`), but **`fl.belonging` is not in that list**, so deceased rows accumulate belonging decay from a commute they are not making. Small, but it contaminates any flourishing statistic taken over all rows. |
| Fuel-price pass-through to household cost | `mobility.py:147-151`, `FUEL_SHARE_OF_BUDGET = 0.08` | **DESIGNED** | Inert at `fuel_price = 1.0` (the default in `alive.py:390`), i.e. off unless a scenario drives it. |

---

## 6. `earth1/partnership.py`

| behaviour | mechanism (file:line) | verdict | note / measurement needed |
|---|---|---|---|
| Who is partnered at t=0 | `partnership.py:18-40` — two oldest adults per household, both past `ADULT=0.02`, age gap ≤ `MAX_AGE_GAP=0.25`, with a flat 15% skip (`:37`) | **DESIGNED, drawn at genesis** | Deterministic under the world seed. The 15% "some households are not couples" is a bare literal. |
| Partnership formation over time | — | **DESIGNED-ABSENT, and honestly documented** | `partnership.py:7-8` states it plainly. Verified by grep: the only writers of `life.partner` are `pair_at_genesis`, `persistence.py:187-197` (backfill), `rebirth.py:359` (newborn ⇒ −1), and `dissolve_on_death`. This is the one docstring in the cluster that **understates** rather than overstates. |
| Dissolution by death (widowing) | `partnership.py:43-55`, invoked `alive.py:546-547` | **DESIGNED** | Deterministic consequence of a mortality draw. M3 measured 14 widowings in 120 days at pop 6,000. |
| "STATE ONLY: no dynamics read it" | `partnership.py:4` | **VERIFIED TRUE — with a naming trap** | Grep confirms no dynamic consumer; readers are `history.py:86` and `api/readouts.py:84,259`. **But** `life.py:677-679` comments "a child arrives: **partnered**, of age, and not destitute" while gating on `life.relationship > 0.6` — a *continuous scalar*, not the partner edge. Two unrelated notions of "partnership" coexist; the first-class edge does not gate fertility, and a paper must not conflate them. |

---

## 7. THE CENTRAL QUESTION: ARE CASCADES A THRESHOLD PHENOMENON OVER A DISTRIBUTION, OR EFFECTIVELY DETERMINISTIC?

Neither, and the honest answer is worse than either. The firing decision genuinely is a threshold on a distributed statistic — the per-locality participation fraction is a real, varying quantity (M3 day 0, `collective_surge`: min 0.000 / median 0.048 / max 0.462 across 197 eligible localities). But four measured properties disqualify it as an emergent cascade:

**(a) It is not a cascade — second-order triggering is architecturally impossible.** A firing writes a residue (`alive.py:512-523`) that is read only by `effective_forces` (`alive.py:184-216`), which is consumed exclusively by the readout layer. The detector reads `civ.forces` directly (`alive.py:467`). Nothing a cascade does can be seen by the detector. The repo states this correctly at `alive.py:443-445` — and `thresholds.py:3-5` states the opposite.

**(b) The distribution drifts monotonically past a fixed bar; the world does not self-organise, it slides.** M3, pop 6,000, genesis → day 120: `collective_surge` global share 0.077 → **0.390**, hot localities 55/197 → **119/192**; `identity_collapse` 0.040 → **0.247**, hot 18 → 94. By day 120 the *majority* of localities sit permanently above the bar, with locality fractions reaching 1.000. This is exactly the repo's own diagnosis — `ops/alive/H_CASCADE_1.md:22-30`: "persistent level conditions are converted into repeated discrete events by cooldown-only re-arming… **Migration/network spread ruled out (99.9% direct)**". The engine's own instrument says these are not spreading phenomena.

**(c) The bar sits inside the noise band of the statistic it thresholds.** `data/h_cascade_1/episode_structure.json` records median cold-gap-before-re-entry of **2–3 days**, with **54–64% of re-entries occurring within ≤3 days** and median closed-episode length 2 days. Localities are flickering across the threshold, not transitioning. A phase transition does not re-enter its own episode every other day.

**(d) The event count is set by accounting, not by physics.** Same file: for `collective_surge`, `fires_A = 11,456` → `fires_H1 = 772` (15×) and for `identity_collapse` `5,553` → `1,666` — from the episode-entry bookkeeping change alone, with **`hot_sets_identical_A_vs_H1_all_days: true`**. Identical world, identical hot set, 15× fewer "events". And the count is equally hostage to the free parameter: the repo's own pre-registered sweep gives 104 / 27 / 14 / 4 / 0 firings at 0.10 / 0.15 / 0.20 / 0.25 / 0.30.

**Verdict for the paper:** the cascade layer is a **thresholded readout of a drifting designed distribution**, with the event count jointly determined by a free critical fraction, a cooldown, and an episode-entry convention. It should not be described as an emergent cascade, a phase transition, or a contagion process.

---

## 8. THE STRONGEST GENUINELY-EMERGENT FINDINGS IN THIS CLUSTER

Honestly: this cluster is thin on emergence, and I would rather say so than manufacture it.

1. **The locality partition itself, and its consequence for who can ever be hot.** The cascade locality key `country×1000 + region×2 + urban` (`alive.py:420-422`) is not enumerated anywhere — the occupied set (879 of 886 theoretical cells at pop 200k, `ops/alive/H_CASCADE_1.md:14-18`) arises from the joint genesis distribution of country × region × urbanisation. Which localities clear `pop ≥ 10` and are therefore cascade-eligible at all is an emergent property of that partition, and it is the gate on the entire cascade layer. It is also where the population-size confound lives: at ~30 agents/locality (my runs) the participation fraction's sampling s.d. is ~0.05 against a 0.12 bar; at ~230 (production) it is ~0.017. **Measurement needed:** the hot-locality count as a function of population at fixed physics — if it moves, the "cascade rate" is partly a discretisation artefact.

2. **The persistence structure of the hot set.** M2, genesis vs. day 60, eligible localities: `collective_surge` Jaccard(hot@0.12) = **0.47**, corr(genesis fraction, day-60 fraction) = **+0.66**; `identity_collapse` Jaccard 0.25, corr +0.47; `panic_cascade` Jaccard 0.04, corr +0.23. So *which* localities are hot is roughly half inherited from the genesis force draw and half produced by living — and the split differs sharply by rule. This is a real, quantifiable, publishable decomposition, and it is the direct analogue of the fat-tail test that caught the earlier error. **It is the measurement I would put in the paper.** Note the level does move a great deal (hot@0.25 for `collective_surge`: 19 → 74 over 60 days), so unlike the wage kurtosis this is *not* simply "present at genesis" — it is genuinely mixed, and the mixture should be reported as a mixture.

3. **Bereavement reach from road deaths** (`mobility.py:131-136`) — the set of people touched by a death is the fabric's degree distribution composed with a mortality draw, and is set nowhere. Genuinely emergent, but measured incidence is negligible at the scales I ran (2 deaths / 120 days / 6,000 agents).

4. **A candidate I could not test and flag as open:** whether flight-borne cultural mixing (`mobility.py:163-172`) actually arrests the homophilous convergence of the CULTURE channel. If it does, that is a real emergent equilibrium between a convergent kernel and a wealth-biased mixing term. Needs the `CULTURAL_MIXING = 0` ablation over ≥2 simulated years.

---

## 9. THE MOST MISLEADING DOCSTRING CLAIMS FOUND

1. **`thresholds.py:3-5` — "events modify forces, which may trigger further thresholds, creating emergent cascading dynamics."** The canonical engine is open-loop by explicit design (`alive.py:443-445`); the only closed-loop version is a deliberately broken test twin. This is the exact shape of the fat-tails error — a mechanism narrative that the current code contradicts — and it is the sentence most likely to be lifted into a paper.

2. **`thresholds.py:92-98` — "MIN_PARTICIPATION is an external anchor, not a tuned value… Registered before the run… and swept."** The sweep it cites recorded **`"verdict": "FAIL: knife-edge on the free parameter"`** (`data/fix1_local_thresholds.json`), the constant is listed as a calibratable parameter with a prior in `scripts/sbi/theta.py:14`, and the live engine runs a *different* value (0.12) at a *finer* locality scope — both changes in the direction of more firing. The docstring cites the pre-registration and omits its verdict.

3. **`contagion.py:1-39` — the module's entire premise.** "Energy does pass between co-present people"; "a model with only the first cannot produce crowds"; "THAT IS THE STRUCTURAL HOLE THIS FILLS." `CONTAGION_GAIN = 0.0` (`:51`) makes both transmission passes exact no-ops (measured: `contagion_moved = 0.0` on 150/150 days), and the crowd gate is unreachable (measured: 0 crowds and 0 riots in 120 days; `CROWD_AROUSAL = 0.82` exceeds the FEAR p99 of 0.79, and exceeds the *global maximum* of 0.7935 once the national-sport injector is removed). The module transmits nothing and produces no crowds. Nothing in the 39-line docstring signals this; the disabling is disclosed only in a terse inline comment.

4. **`contagion.py:71-83` — "mean fear sits near 0.85 — so almost every locality cleared the bar almost every day."** Measured mean FEAR is 0.53–0.65. The calibration story explains a threshold chosen for a world the engine no longer runs, and reads as if the current threshold is well-placed when it is in fact unreachable.

5. **`mobility.py:15-17 / 176-179` — "the countries hit first are the ones with the most connections, not the nearest ones."** The host is a uniform draw over all living agents worldwide including the traveller's own countrymen (`:167-168`). There is no connection graph, no destination, no distance. And there is no onward transmission anywhere in the engine to turn an import into an outbreak — `health.py:189-191` has no contact or density term at all. Measured imports: 0 in 2,666 flights.

6. **`alive.py:14` — the module header's "9 CASCADE local thresholds fire — thresholds.py."** The cascade is implemented at `alive.py:470-523`, not in `thresholds.py`, with a different critical fraction, a different locality, and different semantics. A reader following the header to `thresholds.py` will document a detector that never runs.

---

### Files read (absolute paths)
`/Users/pietronovelli/Documents/GitHub/earth-1-engine/earth1/thresholds.py`, `contagion.py`, `event_log.py`, `mobility.py`, `partnership.py`, `alive.py`, `tick.py`, `chaos.py`, `health.py`, `life.py`, `institutions.py`, `rehome.py`, `types.py`, `genesis.py`, `eventwire.py`, `persistence.py`; `scripts/fix1_local_thresholds_test.py`, `scripts/sbi/theta.py`; `data/fix1_local_thresholds.json`, `data/fix1_local_thresholds_prereg.json`, `data/threshold_reachability.json`, `data/threshold_envelope.json`, `data/h_cascade_1/episode_structure.json`, `data/h_cascade_1/stageC_compare.json`; `ops/alive/H_CASCADE_1.md`. Measurement scripts (scratchpad, not in the repo): `/private/tmp/claude-501/-Users-pietronovelli-Documents-GitHub-vaultik-x/e30708db-e208-4f7c-aad1-c0be9c88f760/scratchpad/measure_cascade.py` and `measure2.py`. **No repository file was modified.**