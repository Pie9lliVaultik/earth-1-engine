# CLUSTER 1 — POPULATION GENESIS: DESIGNED vs EMERGENT

**Verdict up front.** In this cluster there is essentially nothing emergent. Every agent attribute at t=0 is either (a) directly drawn from a hand-set distribution, (b) a deterministic algebraic transform of such draws, or (c) a table lookup keyed on country. The single quantity in the cluster that is *derived rather than set* — the adult age pyramid — is derived at genesis by solving a constraint, not grown by interaction, and its "zero free parameters" claim is false (three hand-tuned constants, tuned against the very statistics quoted as its validation). The one measurement I ran that behaves like a genuine emergent observable is the **implied adult crude death rate**, which is nowhere parameterised and falls out of the pyramid × the mortality hazard.

Files audited (absolute paths):
`/Users/pietronovelli/Documents/GitHub/earth-1-engine/earth1/genesis.py`, `popsynth.py`, `census.py`, `regions.py`, `types.py`, `rng.py`, `precision.py`, with corroborating reads of `alive.py`, `fabric.py`, `generational.py`, `life.py`, `culture.py`, `persistence.py`, and `/Users/pietronovelli/Documents/GitHub/earth-1-engine/scripts/c2plus/build_tables.py`, `run_bakeoff.py`.

---

