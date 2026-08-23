# EARTH-1 API COMPLETENESS AUDIT (main, read-only, 2026-08-23)

Question: can every meaningful component of Earth-1 be accessed through the API, or are only the top-level surfaces connected to `alive.World`?

## Registered API surface (earth1/api/main.py)

Functional on the live 4M Epoch 2: `GET /world` (6 aggregates + identity), `GET /world/countries` (4 aggregates per country with ≥50 alive), `GET /world/earthling/{idx}` (the `observe` view of one LIVING slot), `GET /observatory/standing-readings`, `GET /civ`, `GET /health`.
503 by design: `/ask` and variants (calibration pending), `/forecast/multiverse|scenarios|timeline|tree` (Phase-2), `/forecast/futures/{idx}` (refuses clones above 500k agents — i.e. refuses on the live Earth). 410: `/world/tick`. `/predictions/*` is a DB of predictions (no world access); `/billing/*` is commercial plumbing. `routes_legacy/*` unmounted.

Every functional route carries the identity block (epoch, world_uuid, snapshot sha256, physics_version, world_day). That is the One-Earth proof — it is not an ontology surface.

## Canonical `alive.World` ontology (13 subsystems, measured on a birthed world)

civ (15 trait arrays, forces[N,8], alpha, adj), life (33 arrays incl. firm/firm_health/firm_country, housing, durables, mental/physical/addiction/relationship/social_need/political, last_event), fabric (adj + 7 typed tie matrices + household), health (condition, diagnosed_day, in_treatment, alive, cause_of_death, lifetime_illnesses, declining, falls), knowledge, gov (8 per-country arrays), klass (homeless, criminal, migrated…), chronicle (Memory events with per-agent scope; cascade residues/cooldown/episodes), feed (sparse), climate (7 per-country), flourishing (10 incl. hunger/thirst/hope/meaning/belonging), presence (locality, density, gathering), mobility (car, flights, commute, travelled).

## Classification

