# CLUSTER 3 AUDIT — SOCIAL STRUCTURE AND PROPAGATION

Repo: `/Users/pietronovelli/Documents/GitHub/earth-1-engine`. Canonical daily path is `earth1/alive.py::live_one_day` (line 219). Everything below was traced from that entry point; modules or functions not reachable from it are marked OFF-PATH.

**Headline for the paper (decisive question):** agent-to-agent influence *does* genuinely move state. Two operators on the canonical path read a *named partner's current value* and move the reader toward it: `influence.propagate` (`earth1/influence.py:246` → `dyadic_move` at `earth1/influence.py:205-217`, `delta = f[partner] - f`) and `feed.feed_tick` (`earth1/feed.py:177`). This is real transmission, not a shared response to a common input. **But** three confounds on the same path produce neighbour-correlated opinion *without* any transmission, and none of them is currently separated in the code: (a) a genesis-anchored per-agent restoring target on a homophilous graph, (b) memory press, which is literally a common input, (c) the tie-weighted encounter sampler drawing overwhelmingly from same-country/same-locality/same-cohort partners. The ablation that settles it is named in the prose section.

---

## `earth1/fabric.py` — the social graph

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Graph exists at all; 7 tie channels with fixed weights and fixed k | `fabric.py:44-57` (`TIE_SPEC`), `fabric.py:117-216` | **DESIGNED** | Every weight (1.00/0.60/0.40/0.70/0.15/0.55/0.30) and every k is a hand-set constant. |
| Graph is drawn ONCE, at genesis | `alive.py:63` (`build_fabric` called only in `birth_world`) | **DESIGNED** | No other call site anywhere (`grep build_fabric`). |
| Graph changes over time | `plasticity.py:71-160` (friends+weak only), `rehome.py:245-276` (colleagues), `rehome.py:239` / `rebirth.py` (household on rebirth) | **DESIGNED (mechanism) / EMERGENT (trajectory)** | `neighbours`, `diaspora`, `media` are **static for the world's entire life** — no code path edits them. The evolving graph is a strict subset of channels. |
| Household size varies by country fertility | `fabric.py:76-88` (`1.2 + 0.9*tfr`), `fabric.py:134-148` | **DESIGNED** | Linear fit on TFR, hand-set coefficients. |
| "A job loss lands on five people in Lagos and two in Stockholm" (household channel *dominates* in high-TFR countries) | docstring `fabric.py:13-18`, `fabric.py:83`; actual code `fabric.py:149` (k=3 fixed) + `fabric.py:210` (`m.maximum(m.T)`) | **ASSERTED — and contradicted by measurement** | I measured `_pairs_within` directly: hh=2 → weighted degree **3.000**, 1.00 distinct neighbour at weight **3.0**; hh=6 → weighted degree **4.749**, 3.69 distinct neighbours at weight ~1.0. Ties per agent is hard-coded 3 regardless of house size; duplicates stack and are then capped by `maximum`. So a small household concentrates *all* household weight on one person; total household encounter probability barely varies. `TIE_SPEC["household"] = (1.00, None)` — the `None` "size set by country fertility" is never read. Measurement to report: household-channel weighted degree and distinct-neighbour count vs country TFR. |
| Weak ties are Granovetter bridges that let cascades jump clusters | docstring `fabric.py:25-28`; code `fabric.py:171-178` | **DESIGNED, with an unintended size artefact** | Partners are drawn uniformly over the *whole population* and then filtered `keep = same_country \| (rand<0.02)`. Expected weak degree ≈ `2·k·p_country`. An agent in a country holding 17% of world pop keeps ~2 weak ties; an agent in a 0.1%-share country keeps ~0.04. **Cascade-jumping capacity is proportional to own-country population share by construction.** Measurement: weak-tie degree vs country population share. |
| "Media hubs — celebrities, scientists, heads of state" | docstring `fabric.py:59-62`; code `fabric.py:198-203` | **ASSERTED / false as stated** | `hubs = rng.choice(n, n_hub, replace=False)` — a **uniform random draw over the population**, uncorrelated with knowledge, status, degree or occupation. Audience is uniform random too. It is a random star, not a celebrity. |
| Media ties are "what make it one world"; "phi-proxy measured 0.0028" | docstring `fabric.py:51-56` | **ASSERTED** (historical measurement claim) | Media contributes only ≈0.024 edges/agent (`n·HUB_SHARE·3·40`) at weight 0.30. Measurement needed: connected-component count of `fabric.adj`, and cross-border share of total edge weight, with and without `diaspora`+`media`. |
| Heterogeneous tie weights at genesis | `fabric.py:208-210` (COO duplicates summed by `csr_matrix`, then `maximum(m.T)`) | **DESIGNED (side effect)** | Weight heterogeneity comes from repeated ring-offset draws colliding, not from any behavioural process. `plasticity.py:104` acknowledges "genesis stacks duplicates up to ~3.5". |
| Diaspora corridors "follow cultural and regional proximity" | docstring `fabric.py:181-183`; code `fabric.py:186-195` | **DESIGNED, weaker than described** | Partner is `rng.integers(0, n)` filtered by `cross-country & same-region & is_migrant`. No corridor structure beyond the region indicator; migrant share is a flat 0.14 everywhere. |