## genesis.py

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Country membership of each agent | `genesis.py:151-166`, `178-179` | **DESIGNED** | `_allocate_countries` from `census["pop"]` shares with `min_per_country=500` floor. |
| "Floor guarantees statistical representation" | `genesis.py:156-158`, docstring `39-45` | **ASSERTED — and false as written** | The floor is applied, *then* the whole vector is rescaled by `scale = total/raw.sum()` (`:157-158`), so no country ends AT the floor. Measured at pop=100k: **157/194** countries hit the raw floor (docstring says 174) and each receives **313** agents, not 500. |
| Census-weight correction | `genesis.py:38-56` | **DESIGNED** | `w = census_share/agent_share`, mean-normalised. Consumed by `branch.py:139`, `poverty.py:62`, `engine.py:134`, `consequences.py:96`, `adapters/multiverse.py:68`. |
| "India 11.2% of agents vs 17.9% of humanity at 100k" | docstring `genesis.py:43-45` | **ASSERTED — verified true** | I measured 11.198% vs 17.884%. The only part of that docstring that holds. |
| Adult age pyramid | `genesis.py:100-136`, `139-148` | **DESIGNED (derived, not grown)** | `f(x) ∝ exp(-r·x)·S(x)`; `r` bisected (`:116-129`) so modelled u18 matches census `u18`. Solved once at genesis, before any dynamics. Not emergent under this audit's definition. |
| "the same Gompertz survival the generational tick kills with — one mortality physics, one pyramid" | comment `genesis.py:66-70` vs `genesis.py:91-95` vs `generational.py:230-232` | **ASSERTED — false** | Genesis uses a **cohort-discounted** LE: `le_eff = le − min(0.1·(age−18), 6.0)`. The killing tick uses `_gompertz_a(le)` on the **raw** country LE for every agent at every age. Two different hazards. |
| "Two census inputs, zero free parameters" | comment `genesis.py:70-71` | **ASSERTED — false** | At least five hand-set numbers shape the pyramid: `_COHORT_LE_SLOPE=0.1` (`:82`), `_COHORT_LE_CAP=6.0` (`:83`), the bisection bracket `(-0.05, 0.10)` (`:116`), and the r-floor `np.clip(..., 0.0, 0.10)` (`:129`). |
| Comment/constant contradiction in the cohort LE discount | comment `genesis.py:77-81` vs constants `genesis.py:82-83` | **ASSERTED — stale by exactly 2×** | Comment says LE rose "~0.2y per calendar year" and the discount is "capped at 12y"; code is `0.1` and `6.0`. The comment describes a superseded parameterisation. |
| p90 adult age ≈ 68, adult CDR in [6,15] | comments `genesis.py:63-64`, `79-80` | **ASSERTED — and the constants were tuned to it** | I measure p90 = **68.0 y** and implied adult CDR = **11.5/1000/yr** (census-weighted 11.6). Landing exactly on the quoted targets while three constants are free means these are **fitted**, not predicted. Measurement to settle: refit `_COHORT_LE_SLOPE`/`_CAP` on a country holdout and report out-of-sample p90/CDR. |
| Urban/rural | `genesis.py:203` | **DESIGNED** | Bernoulli on census `urban`. |
| Income (3 levels), incumbent substrate | `genesis.py:206-213`, `32` | **DESIGNED, and only 4 distinct shapes worldwide** | Thresholds are functions of `edu_hi`, which is a 4-valued lookup on income class. Measured: exactly **4** distinct per-country income distributions across 194 countries; residual cross-country sd ≈ 0.03 is pure sampling noise. LIC still yields 27.3% "high income". |
| Education (3 levels), incumbent substrate | `genesis.py:216-221` | **DESIGNED, 4×3 shapes** | `base_edu = edu_hi + {2:0.28,1:0.08,0:-0.14}[income]`. No country-level education datum enters. |
| Region membership | `genesis.py:279-282` | **DESIGNED** | `rng.choice(p=population_share)`, independent of every other attribute (not conditioned on urban, income, education). |
| Regional force deltas | `genesis.py:262-292`, table `regions.py:47-636` | **DESIGNED** | Hand-authored (Tier 1) or archetype-templated (Tier 2) constants added to force components. |
| Hofstede per-agent (`power_distance`, `individualism`, `uncertainty_avoidance`, `long_term_orientation`) | `genesis.py:296-312` | **DESIGNED** | `clip(rng.normal(national_score, 0.12))`. Measured between-country variance share: **64.9% / 71.5% / 72.1% / 79.4%** — i.e. these arrays *are* the national score plus fixed noise. |
| Hofstede coverage | `census.py:207-321`, `1758-1776` | **DESIGNED (imputed for 84 countries)** | 110/194 countries have published norms; the other **84** receive the arithmetic mean of their world-region (`regional_force_norms`, `census.py:1758-1765`). Those 84 countries carry no country-specific cultural information. |
| Inglehart coordinates | `genesis.py:315-330`, `culture.py:INGLEHART` | **DESIGNED (constant for 118 countries)** | 76/194 covered; **118** receive `{trad_sec:0.45, surv_self:0.45}`. For 61% of countries this channel is a global constant. |
| `culture_offset` | `genesis.py:333` | **DESIGNED** | `(h_ind−0.5)·0.4 + region_culture_delta`. 92.4% between-country variance — it is a country label, not a person property. |
| "Soul scalars": `empathy`, `risk_appetite`, `desire_intensity`, `economic_field`, `conscientiousness`, `agreeableness`, `extraversion`, `neuroticism` | `genesis.py:351-361` | **DESIGNED — near-pure noise** | Measured between-country variance share: empathy **1.9%**, risk_appetite 3.1%, desire_intensity 1.8%, economic_field 1.5%, conscientiousness **0.7%**, agreeableness 1.5%, extraversion 2.3%, neuroticism 1.6%. ≥97% of the variance in each is the hand-set σ (0.15–0.17) around a near-global mean. |
| `openness`, `doubt` | `genesis.py:351`, `:353` | **DESIGNED** | 26.2% / 18.1% between-country — the only "soul" traits carrying real country structure, via `c_open`/`c_doubt` modulation at `:345-347`. |
| The 8 forces at genesis | `genesis.py:365-394` | **DESIGNED (deterministic transform)** | Every force is a fixed linear/clipped combination of already-drawn traits + region delta. No interaction, no dynamics. Between-country shares: FEAR 7.8%, DESIRE 1.8%, ECONOMICS 1.5%, COLLECTIVE 50.3%, IDENTITY 62.5%, CULTURE 73.9%, EXPERIENCE 5.9%, TEMPERAMENT 4.0%. |
| `forces[:, EXPERIENCE]` | `genesis.py:389`, re-imposed `generational.py:227` | **DESIGNED (identity map)** | EXPERIENCE *is* `civ.age`, rewritten every tick. It can never be emergent; any result attributing something to "the experience force" is attributing it to age. |
| DEMO→FORCE age gradient | `genesis.py:400-411`, `data/demo_force_gradient.v1.json` | **DESIGNED (fitted)** | File self-reports `"status": "FITTED"`, n_items 98, split `sha256(iso2)%2`. Its own `sign_concordance` block records **3 of 8** betas disagreeing with the pre-committed sign (FEAR, ECONOMICS, COLLECTIVE). Flag-gated (`EARTH1_DEMO_FORCE_GRADIENT=v1`), off by default. |
| `alpha` (conviction) | `genesis.py:414` | **DESIGNED** | `0.28 + 0.62·openness` after algebra. Deterministic in openness; 26.2% between-country, identical to openness. |
| `means` | `genesis.py:417` | **DESIGNED (aggregate statistic)** | `forces.mean(axis=0)`. Recomputed at `generational.py:316`, `feedback.py:143`, `living.py:331`. |
| Genesis social graph, "~80% within-country" | `genesis.py:518-591`, docstring `530-536` | **ASSERTED — true but the object is discarded** | Measured 79.7% by edge count / 92.9% by weight, so the docstring is numerically right. But `alive.py:64` does `civ.adj = fab.adj` — I confirmed `w.civ.adj is w.fabric.adj` is True. In the canonical world `_build_graph` is dead code; the live graph is 98.4% within-country. Only the quarantined `engine.py:52` path uses it. |
| WVS-injected `religiosity`/`marital`/`employed`/`ideology`/`social_class` | `genesis.py:435-491` | **DESIGNED, and inert** | Drawn from `P(x \| country, age_bucket, education)` tables. Repo-wide grep: **zero readers** in `earth1/`; the only consumer anywhere is `scripts/c2_measure.py:57`. The comment's claim that this is "the first agent property that carries information no country mean contains" (`:425-427`) is true of the *draw* and irrelevant to the *physics*, which never reads it. |
| Fallback for the 130 unsurveyed countries | `genesis.py:458-465` | **ASSERTED** | Comment: "'neutral' (0.5) measured better than 'globalmean'". Code establishes only the switch. Measurement needed: the A/B that produced that ranking, with the metric named. |
| `civ.sex` | `genesis.py:513-514` vs `types.py:81-135` | **DESIGNED, off-contract** | Assigned as a dynamic attribute; `Civilization` declares no `sex` field. Consequence: `persistence.py:163-167` (`_feed` walks `__dataclass_fields__`) excludes it, so `world_hash` cannot distinguish two C2+ worlds that differ only in sex. Read only by `tests/test_popsynth.py` and `scripts/calibrate/decompose.py`. |
| "Layer 2: Cultural dimensions from force_norms + **within-country distributions**" | module docstring `genesis.py:6` | **ASSERTED — false** | `get_within_country` is imported at `genesis.py:19` and **never called**. Same for `sample_region` (`genesis.py:21`). Repo-wide, `WITHIN_COUNTRY` is touched only by `tests/test_census.py`. |
| Which attributes are "grown" rather than drawn | writers survey across `earth1/` | **structural finding** | Only `forces`, `alpha`, `age`, `age_bucket`, `openness`, `doubt`, `desire_intensity` are ever mutated post-genesis (`alive.py:370,402-403,529-532`, `generational.py:139,216-227`, `feedback.py:83,139`, `feed.py:137,178`, `memory.py:86`, `mobility.py:169-173`, `weather.py:172`, `observer.py:58-64`, `timeline.py:224-230`). The other **12** trait arrays — empathy, risk_appetite, economic_field, culture_offset, conscientiousness, agreeableness, extraversion, neuroticism, power_distance, individualism, uncertainty_avoidance, long_term_orientation — plus `education`, `income`, `urban`, `region`, `country` are **frozen at the genesis draw for the entire life of the world** (education/income/urban change only at rebirth, `generational.py:298-304`). |