| domain | family | class | source | exists | routes | GET | list/search | history | branch-aware | missing surface |
|---|---|---|---|---|---|---|---|---|---|---|
| Population | Earthling (one person) | **DIRECT_API** | civ/life/health arrays, observe.observe | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | no list/search (by country, age, occupation…); 404 for dead slots — a deceased Earthling is unaddressable |
| Population | stable Earthling ID | **NOT_IMPLEMENTED** | slot index idx; rebirth reuses slots (alive._be_born) | no | — | ✗ | ✗ | ✗ | ✗ | no persistent person identity across slot reuse; GET /earthlings/{id} would silently return a different person after rebirth |
| Population | demographic state (country, region, age, education, income, urban) | **INDIRECT_API** | civ.country/region/age/education/income/urban | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | region/income not in observe view; no query by demographic |
| Population | traits/personality (Big-5, Hofstede, openness, empathy, risk…) | **INTERNAL_ONLY** | civ.openness…long_term_orientation (15 arrays) | yes | — | ✗ | ✗ | ✗ | ✗ | GET /earthlings/{id}/traits |
| Population | complete life state | **INDIRECT_API** | life.* (33 arrays) | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | observe exposes ~18 of 33 life fields; durables, rent, arrears, evicted, owns_home, policy_net, baselines, setpoints absent |
| Population | personal history / memory | **INDIRECT_API** | life.last_event, last_event_day, n_events; chronicle.events scope masks | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | only the LAST event code and an event count; no per-person timeline; memories that include the person are not queryable by person |
| Geography | planet (global aggregates) | **DIRECT_API** | world summary, observatory standing readings | yes | GET /world, GET /observatory/standing-readings, GET /civ | ✓ | ✗ | ✗ | ✗ | — |
| Geography | continent | **NOT_IMPLEMENTED** | none (no continent grouping in genesis) | no | — | ✗ | ✗ | ✗ | ✗ | continent is not a model concept |
| Geography | country | **DIRECT_API** | civ.country, GENESIS_COUNTRIES, gov.* per country, climate.* per country | yes | GET /world/countries | ✓ | ✓ | ✗ | ✗ | only 4 aggregates (alive, unemployment, deprived, hope); no GET /places/{iso2}; countries with <50 alive hidden; gov/climate per-country state not exposed |
| Geography | region/state (genesis region) | **INTERNAL_ONLY** | civ.region + regions.RegionalProfile (443 named regions) | yes | — | ✗ | ✗ | ✗ | ✗ | GET /places/{iso2}/regions/{code}; regional profiles (name, economy, history) never served |
| Geography | city | **NOT_IMPLEMENTED** | none — locality is country·region·urban flag; no named cities | no | — | ✗ | ✗ | ✗ | ✗ | city is not a model concept |
| Geography | locality / village | **INTERNAL_ONLY** | presence.locality (country*1000+region*2+urban), locality key in cascade block | yes | — | ✗ | ✗ | ✗ | ✗ | GET /places/localities/{key}: population, forces, hot state, episodes |
| Geography | location hierarchy | **INTERNAL_ONLY** | country→region→urban flag (implicit in key arithmetic) | yes | — | ✗ | ✗ | ✗ | ✗ | no hierarchy endpoint |
| Geography | population membership / presence / movement | **INTERNAL_ONLY** | presence.locality/density/gathering; klass.migrated; mobility.*; journal migrated_today | yes | — | ✗ | ✗ | ✗ | ✗ | where a person is, who is in a place, who moved — none addressable |
| HumanDynamics | canonical forces (8) — stored | **DIRECT_API** | civ.forces | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | per person only; no place-level force readout; no search by force |
| HumanDynamics | effective forces (stored + cascade overlay) | **INTERNAL_ONLY** | alive.effective_forces(w) | yes | — | ✗ | ✗ | ✗ | ✗ | the readout ontology (F_effective) is never served; API shows stored only |
| HumanDynamics | force history | **NOT_IMPLEMENTED** | no per-agent force time series is stored (journal keeps population means only) | no | — | ✗ | ✗ | ✗ | ✗ | history requires a recorder; not a model concept today |
| HumanDynamics | conviction (alpha) | **INDIRECT_API** | civ.alpha | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | — |
| HumanDynamics | susceptibility | **INTERNAL_ONLY** | computed per tick in live_one_day (transient) | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| HumanDynamics | cascade residues / episode state | **INTERNAL_ONLY** | chronicle.cascade_residues, cascade_last_fired, cascade_episode_active | yes | — | ✗ | ✗ | ✗ | ✗ | GET /places/{loc}/cascades, GET /earthlings/{id}/residues |
| HumanDynamics | events affecting an Earthling | **INTERNAL_ONLY** | chronicle.events[].scope (bool mask per agent) | yes | — | ✗ | ✗ | ✗ | ✗ | GET /earthlings/{id}/events |
| HumanDynamics | causal / impact history | **NOT_IMPLEMENTED** | not represented (no provenance chain from event to state change) | no | — | ✗ | ✗ | ✗ | ✗ | impact tracing is not a model concept |
| SocialGraph | nodes | **INDIRECT_API** | civ.adj / fabric.adj (N×N sparse) | yes | GET /world/earthling/{idx} | ✗ | ✗ | ✗ | ✗ | — |
| SocialGraph | edges (neighbours of a person) | **INDIRECT_API** | fabric.adj rows; observe gives COUNTS per tie type only | yes | GET /world/earthling/{idx} | ✗ | ✗ | ✗ | ✗ | no neighbour IDs, no edge list: GET /earthlings/{id}/relationships |
| SocialGraph | relationship type | **INDIRECT_API** | fabric.by_type: household, colleagues, neighbours, friends, weak, diaspora, media | yes | GET /world/earthling/{idx} | ✗ | ✗ | ✗ | ✗ | counts only |
| SocialGraph | edge strength | **INTERNAL_ONLY** | adj data weights (tie-weighted partner sampling) | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| SocialGraph | formation / dissolution | **INTERNAL_ONLY** | plasticity.plasticity_tick (ties_strengthened/weakened/pruned/rewired — journal totals only) | yes | — | ✗ | ✗ | ✗ | ✗ | no per-edge history |
| SocialGraph | family | **INDIRECT_API** | fabric.household id + household ties | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | household_id exposed; members not listable; no parent/child/sibling typing |
| SocialGraph | friendship | **INDIRECT_API** | fabric.by_type['friends'] | yes | GET /world/earthling/{idx} | ✗ | ✗ | ✗ | ✗ | count only |
| SocialGraph | romantic relationships | **NOT_IMPLEMENTED** | life.relationship is a scalar quality, no partner edge | no | — | ✗ | ✗ | ✗ | ✗ | partner/romantic edge is not a model concept |
| SocialGraph | professional relationships | **INDIRECT_API** | fabric.by_type['colleagues'] (from life.firm) | yes | GET /world/earthling/{idx} | ✗ | ✗ | ✗ | ✗ | count only |
| SocialGraph | neighbourhood / community / network | **INDIRECT_API** | fabric.by_type['neighbours','weak','diaspora','media'] | yes | GET /world/earthling/{idx} | ✗ | ✗ | ✗ | ✗ | counts only; no community/place query |
| SocialGraph | graph functions (ego network, path, degree, components) | **INTERNAL_ONLY** | scipy sparse ops in influence/fabric; no query layer | yes | — | ✗ | ✗ | ✗ | ✗ | GET /social-graph/{id}/ego?depth= |
| Economy | job / employment / occupation / tenure / spells | **INDIRECT_API** | life.employed, in_lf, occupation, tenure, spells | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | no search (all unemployed in X) |
| Economy | companies / employers | **INTERNAL_ONLY** | life.firm (id), firm_health[firms], firm_country[firms] | yes | — | ✗ | ✗ | ✗ | ✗ | GET /companies/{id}: health, country, employees |
| Economy | income / wage / wealth / cost | **INDIRECT_API** | life.wage, wealth, cost | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | — |
| Economy | transactions / consumption | **INTERNAL_ONLY** | life.durables, durable_spend, rent, arrears, cost (flows are per-tick scalars, no ledger) | yes | — | ✗ | ✗ | ✗ | ✗ | GET /earthlings/{id}/consumption; no transaction ledger exists |
| Economy | economic state & history (country) | **INTERNAL_ONLY** | journal.jsonl aggregates (unemployment, gini…), gov.tax/welfare | yes | — | ✗ | ✗ | ✗ | ✗ | per-country economic history not served; journal is a file |
| Material | food / water | **INDIRECT_API** | flourishing.hunger, thirst (need satisfaction); climate.farm_share, soil | yes | — | ✗ | ✗ | ✗ | ✗ | not in observe; no resource stocks/flows |
| Material | goods / resources / material flows | **NOT_IMPLEMENTED** | no resource-flow model (durables scalar only) | no | — | ✗ | ✗ | ✗ | ✗ | goods/resource flows are not a model concept |
| Material | purchases | **NOT_IMPLEMENTED** | no purchase events (durable_spend is a rate) | no | — | ✗ | ✗ | ✗ | ✗ | — |
| Material | housing | **INTERNAL_ONLY** | life.owns_home, rent, arrears, evicted; klass.homeless, days_homeless | yes | — | ✗ | ✗ | ✗ | ✗ | homeless share only in /world summary |
| Material | perishability / resource modules | **INTERNAL_ONLY** | perishability.py readout (legacy disposition: pure readout) | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Biology | health state / illness / treatment | **INDIRECT_API** | health.condition, diagnosed_day, in_treatment, declining; life.mental/physical/addiction | yes | GET /world/earthling/{idx} | ✓ | ✗ | ✗ | ✗ | condition code, diagnosis day, treatment, declining not exposed (only mental/physical/addiction) |
| Biology | mortality / cause of death | **INTERNAL_ONLY** | health.alive, cause_of_death; journal deaths by cause | yes | — | ✗ | ✗ | ✗ | ✗ | dead Earthlings return 404; cause of death unreadable |
| Biology | biological history | **INTERNAL_ONLY** | health.lifetime_illnesses, falls (counters only) | yes | — | ✗ | ✗ | ✗ | ✗ | no episode log |
| Institutions | governments / policy | **INTERNAL_ONLY** | gov.tax, welfare, policing, legitimacy per country | yes | — | ✗ | ✗ | ✗ | ✗ | GET /places/{iso2}/government |
| Institutions | war / political state | **INDIRECT_API** | gov.at_war_with, war_days, unrest_norm | yes | GET /world | ✗ | ✗ | ✗ | ✗ | only countries_at_war count |
| Institutions | culture | **INTERNAL_ONLY** | civ.culture_offset, Hofstede dims, regions.force_deltas | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Institutions | collective state (locality/country force means) | **INTERNAL_ONLY** | computed in cascade block / answer_living stance | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Institutions | country / locality statistics | **DIRECT_API** | /world/countries | yes | GET /world/countries | ✓ | ✓ | ✗ | ✗ | 4 metrics; no locality level |
| Institutions | knowledge / science / works | **INDIRECT_API** | knowledge.stock/status/connected/works_made/discoveries | yes | GET /world, GET /observatory/standing-readings | ✗ | ✗ | ✗ | ✗ | mean only |
| Institutions | flourishing (hope, meaning, belonging…) | **INDIRECT_API** | flourishing.* (10 arrays) | yes | GET /world, GET /world/countries | ✗ | ✗ | ✗ | ✗ | mean hope only |
| Institutions | climate | **INTERNAL_ONLY** | climate.* per country | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Physics | physics version identity | **DIRECT_API** | alive.PHYSICS_VERSION via api.deps identity | yes | every route identity | ✓ | ✗ | ✗ | ✗ | — |
| Physics | active modules list | **INTERNAL_ONLY** | alive.live_one_day step order; legacy_gate.PRODUCTION | yes | — | ✗ | ✗ | ✗ | ✗ | GET /physics/modules |
| Physics | parameters | **INTERNAL_ONLY** | alive.CANONICAL_DAY, thresholds.TRANSITION_RULES, manifest.physics_identity() | yes | — | ✗ | ✗ | ✗ | ✗ | GET /physics/parameters |
| Physics | module state (e.g. cascade rules hot set, feed matrix, susceptibility) | **INTERNAL_ONLY** | chronicle cascade state, w.feed, transient per-tick arrays | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Physics | equations / readouts | **INTERNAL_ONLY** | answer_living.readout/stance (in-process) | yes | — | ✗ | ✗ | ✗ | ✗ | /ask is 503 by design (calibration pending) |
| Physics | provenance / version metadata | **DIRECT_API** | journal startup record (commit, service, config hash); EPOCH.json; state.json | yes | every route identity (epoch, uuid, snapshot, physics) | ✓ | ✗ | ✗ | ✗ | commit/config hash not in API identity |
| Events | world events (memories) | **INDIRECT_API** | chronicle.events (Memory: id, label, day, force_signature, scope, salience, half_life, origin) | yes | GET /observatory/standing-readings | ✗ | ✗ | ✗ | ✗ | count only: GET /events, GET /events/{id} |
| Events | locality events (cascade firings) | **INTERNAL_ONLY** | chronicle.cascade_residues (rule, loc, day, effects, h) | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Events | affected Earthlings | **INTERNAL_ONLY** | Memory.scope mask; residue locality membership | yes | — | ✗ | ✗ | ✗ | ✗ | GET /events/{id}/earthlings |
| Events | direct effects | **INTERNAL_ONLY** | Memory.force_signature×salience; residue effects | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Events | persisted effects | **INTERNAL_ONLY** | residue decay levels (cascade_residue_levels); memory salience | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Events | downstream / cascade effects | **NOT_IMPLEMENTED** | not traced (no causal provenance) | no | — | ✗ | ✗ | ✗ | ✗ | — |
| Events | event history | **INTERNAL_ONLY** | journal.jsonl (daily aggregates, news reads); chronicle.total_ever/forgotten | yes | — | ✗ | ✗ | ✗ | ✗ | expired memories are dropped, not archived |
| Futures | create branch | **DIRECT_API** | /forecast/futures/{idx} (per-person futures on full clones); branch.run in-process | yes | GET /forecast/futures/{idx} | ✓ | ✗ | ✗ | ✓ | REFUSED above 500k agents (live Epoch 2 = 4M → 503); no scenario branches (/forecast/scenarios 503) |
| Futures | inspect branch (by id) | **NOT_IMPLEMENTED** | branches are transient return values; no branch object/ID/store | no | — | ✗ | ✗ | ✗ | ✗ | POST /branches, GET /branches/{id} |
| Futures | advance branch | **NOT_IMPLEMENTED** |  | no | — | ✗ | ✗ | ✗ | ✗ | — |
| Futures | compare branches | **INTERNAL_ONLY** | branch.run returns consequence distributions (in-process) | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Futures | query Earthling/place inside a branch | **NOT_IMPLEMENTED** |  | no | — | ✗ | ✗ | ✗ | ✗ | — |
| Futures | branch lifecycle | **NOT_IMPLEMENTED** |  | no | — | ✗ | ✗ | ✗ | ✗ | — |
| Time | current simulation day | **DIRECT_API** | identity.world_day | yes | every route identity | ✓ | ✗ | ✗ | ✗ | no calendar date (epoch has none) |
| Time | historical state / state at time t | **INTERNAL_ONLY** | data/alive is the only live snapshot; off-box dated backups; timeline.restore (snapshot store never built) | yes | — | ✗ | ✗ | ✗ | ✗ | GET /world?day= |
| Time | snapshot / restore | **INTERNAL_ONLY** | persistence.save_world/load_world; timeline._save/restore | yes | — | ✗ | ✗ | ✗ | ✗ | — |
| Time | timeline / scrub | **INTERNAL_ONLY** | timeline.py (designed; store absent) | no | — | ✗ | ✗ | ✗ | ✗ | — |
| Time | assimilation | **INTERNAL_ONLY** | assimilate.py (in-process; design-only per Bible) | no | — | ✗ | ✗ | ✗ | ✗ | — |