## `earth1/graph_kernels.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Fused k-way CSR merge / fused edge distance | `graph_kernels.py:116-143`, `146-176` | **DESIGNED** (pure optimisation) | No semantics. |
| Both kernels are OFF by default | `graph_kernels.py:37` (`ENABLED = os.environ["EARTH1_FUSED_KERNELS"]=="1"`), guards at `:121`, `:168` | **DESIGNED** | Production Earth runs the scipy/numpy paths. Note the genesis assembly (`fabric.py:205-216`) never calls the merge at all — only `rehome._recompose_adj` (`rehome.py:296`) does, so genesis and re-composition are different code paths that must agree. |
| "bit-exact… proven by trajectory hash"; the 107 s/day vs 79 s/day concurrency numbers | docstring `graph_kernels.py:1-2, 22-29`, `152-153` | **ASSERTED** | Historical benchmark claims. Settle by re-running the A/B world-hash comparison at the stated width; do not repeat the numbers in the paper as code properties. |

## `earth1/memory.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Salience decays on a half-life | `memory.py:37` (720 d), `memory.py:80` | **DESIGNED** | |
| A memory presses on the forces of everyone in scope | `memory.py:84-90`, `PRESS=0.02` at `:40` | **DESIGNED — and it is a COMMON INPUT, not diffusion** | Every agent in `scope` receives the **identical** `force_signature` vector. Two agents in scope converge because they are given the same push, not because they interacted. This is exactly the mechanism that would masquerade as social diffusion in an observable. |
| Memory press is monotone-upward | `event_from_news` builds a non-negative signature (`memory.py:196-199`); update is additive (`memory.py:87-89`) | **DESIGNED** | News memories can only *raise* FEAR/COLLECTIVE/EXPERIENCE. There is no de-pressing path. |
| Memories spread along the social fabric | `memory.py:103-143` (`spread`), catch at `:139`, rate 0.06 | **EMERGENT (weakly)** — interaction of Chronicle scope × `civ.adj` degree-normalised exposure | Genuine network process: `exposure = (adj @ scope)/deg`, `P(catch) = 0.06·exposure`. Uses the **stored** graph (dead included), by design (`alive.py:298-299`). Scope is monotone (`m.scope = m.scope \| catch`, `memory.py:186`) — it never contracts. |
| Rehearsal: similar events refresh old ones | `memory.py:65-72` (cosine > 0.80 → `+0.35`) | **DESIGNED, with a degenerate geometry** | `event_from_news` writes only 3 of 8 channels, and two of them are collinear in `\|tone\|` (`memory.py:196-198`), so all news signatures lie on a 2-parameter curve. Cos>0.80 is therefore near-generic, not selective. **Measurement:** fraction of `remember()` calls that trigger ≥1 boost, over the actual injected event stream; and the steady-state salience distribution. If it is near 1.0, "a society repeatedly hit develops permanent sensitivity" is an artefact of the signature encoder, not of the society. |
| "Events generated by us become objects in their world" | docstring `memory.py:1-29` | **ASSERTED for the canonical loop** | **Nothing in `live_one_day` ever calls `Chronicle.remember`.** All call sites are exogenous: `observer.py:75`, `timeline.py:239`, `models.py:190`, `branch.py:98`, `historical.py:201`. A bare world run has an empty chronicle forever; `chronicle.tick`/`spread` (`alive.py:415-416`) are no-ops. Cascade firings write `cascade_residues` dicts (`alive.py:520`), **not** `Memory` objects — they never enter decay/rehearsal/spread. |
| `spread` now uses the world RNG | `memory.py:112-114` docstring; code `:139`, `:185` | **DESIGNED (verified in code)** | The claim "any run with a non-empty chronicle was unreproducible" is a historical claim (ASSERTED); the current code demonstrably takes `rng` from the caller (`alive.py:416`). |
| `CHRONICLE_INDEX v1` is bit-identical | `memory.py:146-189`, gated by `EARTH1_CHRONICLE_INDEX == "v1"` (`:128`) | **ASSERTED** | Off by default. The stated gate ("20k day-30/90 world-hash equality") is a measurement claim. |
| Journal field `oldest_days` | `memory.py:96-98` | **defect** | Computes `max(salience)`, not an age in days. Any figure or table citing `oldest_days` is mislabelled. |