## popsynth.py (C2+ substrate)

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Joint (sex, age, edu, income, urban) draw | `popsynth.py:29-51`, `:45` | **DESIGNED** | Flatten the 216-cell country table, `rng.choice` on the normalised weights. A direct multinomial draw from a fitted table. |
| "the per-country IPF table in `data/c2plus_tables_v1.json`" | docstring `popsynth.py:5` vs `:16` | **ASSERTED — false** | Default is `c2plus_tables_v2.json` (`EARTH1_C2PLUS_TABLES`). v1 and v2 differ materially: v2 applied the income frame repair (`build_tables.py:55-67`). |
| Within-band age | `popsynth.py:48-50` | **DESIGNED, and destroys the pyramid shape** | `age_raw = lo + U(0,1)·(hi−lo)`. The top band is 65–90 uniform. The survival-derived shape genesis solves for at `genesis.py:100-136` survives only at 6-band resolution; inside bands it is flat. Directly contradicts the "one mortality physics, one pyramid" framing. |
| IPF table provenance | `scripts/c2plus/build_tables.py:37-54`, `:99-101` | **DESIGNED (seeded from a global pool)** | The IPF seed is `pool = mean of all surveyed WVS country tables` (`:39`) — one global association structure raked to per-country margins. Only the *margins* are country-specific. |
| Coverage of the "measured joint" | `data/c2plus_tables_v2.json` meta | **DESIGNED (mostly imputed)** | Measured meta: `surveyed: 63`, `tier_fallback: 131`. **131/194** countries get income-tier-pooled edu/income margins, i.e. one of 4 patterns again. |
| Income margin | `build_tables.py:68-98` | **DESIGNED — circular** | v2 rakes the income margin back to **the incumbent genesis income distribution** (`_genesis(200_000, 4242)`), for all 194 countries (`income_frame_repaired: 194`). So the "measured joint" substrate's income marginal is the incumbent's 4-valued designed guess. Only the copula is WVS-derived. |
| Age margin | `build_tables.py:82-84` | **DESIGNED — circular** | Age band margins come from genesis's own `_sample_adult_ages`, not from WVS or census age data. |
| "+24.8% withheld-joint win" | comment `build_tables.py:61-62` | **ASSERTED** | A bake-off result (`run_bakeoff.py:170-199`). Code establishes the protocol, not the number. Measurement needed: rerun `stage_run` and report the per-country LOO `mae_kway` for k=2,3 with CIs. |
| "genesis has NO sex attribute -> CANNOT_EXPRESS" | `run_bakeoff.py:9-10`, `:194-195` | **DESIGNED (scoring convention)** | M1 is given the true sex margin and scored as independent on that axis — a favourable-to-incumbent convention that should be stated in any paper reporting the bake-off. |