## Structural findings

1. **The API is a readout of aggregates plus one per-person view.** Of 78 state families, 9 are directly addressable, and 7 of those are aggregates or identity. The single entity endpoint (`/world/earthling/{idx}`) exposes ~18 of ~90 per-person fields and returns 404 for the dead.
2. **No entity other than 'living slot' and 'country' is addressable.** Regions (443 authored profiles), localities, households, firms, events, memories, cascade episodes, branches — all exist in state, none has an ID route.
3. **No list/search anywhere except `/world/countries`.** A developer cannot ask 'all unemployed in Lagos', 'everyone this memory happened to', 'members of household 4711'.
4. **No history anywhere.** The world keeps current state plus daily population aggregates in `journal.jsonl`; no per-person force/health/work time series, no archived events (expired memories are dropped), no state-at-time-t route; the timeline store was never built.
5. **Social graph is served as seven integers.** Neighbour IDs, edge weights, typed edges, ego networks, paths are all internal. Romantic partnership is not a modelled edge at all.
6. **Branching has no object model.** Branches are in-process return values; the one route is refused at the live scale; nothing can be queried inside a future.
7. **Effective forces — the readout ontology PF-DECAY-2 established — are never served**; the API shows stored forces only.
8. **Earthling identity is a reusable slot**, so 'GET /earthlings/{id}' cannot be stable across rebirth without a person-ID layer.