## `earth1/influence.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| **Agent-to-agent state transfer exists** | `influence.py:232-248`; `sample_partners` `:186-202`; `dyadic_move` `:205-217` | **EMERGENT (transmission) from DESIGNED law** — interaction of `fabric.adj` weights × per-agent `susceptibility` × partner's current forces | `delta = f[partner] - f`; `f += sus·mu·delta`, three sequential rounds per day with `f` updated between rounds (`:243-247`), so within-day chains of length ≤3 exist. This is the load-bearing positive answer to the decisive question. |
| **Conviction does NOT condition the canonical influence kernel** | `influence.py:232` — `alpha` is a parameter of `propagate` and **is never read in the body** (`:240-248`) | **The module's central docstring claim (`:1-34`) is false of the canonical code** | `alpha`'s only live effect is `susceptibility.py:52`: `s *= (1.25 - 0.5·alpha)`, a **channel-uniform** scalar gain. There is no pole term, no alignment weight, no `beta` on the canonical path. |
| `beta` — "the parameter that decides whether the world is chaotic" | docstring `influence.py:22-29`, `BETA=1.0` at `:40`; `CANONICAL_DAY["beta"]=2.0` at `alive.py:99`; `live_one_day(beta=…)` at `alive.py:220` | **DEAD PARAMETER** | `beta` and `layers` are accepted by `live_one_day` and **never used** (only occurrences in `alive.py` are lines 92, 99-100, 220, 224). `propagate` swallows them via `**_ignored` (`influence.py:236`). The pole-alignment law that `beta` controls lives only in `propagate_meanfield_legacy` (`:46-99`), explicitly LEGACY_COMPARISON_ONLY (`:159-162`). **Do not describe Earth-1 as running a conviction-conditioned polarizing kernel.** |
| Conviction is a log-odds update driven by encounter evidence | `influence.py:220-229` (`accumulate_drive`), `:251-269` (`update_conviction`), gain 0.003 (`:167`) | **EMERGENT (weakly)** — interaction of partner draw × current force dispersion | Genuine: alpha's motion depends on *who you met and how far they were*. |
| "Bounds are asymptotes of the log-odds form, **not a ratchet**" | docstring `influence.py:257-258`; drive formula `:226` `clip((0.5 − d_e)/0.5, −1, 1)` | **ASSERTED — and structurally suspect** | `d_e` is the *mean* absolute difference across 8 channels. Drive is negative only when `d_e > 0.5`, which requires a partner half a unit away on average across all eight channels. Given homophilous partner sampling and post-relax force concentration, drive will be positive for nearly every encounter, making alpha a de-facto one-way drift. **Measurement:** histogram of `d_e` over all encounters and `P(drive < 0)` per day. `scripts/disagreement_probe.py:1-13` is the existing instrument for exactly this and its own docstring flags "the natural fraction with net-negative drive" as open. |
| **Encounter randomness does not depend on the world seed** | `influence.py:242` `default_rng(ENCOUNTER_SEED_TIE + int(day))`; same at `feed.py:173` | **DESIGNED — with a consequence for ensemble statistics** | The uniform stream is a function of the *day index only*. Two ensemble members with different genesis seeds share the entire encounter uniform stream; the encounter channel contributes **zero** run-to-run variance at fixed population size. The docstring frames this as "common random numbers for paired branches" (`:152-156`), which is true and useful — but any ensemble-spread or confidence figure in the paper must state that partner draws are not resampled across replicates. |
| Isolation decay of conviction is disabled | `influence.py:130-135`, `CONVICTION_DECAY` `:43` | **DESIGNED (off)** | In the legacy law only; irrelevant to the canonical path. |