## census.py

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| 194-country demographic table (`pop`, `med_age`, `urban`, `male`, `u18`, `tfr`, `le`, `income`) | `census.py:9-204` | **DESIGNED** | Frozen literals. Only `pop`, `urban`, `male`, `u18`, `le`, `income`, `tfr` are consumed; `med_age` is read at `genesis.py:188` into `c_med_age` and then **never used** — it is a free out-of-sample check on the derived pyramid. |
| "extracted 2026-08-12 from Supabase research API", "UN WPP 2024, World Bank, Pew" | docstring `census.py:1-4` | **ASSERTED** | Unverifiable from code, and partly contradicted below. Measurement needed: a provenance diff of each column against the named sources. |
| `FORCE_NORMS` (Hofstede) | `census.py:207-321` | **DESIGNED** | 110 countries. |
| Regional-average imputation | `census.py:1758-1776` | **DESIGNED** | 84/194 countries get a region mean, silently — `effective_force_norms` returns it with no provenance marker, so downstream code cannot tell measured from imputed. |
| `WITHIN_COUNTRY` distributions | `census.py:324-1724` | **DESIGNED — archetype templates, and dead** | Not the 194-country data the docstring implies. Measured distinct patterns: age_bucket **5**, occupation **7**, worldview **12**, education **32** across 194 countries. `income_decile` is **2** patterns, and 193/194 are the literal uniform `d1..d10 = 0.1` — a placeholder, not census data. Nothing in `earth1/` reads any of it. |
| `WORLD_REGIONS`, `get_region` | `census.py:1727`, `1745-1755` | **DESIGNED** | Hand-assigned region label per country. |