## Totals

TOTAL CANONICAL STATE FAMILIES: 78
DIRECTLY API-EXPOSED: 9 / 11.5%
INDIRECT ONLY: 19 / 24.4%
INTERNAL ONLY: 37 / 47.4%
NOT IMPLEMENTED: stable Earthling ID; continent; city; force history; causal / impact history; romantic relationships; goods / resources / material flows; purchases; downstream / cascade effects; inspect branch (by id); advance branch; query Earthling/place inside a branch; branch lifecycle
CAN A DEVELOPER ADDRESS EVERY EARTHLING DIRECTLY?: NO — living slots only, by index; dead Earthlings 404; IDs are reusable slots, not persons
CAN A DEVELOPER ADDRESS EVERY GEOGRAPHIC ENTITY DIRECTLY?: NO — country aggregates only; region/locality internal; continent/city not modelled
CAN A DEVELOPER INSPECT EVERY ACTIVE FORCE/PHYSICS STATE?: NO — stored forces per person only; effective forces, residues, parameters, module state internal
CAN A DEVELOPER TRACE EVENTS AND IMPACTS?: NO — memories/firings internal; only a count is served; downstream tracing not modelled
CAN A DEVELOPER QUERY THE FULL SOCIAL GRAPH?: NO — tie-type counts per person only; no neighbour IDs/edges/strength/graph queries
CAN A DEVELOPER QUERY LIFE/WORK/HEALTH/CONSUMPTION?: PARTIAL — work/money/health scalars via observe; companies, housing, consumption, illness detail internal
CAN THE SAME QUERIES RUN AGAINST A BRANCHED FUTURE?: NO — no branch objects; the one branch route is refused at the live 4M scale
IS EARTH-1 CURRENTLY A COMPLETE API-ADDRESSABLE CIVILIZATION?: NO

Missing surface area, exactly: every row above marked INTERNAL_ONLY or NOT_IMPLEMENTED, plus list/search on every family, history on every family, and branch-awareness on every family. No gaps filled. STOP.