## `earth1/culture.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Hofstede 6-dim and Inglehart 2-dim per country | `culture.py:14-92`, `:97-175` | **DESIGNED (external data table)** | Static literals. No time dimension, no dynamics, no agent state. |
| Culture *propagates* between agents | — | **does not exist in this module** | `culture.py` is a lookup table with 5 accessors (`:181-217`). Its only consumers are `genesis.py:22,324-326` and `population.py:6,198-201` — i.e. it conditions **birth values only**. `Force.CULTURE` thereafter moves only via the generic operators. Cross-country cultural differences in the running world are a **genesis imprint**, not a cultural process. |
| Culture is *restored* toward its genesis value every day | `life.py:398` (`force_baseline = civ.forces.copy()` at birth), `life.py:763,791`, `alive.py:402` (`relax=0.045`) | **DESIGNED** | The single most important structural fact for the "does culture propagate" question: every agent is pulled 4.5%/day back toward a target anchored on its **genesis** force vector. |
| The one live path by which social experience edits the anchor | `alive.py:527-533` (`trait += residue·(f_i − neighbourhood_mean(f))`), then `life.py:771-781` with `TRAIT_MEMORY = 1.0` (`life.py:204`) | **EMERGENT** — interaction of `adj_live` × own forces × trait→baseline→target ring | This is a genuine, closed, agent-to-agent feedback ring, and it is **anti-conformist**: it amplifies an agent's *deviation* from its neighbourhood into its own permanent anchor. Best genuinely-emergent candidate in the cluster. Measurement: variance of `civ.openness/doubt/desire_intensity` over time at `residue=0.02` vs `residue=0`. |

## `earth1/knowledge.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Knowledge learned from neighbours who know more | `knowledge.py:108-121` — `nb = (adj@stock)/deg`, `gap = max(nb − stock, 0)` | **EMERGENT** — interaction of `adj_live` × own openness × own deprivation | Genuine network transfer, but **mean-field**: the agent responds to the neighbourhood *average*, not to a named person. This is architecturally the opposite choice from `influence.propagate` (which `influence.py:147-149` explicitly says mean-field "destroys minority signal"). The two propagation laws in the same engine disagree with each other. |
| Learning is ratcheted upward only | `knowledge.py:109` `np.maximum(nb − stock, 0)` | **DESIGNED** | "Nobody unlearns" is enforced, not observed. |
| Learning rates 0.0015 / 0.0004; hardship penalty 0.7 | `knowledge.py:116-120` | **DESIGNED** | The comment at `:113-115` ("the first version moved 2%/day, which saturated the population inside a year") is an **ASSERTED** historical measurement. |
| Scientists are the top 0.5% by knowledge | `knowledge.py:48`, `:133-135` | **DESIGNED (relative rank)** | The comment at `:44-47` ("an absolute cutoff made 61% of the population scientists") is **ASSERTED**. |
| Discovery rate rises with connectedness to other scientists | `knowledge.py:136-137` — `peers = adj @ scientists`, `rate = 0.06·(1+0.5·peers)·dt` | **EMERGENT** — interaction of graph topology × the knowledge distribution's top tail | Genuine two-component interaction. But note `peers` is a **weighted** count, unnormalised, so it inherits the degree artefacts above (large-country agents have more weak ties → higher discovery rate). Measurement: discovery rate vs country population share; if correlated, the "collaboration multiplier" is a graph-construction artefact. |
| Global knowledge stock as a permanent ratchet | `knowledge.py:146-147` (`+2.5e-6` per discovery, clipped to 1.0) | **DESIGNED** | A hand-set increment. |
| Status | `knowledge.py:129-130` — fixed 0.30/0.25/0.25/0.20 blend | **DESIGNED** | Docstring says status "compounds, because status buys access which buys more status" (`:16-18`). **There is no compounding term**: status is recomputed from scratch each tick from wealth/occupation/knowledge/degree and is never an input to anything. Grep confirms `kn.status` has no consumer in the daily loop. **Misleading docstring.** |
| "Beauty is negentropy… works spread along the same social fabric" | docstring `:25-31`; code `:149-167` | **ASSERTED / false as stated** | Works **do not spread**: `works_made` is a per-agent counter and `living_works` is a single global float with a decay (`:158-159`). No graph term. The reported `negentropy` (`:164-167`) is `std(forces of makers) − std(mean force vector of makers)`, a summary statistic of a random subset, not a property of any artefact. |