## regions.py

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| Tier 1 hand-authored regions | `regions.py:47-636` | **DESIGNED** | Force deltas are authored constants (e.g. `{"collective":0.06,"identity":0.04,"culture":0.05}` for IN-NOR, `:52`). |
| "Tier 1 — top 30 countries: 5-12 hand-authored regions each" | docstring `regions.py:9` | **ASSERTED — false** | Measured: **28** countries, **3 to 7** regions each. No country has 12, and none has more than 7. |
| "Tier 2 — next 70 countries: 3-5 template-derived regions" | docstring `regions.py:10` vs `:661-691`, `:705-712` | **ASSERTED — false** | `_make_tier2` always emits exactly **3**. Measured: **72** countries, all with exactly 3. |
| "Tier 3 — remaining 94" | docstring `regions.py:11`, code `:714-722` | **DESIGNED — correct** | Measured 94. All 94 have empty `force_deltas`, so the regional channel is a no-op for them. |
| Tier 2 force deltas | `regions.py:642-658`, `685-690` | **DESIGNED — 3 templates, not geography** | Every Tier-2 country gets the same CAP/RUR/PER triple with shares 0.35/0.40/0.25 and the same archetype deltas, varied only by a 4-way region test at `:676-683`. "What makes a Sicilian different from a Milanese" (`:5-6`) does not apply below Tier 1. |
| `sample_region` | `regions.py:758-769` | **DESIGNED, unused** | Imported by `genesis.py:21`, never called; genesis re-implements the draw inline at `:279-282`. |

## types.py

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| `Force` enum, `NUM_FORCES` | `types.py:8-20` | **DESIGNED** | The eight-force ontology is an axiom of the model, not a result. |
| `PERISHABILITY_HALF_LIFE` (14 → 9000 days) | `types.py:69-78` | **DESIGNED** | Hand-set half-lives per force. Read by `temporal.py:25,73`, `perishability.py:8,17-18`, `engine.py:12` — the legacy/opinion path, not `alive.live_one_day`. |
| `Civilization` field set | `types.py:81-135` | **DESIGNED (schema)** | 20 per-agent arrays + graph + means. No `sex` field — see the `civ.sex` row above. |
| `person_id`/`parent_id` | `types.py:120-131` | **DESIGNED, inert** | The comment "State only — nothing in the dynamics reads them" (`:128`) is one of the few self-descriptions in this cluster that the code confirms. |
| `CauseOfDeath` code 5 ambiguity + `resolve_cause` | `types.py:22-66`, `49-66` | **DESIGNED (contract)** | The refusal to guess is real code (`raise ValueError` at `:60-64`). The historical claim "it was 5 before 2026-08-19 (world day ~394)" is **ASSERTED**; settle by `git log -S` on the WAR constant. |

## rng.py

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| `make_rng(seed)` | `rng.py:6-7` | **DESIGNED** | `Generator(PCG64(seed))`. |
| "every run is reproducible" | docstring `rng.py:1` | **ASSERTED — scope-limited** | Reproducible only if every stream is derived deterministically. Genesis in fact spans five independently seeded generators: `make_rng(seed)` (`genesis.py:173`), `make_rng(seed+1)` for the graph (`:420`), `default_rng([seed,777])` (`popsynth.py:36`), `default_rng(seed+99)` (`genesis.py:439`), plus `seed^0xFAB` (`fabric.py:119`), `seed^0x11FE` (`life.py:317`), `seed^0x5A5A` (`alive.py:83`). Deterministic, but the additive offsets (`seed+1`, `seed+99`) mean seeds 42 and 41 share a stream by construction if the offsets ever collide. Measurement: a seed-sweep independence check across the additive-offset family. |
| `sigmoid`/`logit` | `rng.py:10-16` | **DESIGNED** | Clipped at ±500 / 1e-7. |