## `earth1/susceptibility.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Per-agent, per-channel gain on all incoming force | `susceptibility.py:42-78`, applied at `alive.py:364` then to ties (`:372`), contagion (`:381,385`) and feed (`:399`) | **DESIGNED** | Every coefficient is hand-set. The array is recomputed from scratch each tick — it carries no history. |
| Age plasticity | `:48` `clip(1.35 − 0.7·age, 0.45, 1.4)` | **DESIGNED** | Linear; the clips never bind (`civ.age ∈ [0,1]` → range 1.35…0.65). The docstring's "rises sharply through the twenties then plateaus" (`:25-27`) describes a curve the code does not implement. **Misleading docstring.** |
| Conviction reduces movability | `:52` `s *= (1.25 − 0.5·alpha)` | **DESIGNED** | This is the *entire* live effect of conviction in Earth-1 (see influence table). It is channel-uniform — conviction cannot make you hard to move about one thing and easy about another. |
| Addiction locks desire / deafens to the group | `:60-63` | **DESIGNED** | |
| "Susceptibility is why the same event produces revolution in one population and a shrug in another" | docstring `:32-33` | **ASSERTED** | Measurement: identical injected shock (same `Memory`, same scope size) into two populations differing only in `sus`, comparing cascade counts. Nothing in the code establishes it. |

## `earth1/feed.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Feed moves the reader toward a named source's value | `feed.py:166-179`, `dyadic_move(..., weights=AROUSAL)` at `:177` | **EMERGENT (transmission)** — interaction of feed graph × arousal vector × susceptibility | Second genuine agent-to-agent channel. |
| **The canonical feed ignores conviction** | `feed.py:166` — `alpha` is a parameter and is **never read** in the body (`:169-179`) | **The module's thesis ("a polarizing kernel with a much higher effective beta", `:27-31`) is false of the canonical code** | `FEED_BETA_MULTIPLIER = 2.2` (`:46`) and `FEED_ETA` (`:47`) are used **only** by `feed_tick_legacy` (`:123`, `:132`), which is LEGACY_COMPARISON_ONLY (`:159-160`). The live feed is one uniform-weighted encounter at `mu=0.05`, channel-weighted by `AROUSAL`. |
| Arousal-weighted channels ("measured, not alleged") | `feed.py:50-54`, `:162`, applied `:177` | **DESIGNED** | Eight hand-set constants. "Measured repeatedly in diffusion studies" (`:49`) is a literature claim about the world, not a property of this engine. |
| **The feed graph is homophilous** | `feed.py:73-85` — rank on `IDENTITY − FEAR`, connect within `±n/200` ranks | **DESIGNED AT GENESIS — not an emergent echo chamber** | `build_feed` is called exactly once, at `alive.py:74`, on **genesis** forces. It is never rebuilt (only rows/cols zeroed on rebirth, `rebirth.py:303`). The "engagement optimiser… converges on agreement" (`:62-65`) is a one-shot draw from the day-0 ordering. Any observed feed echo chamber is a genesis-ordering artefact, and must not be reported as emergent selection. |
| Homophily band width | `feed.py:81` `jitter ∈ ±max(n//200, 2)` | **DESIGNED** | ±0.5% of the population in rank — an extremely tight band, hand-chosen. |
| `FEED_SIZE = 24` "accounts a connected agent effectively reads" | `feed.py:55`; actual peer wiring `feed.py:79` (`range(6)`); `FEED_SIZE` used only for influencer audiences `:94-96` | **defect / misleading constant** | An ordinary online reader gets **6** peer edges plus ≈0.19 expected influencer edges (`n_inf·FEED_SIZE·8 / n = 0.192`), i.e. ~6.2, not 24. |
| Feed edges are unweighted | `feed.py:105` `m.data[:] = 1.0` | **DESIGNED** | Partner sampling over the feed is therefore *uniform* over distinct sources. There is no ranking, despite `:15` ("filtered, ranked, and served continuously"). |
| Asymmetry / no reciprocity | `feed.py:103-106` (never symmetrised) | **DESIGNED** | Correct as described; contrast `fabric.py:210`. |
| Feed access is unequal | `feed.py:69,102` gated on `knowledge.connected`, which is drawn at birth from `CONNECTIVITY` by income tier (`knowledge.py:41,87`) | **DESIGNED** | Fixed for life — `kn.connected` is never updated after birth. |