## precision.py

| behaviour | mechanism (file:line) | class | note / measurement needed |
|---|---|---|---|
| float32 conversion walk | `precision.py:31-98` | **DESIGNED** | Reflective, aliasing-preserving; `arr_memo` keyed on `id(a)` (`:48-55`) keeps shared arrays shared. |
| `float16-control` as "the pre-registered DEGRADED control" | docstring `:13-17`, code `:40-41`, `:101-104` | **DESIGNED — but it degrades only the initial condition** | `astype(float16).astype(float32)` runs **once at load**; `recoerce` (`:101-140`) only casts f64→f32 and never re-quantizes. So after day 0 the "f16 control" is an f32 run from a quantized start, not an f16 trajectory. Any equivalence gate must state that. |
| "so an f32 artifact can never masquerade as f64" | docstring `:181-182`, code `:178-183` | **ASSERTED — half true** | `world_precision` maps only f64 and f32. A `float16-control` world reports **`"float32"`**, so the degraded control *can* masquerade as a legitimate f32 executor in a manifest. Fix would be reading `w._precision` (set at `:97`). |
| `float64_survivors` | `precision.py:142-175` | **DESIGNED (diagnostic)** | Detects upcast leaks; makes no claim about model semantics. |
| "float32 may change REPRESENTATION, never model semantics" | docstring `:3-4` | **ASSERTED** | A founder ruling, i.e. a policy, not a code property. Measurement named in the file itself (`ops/alive/PRECISION_EQUIVALENCE_PROTOCOL_0_7.md`); the paper should cite the gate result, not the ruling. |

---

## The strongest genuinely-emergent findings in this cluster

Honestly: three, and only the first is unambiguous.

**1. The implied adult crude death rate is emergent.** It is set nowhere. It is the product of two independently constructed objects: the genesis age pyramid (`genesis.py:100-148`, from census `u18` + `le`) and the mortality hazard the tick applies (`generational.py:230-232`, from `_gompertz_a(le)`). I measure **11.5 deaths/1000 adults/yr** unweighted, **11.6** census-weighted. No line of code names a death rate. This is a real interaction of two components and is the correct thing to report as emergent — with the caveat below that the two components disagree about which hazard is real, so the CDR is emergent from an *inconsistency* as much as from a physics.

**2. The cross-country ordering of adult median age is derived, not fitted.** `med_age` is loaded (`genesis.py:188`) and never used; the pyramid is solved from `u18` and `le` alone. So the per-country adult median age is a genuine out-of-sample prediction of the stable-population solve. It is checkable and I checked it: JP 49.5 (census all-age 49.9), DE 49.0 (46.7), US 47.5 (38.9), IN 40.5 (28.8), NG 32.0 (17.9), NE 35.0 (15.5). The adult-vs-all-age framing makes the comparison generous, but the *spread* is visibly compressed — the model puts only 17.5 years between Niger and Japan. That compression is the honest headline finding, and it is a prediction, not a fit.

**3. Household size heterogeneity at t=0 propagates from a single census column.** `fabric.py:76-88` derives household size from `tfr` alone (`1.2 + 0.9·tfr`), and `build_fabric` then cuts households per country (`:126-148`), which makes the day-0 shock-propagation geometry a consequence of fertility. This is a genesis-adjacent interaction (census column × graph construction) rather than a drawn quantity. Weak, but real.

**Everything else in Cluster 1 is designed.** In particular, do not claim personality or cultural heterogeneity as emergent: I measured the between-country variance share of every genesis trait, and for the eight "soul scalars" it is **0.7%–3.1%**. Those arrays are a hand-set Gaussian of σ≈0.16 around a nearly global mean. The four traits that *do* carry country structure (65–79%) carry it because they are literally the national Hofstede score plus noise. This corroborates the standing audit note that trait variance is too narrow, and sharpens it: the problem is not the width of the noise, it is that there is almost nothing but noise.