## `earth1/feedback.py`

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Opinion→trait feedback ("agents develop consistent worldviews that weren't programmed") | docstring `feedback.py:1-6`; `opinion_feedback` `:87-152` | **OFF-PATH — does not run in Earth-1** | The **only** production caller is `earth1/tick.py:203`, and `earth1.tick` is on the QUARANTINED list (`legacy_gate.py:28`). `live_one_day` never calls it. Any claim that Earth-1 agents "develop worldviews" through question-answering feedback is unsupported for the canonical world. |
| Weight-sign-aware reinforcement direction | `feedback.py:112,118-126` | **DESIGNED** (off-path) | The claim that the old code "measurably pushed strong-YES agents away from their own stance" (`:12-14`) is **ASSERTED**. |
| Local trait→force propagation via fixed sensitivities | `feedback.py:46-58`, `apply_trait_delta` `:67-84` | **DESIGNED** | `apply_trait_delta` *is* live-reachable only through `generational.py:225` inside `generational_tick` — which `alive.py` also never calls (it imports only `advance_age`, `alive.py:256`; `generational.py:110-140` explicitly excludes trait drift). |
| "`_recompute_forces` changed forces for ~84% of agents with zero trait changes" | docstring `feedback.py:17-23`, `:155-166` | **ASSERTED** | Historical audit measurement. The current function raises (`:164`), which is a verifiable code property; the 84% figure is not. |
| `TRAIT_BOUNDS` signed `culture_offset` | `feedback.py:64` | **DESIGNED** | The "+0.01 nudge became a +0.096 jump" note (`:61-65`) is **ASSERTED**. |
| Global population anchor refresh | `feedback.py:143` `civ.means[:] = forces.mean(axis=0)` | **DESIGNED** (off-path) | |

---

## Strongest genuinely-emergent findings in this cluster

1. **Dyadic transmission is real and is the cluster's one solid emergent claim.** `influence.propagate` (`influence.py:243-248`) and `feed.feed_tick` (`feed.py:174-178`) both read a specific partner's *current* force vector and move the reader toward it. Agent *i*'s tomorrow is a function of agent *j*'s today. Three sequential encounter rounds with `f` mutated between them (`influence.py:243-247`) create genuine within-day chains. Nothing sets the resulting neighbour-correlation directly. Components that interact: the tie-weighted graph (`fabric.py`), the per-agent susceptibility array (`susceptibility.py`), and the partners' own force states.

2. **The deviation-amplifying trait ring is the deepest emergent structure I found.** `alive.py:527-533` writes `openness/doubt/desire_intensity += 0.02·(f_i − mean(f over neighbours))`; `life.py:771-781` feeds that drift back into the agent's **force baseline** at `TRAIT_MEMORY = 1.0`; `alive.py:402` then relaxes the agent toward that moved baseline. So social position permanently edits the private anchor, and the sign is *anti*-conformist: being unlike your neighbours pushes your anchor further from them. Four components interact (graph, forces, traits, restoring target) and no line sets the outcome. This — not the "conviction kernel" — is the engine's real amplifying channel.

3. **Memory spread is a real network process, but memory *press* is not.** `memory.py:139` genuinely recruits new holders through degree-normalised exposure (emergent). `memory.py:86-89` then gives every holder the **identical** force vector (a common input). A paper figure showing "opinion converging inside a memory's footprint" would be measuring the second, not the first.

4. **Discovery is emergent from topology × the knowledge tail** (`knowledge.py:133-137`) — the top-0.5% cutoff is recomputed daily against a distribution that the learning term is itself moving, so the scientist set is endogenous.

## The most misleading docstring claims found

1. **`influence.py:1-34` — "the conviction-conditioned kernel".** The canonical `propagate` (`influence.py:232`) takes `alpha` and **never reads it**. `beta`, the parameter the docstring calls "what decides whether the world is chaotic", is accepted by `live_one_day` (`alive.py:220`) and used nowhere (`alive.py` mentions `beta` only at lines 92, 99, 220). The entire pole-alignment story describes `propagate_meanfield_legacy`, which `influence.py:159-162` itself declares off-path. Conviction's only live effect is a channel-uniform scalar at `susceptibility.py:52`. **This is the same failure mode as the fat-tails error: a docstring narrating a mechanism the current code does not run.**