## The most misleading docstring claims found

Ranked by how badly they would damage a paper.

1. **`genesis.py:66-70` — "the same Gompertz survival the generational tick kills with — one mortality physics, one pyramid."** False. Genesis builds the pyramid with a cohort-discounted life expectancy (`:91-95`); the tick kills with the raw country LE (`generational.py:231`). The engine's flagship internal-consistency claim does not hold, and it is exactly the kind of claim a reviewer will check first.

2. **`genesis.py:70-71` — "Two census inputs, zero free parameters."** False, and self-servingly so. Five hand-set numbers shape the pyramid, and the two most consequential (`_COHORT_LE_SLOPE=0.1`, `_COHORT_LE_CAP=6.0`) sit directly beneath a comment quoting the very diagnostics (p90 age, adult CDR band) that I measure the model hitting exactly. That is a fit presented as a derivation.

3. **`genesis.py:77-83` — the LE-drift comment is stale by exactly 2× in both numbers** ("~0.2y per year" vs `0.1`; "capped at 12y" vs `6.0`). Anyone reading the comment and reporting the parameterisation would publish numbers twice the ones the code runs.

4. **`genesis.py:6` — "Layer 2: Cultural dimensions from force_norms + within-country distributions."** The within-country distributions are never used; `get_within_country` is imported and never called. Worse, the tables it names are archetype templates (5 distinct age-bucket patterns across 194 countries) and the income-decile block is a literal uniform placeholder for 193 of 194 countries — so a paper repeating this claim would be citing non-data that is also non-executed.

5. **`genesis.py:39-45` — the census-weight docstring's "the genesis floor guarantees statistical representation… 174/194 countries sit AT the floor."** The floor does not survive its own function: the rescale two lines later (`:157-158`) drops every floored country to 313 agents at pop=100k, and the count is 157, not 174. The India figures in the same paragraph are correct, which is what makes the passage dangerous — it reads as verified.

6. **`genesis.py:530-536` — the social-graph docstring.** Numerically accurate (I measure 79.7% within-country) and completely beside the point: `alive.py:64` overwrites `civ.adj` with the fabric graph, which I confirmed is 98.4% within-country. Any statement about "the Earth-1 social graph" sourced from this docstring describes an object the canonical world discards microseconds after building it.

7. **`popsynth.py:1-9` and `scripts/c2plus/build_tables.py:55-67` — the C2+ substrate presented as a measured joint.** Three separate circularities the code makes plain: the IPF seed is one global pooled association structure, not per-country (`build_tables.py:39`); the age margins come from genesis's own sampler (`:82-84`); and in v2 the income margin is raked back to the incumbent genesis income distribution for all 194 countries (`:96-98`, meta `income_frame_repaired: 194`). Combined with `surveyed: 63 / tier_fallback: 131`, the defensible claim is narrow: *the C2+ substrate imports a WVS-derived association structure and nothing else.*

8. **`genesis.py:425-427` — "the first agent property that carries information no country mean contains."** True of the draw, misleading in context: `religiosity`, `marital`, `employed`, `ideology`, `social_class` have zero readers in `earth1/`. The information is injected into the population and never consulted by the physics.

9. **`regions.py:9-11` — the coverage tiers** (30 countries × 5-12 regions; 70 × 3-5). Actual: 28 × 3-7, 72 × exactly 3, and all 94 Tier-3 countries carry empty force deltas. A paper reporting "sub-national resolution for 100 countries" would be overstating both breadth and depth.

10. **`precision.py:178-182` — "so an f32 artifact can never masquerade as f64."** The guard works in the direction stated and fails in the direction that matters: the deliberately degraded `float16-control` executor reports itself as `"float32"`. Combined with `recoerce` never re-quantizing (`:101-104`), the "degraded control" is an f32 run with a quantized initial condition — which should be stated explicitly wherever that control is cited as a rejection demonstration.