2. **`feed.py:27-31` — "a polarizing kernel with a much higher effective beta".** Same defect: `FEED_BETA_MULTIPLIER` is used only in `feed_tick_legacy` (`feed.py:123`). The canonical `feed_tick` (`:166`) also takes `alpha` and never reads it. Worse, `feed.py:10-16` describes the feed as a *running* engagement optimiser, but `build_feed` executes once at genesis (`alive.py:74`) on day-0 forces and is never rebuilt — **feed homophily is drawn at genesis, exactly like the wage tails were.** If the paper reports feed-driven echo chambers, that is a genesis property being mistaken for a process.

3. **`fabric.py:13-18` — "a job loss lands on five people in Lagos and two in Stockholm; this channel dominates in high-fertility countries and barely exists in low-fertility ones".** Measured against `_pairs_within`: household ties are hard-coded at 3 per agent (`fabric.py:149`), and weighted household degree moves only 3.00 → 4.75 from a 2-person to a 6-person household, with the *per-partner* weight running the opposite way (3.0 in a 2-person house, 1.0 in a 6-person house). `TIE_SPEC["household"]`'s `None` "size set by country fertility" (`fabric.py:45`) is never read.

4. **`fabric.py:59-62` — media hubs are "broadcasters, athletes, musicians, scientists, heads of state".** `fabric.py:199` is `rng.choice(n, n_hub, replace=False)`: a uniform random 0.02% of the population, uncorrelated with `knowledge.stock`, `knowledge.status`, occupation or degree.

5. **`knowledge.py:16-18` — status "compounds, because status buys access which buys more status".** `kn.status` is recomputed from scratch every tick (`knowledge.py:129-130`) and has no consumer anywhere in the daily loop. There is no compounding and no feedback. Likewise `knowledge.py:25-31`'s "works spread along the same social fabric" — works have no graph term at all (`:154-159`).

6. **`feedback.py:1-6` — "agents develop consistent worldviews that weren't programmed".** `opinion_feedback` is unreachable from `live_one_day`; its only caller `earth1/tick.py` is quarantined (`legacy_gate.py:28`).

7. **`susceptibility.py:25-27`** claims attitude stability "rises sharply through the twenties and then plateaus"; `susceptibility.py:48` is a straight line in age whose clips never bind.

8. **`influence.py:257-258` — "not a ratchet".** Structurally, negative conviction drive requires mean cross-channel distance to a partner > 0.5 (`influence.py:226`), which homophilous sampling plus daily relaxation makes rare. Treat the symmetry claim as unproven until the drive histogram is reported.

## The decisive experiment for the paper

Run four arms from an identical genesis seed, changing nothing else. The encounter RNG is a private, day-indexed stream (`influence.py:242`, `feed.py:173`) that consumes no world randomness, so zeroing `mu` does **not** desynchronise any other draw — the ablation is clean and the arms stay on common random numbers.

- **A (canonical).**
- **B (no transmission):** `MU_INFLUENCE = 0` and `MU_FEED = 0`.
- **C (no anchor):** `relax = 0`.
- **D (no anchor feedback):** `residue = 0`.

Report, per arm: (i) excess force-correlation of tie-connected pairs over degree-matched random pairs; (ii) Moran's I of each force channel on `fabric.adj`; (iii) within-locality force variance. **If the excess neighbour correlation in arm B is a large fraction of arm A's, the observed "diffusion" is a shared response to a common input** — the homophilous genesis graph (`fabric.py:158-168`), the genesis-anchored restoring target (`life.py:398`, `alive.py:402`), region-level genesis force deltas (`genesis.py:283-288`), and the locality-scoped inputs from weather/institutions/cascades. Arm A−B is the only defensible measure of genuine agent-to-agent influence.

Pair this with a direct transmission test: perturb one force channel in a seed set on a single day and measure the non-seed response over 30 days. `scripts/transmission_probe.py` already implements exactly this instrument (its docstring cites ~0.0018 for the reference arm and a "registered 0.006 floor" — treat both as ASSERTED until re-run). Two further measurements the paper needs from this cluster: the drive histogram (`scripts/disagreement_probe.py`), and — because `influence.py:242` omits the world seed — an explicit statement that ensemble replicates share the entire encounter random stream.

Files read: `/Users/pietronovelli/Documents/GitHub/earth-1-engine/earth1/{fabric,graph_kernels,memory,influence,culture,knowledge,susceptibility,feed,feedback}.py`, plus `alive.py`, `life.py`, `plasticity.py`, `rehome.py`, `generational.py`, `legacy_gate.py`, `types.py` for wiring. Nothing was modified.