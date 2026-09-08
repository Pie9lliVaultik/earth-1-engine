# Earth-1 API — Legacy / Live-World Surface Reference

**Scope**: every mounted route OUTSIDE `/v1` — 95 of the 108 paths in
`docs/openapi.json`. Generated 2026-09-08 by reading the code at the cited
lines; a handful of responses were captured live via in-process
`fastapi.testclient.TestClient` and are marked *(captured)*. Everything else
is code-derived. Where behavior could not be established from the code it is
marked **unknown** rather than guessed.

**Audience**: third-party app integrators. Endpoints that answer 503/410 *by
design* are part of the contract and documented as such.

App factory: `earth1/api/main.py:51`. Version string `0.5.0`
(`earth1/api/main.py:55`).

---

## 1. World resolution — which Earth answers

All world-backed routes resolve **THE canonical daemon world** through
`deps.get_world()` (`earth1/api/deps.py:78`):

- Loads `$EARTH1_ALIVE_HOME/world.pkl` (default `<repo>/data/alive/`,
  `earth1/api/deps.py:34-36`) through the canonical loader (checksum,
  schema, wholeness — `earth1/api/deps.py:56`). `state.json` beside it
  supplies epoch/uuid/sha.
- The snapshot is **the daemon's persisted world**: `earth1-alive.service`
  is the single writer; the API re-reads the snapshot and never mutates it
  (`earth1/api/deps.py:20-23`). Cached in-process; reloaded only when
  `state.json`'s `sha256` changes (`earth1/api/deps.py:90-94`).
- If the snapshot is missing or fails the loader, **every** world-backed
  route returns `503 {"error": "canonical_world_unavailable", "detail",
  "note": "there is no legacy fallback by design"}` via the app-level
  exception handler (`earth1/api/main.py:68-74`). *(captured)*
- `clone_world()` (`earth1/api/deps.py:112`) hands branch/forecast paths a
  **deep clone of the complete civilization** — never a reduced one.
- `get_history()` (`earth1/api/deps.py:101`) opens `history.sqlite` beside
  the snapshot, or returns `None` (pre-API-COMPLETE-1 epochs). History-backed
  responses then return empty lists plus an honest `coverage` block.

### The `identity` envelope

Nearly every non-branch response carries `identity`
(`earth1/api/deps.py:65-74`):

```
physics_version, epoch, world_uuid, world_day, alive, population,
schema_version, snapshot_sha256, checksum, source
```

### The `coverage` block

Every history-backed response carries `coverage`
(`earth1/api/readouts.py:129-146`): `history_available`,
`history_available_from_day`, `last_recorded_day`,
`force_sampling_interval_days` (= 30, `earth1/history.py:27`),
`force_samples_are_continuous` (false), `locality_and_country_series_daily`,
`person_events`, `complete_event_history`, `backfilled`, `retention`,
`note` ("days before history_available_from_day are UNRECORDED, not
uneventful"). When there is no history file: `history_available: false` plus
a `reason`.

### The 8 forces

Force keys used throughout (`earth1/types.py:8-16`, lowercased at
`earth1/api/readouts.py:20`): `fear, desire, economics, collective,
identity, culture, experience, temperament`.

### Locality id scheme

`locality_id = country_index*1000 + region_index*2 + urban(0|1)`
(`earth1/geography.py:51-58`). Odd id = urban = "city". 194 countries
(`earth1/genesis.GENESIS_COUNTRY_CODES`, verified len 194).

---

## 2. Auth & middleware — the honest picture

Two independent layers exist. **Layer 1 wraps the whole app (including
`/v1`); Layer 2 applies only inside `/v1` route handlers.** Legacy routes
see only Layer 1.

### Layer 1 — app-wide `X-API-Key` middleware (DB-backed)

`APIKeyMiddleware` (`earth1/api/auth.py:68-108`):

- **Off by default.** Active only when `EARTH1_AUTH_REQUIRED` is set to any
  non-empty value (`earth1/api/auth.py:75`). When off, every legacy route is
  anonymous.
- When on: `/health` is the **only** exempt path (`earth1/api/auth.py:72`).
  Missing header → `401 {"error":"missing_api_key"}`; DB not configured →
  `503 {"error":"auth_unavailable"}`; unknown/inactive key →
  `403 {"error":"invalid_api_key"}`.
- Keys live in the `api_keys` table as sha256 hashes; raw keys have the form
  `e1-<43 urlsafe chars>` (`earth1/api/auth.py:45`). The matched row is
  attached as `request.state.api_key` (`earth1/api/auth.py:107`).

### Layer 2 — v1 Bearer allowlist (env-backed, fail-closed)

`_auth` (`earth1/api/v1.py:143-165`), documented here only for the
interaction: comma-separated `EARTH1_API_KEYS`; empty allowlist →
`503` (fail closed) unless `EARTH1_DEV_OPEN=1` explicitly enables anonymous
dev access; missing/malformed `Authorization: Bearer …` → `401`; unknown
token → `403`; per-token in-memory rate `EARTH1_API_RPM` (default 30/min) →
`429`.

**Interaction**: with `EARTH1_AUTH_REQUIRED` on, a `/v1` request must
satisfy **both** layers (X-API-Key header for the middleware *and* a Bearer
token for the route). The two key stores are unrelated (DB rows vs env
list). Legacy routes never consult the Bearer layer.

### Middleware stack and execution order

Added at `earth1/api/main.py:59-105`; Starlette is LIFO, so execution
outermost → innermost is:

```
PauseSwitch → APIKey → Budget → RateLimit → CORS → route
```

| Middleware | Trigger | Effect | Ref |
|---|---|---|---|
| PauseSwitch | `EARTH1_PAUSED` in true/1/yes | `503 {"error":"service_paused"}` on everything but `/health` | `earth1/api/middleware.py:45-58` |
| APIKey | `EARTH1_AUTH_REQUIRED` set | see Layer 1 above | `earth1/api/auth.py:68` |
| Budget | auth on **and** key attached | daily request count ≥ key.daily_cap → `429 {"error":"daily_cap_exceeded"}`; DB gone → `503 {"error":"budget_unavailable"}` | `earth1/api/metering.py:95-133` |
| RateLimit | always | token bucket **per client IP**, `EARTH1_RATE_LIMIT` (default 60) req/min; empty bucket → `429 {"error":"rate_limit_exceeded","retry_after_seconds":60}`; `/health` exempt | `earth1/api/middleware.py:14-42` |
| CORS | always | allow all origins/methods/headers, credentials on | `earth1/api/main.py:59-65` |

**Honest caveats integrators must know:**

1. **Usage is never recorded.** `metering.log_usage`
   (`earth1/api/metering.py:32`) has no callers anywhere in `earth1/`
   (verified by repo-wide grep). Consequently `get_daily_usage` always
   reports 0, the Budget middleware's `daily_cap` can never trip in
   practice, and `/billing/usage` returns zeros for `daily_usage`.
2. **Per-key `rate_limit` is not enforced.** The `api_keys.rate_limit`
   column (`earth1/api/auth.py:25`) is stored and reported by
   `/billing/tiers`, but the only active limiter is the per-IP env-configured
   one (`earth1/api/middleware.py:19`). Rate limits are per-process,
   in-memory.
3. **`/billing/webhook` is not exempt from Layer 1.** With
   `EARTH1_AUTH_REQUIRED` on, Stripe's unauthenticated POST would be
   rejected 401 by the middleware before the signature check (only `/health`
   is exempt, `earth1/api/auth.py:72`). Deployments that enable auth must
   account for this.
4. Typed path/query params (e.g. `person_id: int`) return **422** on
   malformed input — standard FastAPI validation, applies everywhere below.

---

## 3. Endpoint reference

Auth for every endpoint below is **Layer 1 only** (app-wide X-API-Key when
`EARTH1_AUTH_REQUIRED` is set; otherwise anonymous), except where a row says
otherwise. "World: daemon" = shared read-only canonical world via
`deps.get_world`. "World: history" = `history.sqlite` beside the snapshot.
"World: none" = DB only, world never loaded.

### 3.1 App-level

| Endpoint | Purpose | Response | Errors | Ref |
|---|---|---|---|---|
| `GET /health` | liveness + world identity | `{status:"ok", world:{identity}}` | `503 {status:"world_unavailable", detail}` when snapshot missing *(captured)* | `earth1/api/main.py:108` |
| `GET /civ` | quick graph stats | `{identity, edges:int, mean_degree:float, top_countries:[{iso2,alive}]×20}` | 503 world | `earth1/api/main.py:119` |

`/health` bypasses **all four** middlewares — it works while paused,
unauthenticated, and un-rate-limited. World: daemon (identity only).

### 3.2 World & epochs

World: daemon.

| Endpoint | Purpose | Params | Response top keys | Errors | Ref |
|---|---|---|---|---|---|
| `GET /world` | short world summary | — | `identity, unemployment, deprived, homeless, mean_hope, mean_knowledge, countries_at_war` | 503 world | `earth1/api/routes/world.py:17` |
| `GET /world/countries` | per-country aggregates, **countries with ≥50 alive only** | — | `identity, countries:[{iso2, alive, unemployment, deprived, hope}]` | 503 world | `earth1/api/routes/world.py:33` |
| `GET /world/earthling/{idx}` | one person, legacy observe view. **`idx` is the SLOT index, not person_id** | `idx:int` path | `identity, earthling:{id, country, age, education, urban, work{…}, money{…}, forces{8}, conviction, self{…}}` (`observe()`, `earth1/observe.py:43-79`; no `connections`/`household_id` — fabric not passed) | 404 "no such earthling" / "this slot is not currently alive"; 503 world | `earth1/api/routes/world.py:54` |
| `GET\|POST /world/tick` | **RETIRED** | — | — | **410** `"evolution via API is retired (0.5e): the daemon earth1-alive.service is the single writer…"` *(captured)* — replacement: the daemon, not any endpoint | `earth1/api/routes/world.py:66` |
| `GET /epochs/current` | live epoch metadata | — | `identity, epoch` (contents of `$EARTH1_ALIVE_HOME/EPOCH.json`, `{}` if unreadable), `policy:"ops/alive/EPOCH_POLICY.md"` | 503 world | `earth1/api/routes/civilization.py:29` |
| `GET /snapshots/current` | the snapshot all surfaces serve | — | `{identity}` only | 503 world | `earth1/api/routes/civilization.py:43` |
| `GET /physics` | physics contract | — | `identity, physics_version, canonical_day, cascade_rules:[{name, conditions:[(force,op,threshold)], effects, cooldown_days, decay_half_life, semantics}], production_modules, step_order` | 503 world | `earth1/api/routes/civilization.py:50`, `earth1/api/readouts.py:479-490` |

### 3.3 Countries / regions / continents / cities / localities

World: daemon; `flows`, `mortality`, `forces/history`, `events` also read
history. All under the `civilization` router (no prefix,
`earth1/api/routes/civilization.py:14`). `iso2` is uppercased by the
handlers.

| Endpoint | Purpose | Params (defaults) | Response top keys | Errors | Ref |
|---|---|---|---|---|---|
| `GET /continents` | 6-continent aggregates | — | `identity, continents:[{name, countries, population_alive, forces_mean{8}\|null}]` | 503 world | `earth1/api/routes/civilization.py:58` |
| `GET /continents/{name}` | one continent, full country views | `name:str` (exact, case-sensitive) | `identity, name, countries:[country_view with regions:null], population_alive` | 404 listing valid names; 503 world | `earth1/api/routes/civilization.py:72` |
| `GET /countries` | all 194 countries (no population threshold — contrast `/world/countries`) | — | `identity, countries:[{iso2, continent, population_alive}]` | 503 world | `earth1/api/routes/civilization.py:84` |
| `GET /countries/{iso2}` | full country view | `iso2:str` | `identity, iso2, name, continent, population_alive, deceased_slots, regions:[{index,code,name,population_share,economic_type,geographic_type}], localities:[int], government:{tax,welfare,policing,legitimacy,at_war_with,war_days,unrest,deprivation_norm}, climate:{baseline_temp,anomaly,soil,farm_share,storm_days,comfort}\|null` + when anyone alive: `forces_mean, unemployment, deprived, homeless, hope, mean_knowledge, wealth_gini`; always `mortality` | 404 "no country X"; 503 world | `earth1/api/routes/civilization.py:93`, `earth1/api/readouts.py:380-406` |
| `GET /countries/{iso2}/regions` | region list only | `iso2` | `identity, iso2, regions` | 404; 503 | `earth1/api/routes/civilization.py:99` |
| `GET /regions/{iso2}/{index}` | one genesis region profile + live pop | `iso2, index:int` | `identity, iso2, index, code, name, population_share_genesis, historical_layers, economic_type, economic_detail, geographic_type, force_deltas, population_alive, localities:[rural_id, urban_id]` | 404 "no such region" (also for unknown iso2 — empty region list); 503 | `earth1/api/routes/civilization.py:106` |
| `GET /countries/{iso2}/localities` | full locality views for the country | `iso2` | `identity, iso2, localities:[locality_view]` | 404; 503 | `earth1/api/routes/civilization.py:122` |
| `GET /countries/{iso2}/flows` | daily flow ledger | `iso2` | `identity, coverage, iso2, series:[{day, alive, unemployment, deprived, hope, fear, wages, subsistence, rent, durables, wealth}]` | **no 404 for bad iso2** — empty `series`; `[]` when no history; 503 world | `earth1/api/routes/civilization.py:129`, `earth1/api/readouts.py:409` |
| `GET /countries/{iso2}/mortality` | deaths now + recorded | `iso2` | `identity, iso2, deceased_slots_now, by_cause_now:{cause:n}` + with history: `deaths_recorded_by_cause, deaths_recorded` | **unknown iso2 → unhandled ValueError → 500** (`codes.index`, `earth1/api/readouts.py:417`); 503 world | `earth1/api/routes/civilization.py:136` |
| `GET /countries/{iso2}/needs` | needs aggregate | `iso2` | `identity, iso2, population_alive, needs_mean:{hunger,thirst,breath,hope,meaning,belonging,satisfaction}\|null, deprived\|null, food_system:{farm_share,soil,temperature_anomaly,storm_days}\|null` | **unknown iso2 → 500** (`.index`, `earth1/api/routes/civilization.py:146`); 503 world | `earth1/api/routes/civilization.py:142` |
| `GET /localities` | every occupied locality | `limit:int=2000` | `identity, count` (total, pre-limit), `localities:[{id, name, population_alive, urban}]` | 503 world | `earth1/api/routes/civilization.py:153` |
| `GET /localities/{loc}` | one locality view | `loc:int` | `identity, id, name, country, continent, region{index,code,name}, urban, is_city, city_name, population_alive, population_deceased_slots, forces_mean\|null, unemployment\|null, deprived\|null, hope\|null, episodes_open:[rule], active_cascade_residues:int` | 404 "no locality N"; 503 | `earth1/api/routes/civilization.py:162`, `earth1/api/readouts.py:347-364` |
| `GET /localities/{loc}/population` | resident person ids | `loc:int, limit:int=1000` | `identity, locality, count` (total alive), `person_ids[:limit], limit` | 503 world (no 404 — unknown loc returns count 0) | `earth1/api/routes/civilization.py:168` |
| `GET /localities/{loc}/forces/history` | daily locality series | `loc:int` | `identity, coverage, locality, series:[{day, pop, forces{8}, eff_identity, episode_identity_collapse, episode_collective_surge, residues}]` | `[]` without history; 503 world | `earth1/api/routes/civilization.py:174`, `earth1/api/readouts.py:372` |
| `GET /localities/{loc}/cascades` | active residues here | `loc:int` | `identity, locality, firings:[cascade item]` | 503 world | `earth1/api/routes/civilization.py:180` |
| `GET /localities/{loc}/events` | person events of current residents + cascades | `loc:int, limit:int=500` | `identity, coverage, locality, person_events:[{day,person_id,kind,detail}] (day DESC), cascades` | 503 world | `earth1/api/routes/civilization.py:186` |
| `GET /cities` | urban localities (odd id) | `limit:int=2000` | `identity, count, definition, cities:[{id, name, country, population_alive}]` | 503 world | `earth1/api/routes/civilization.py:202` |
| `GET /cities/{loc}` | one city (locality view) | `loc:int` | as `/localities/{loc}` | 404 "not a city (rural locality)" for even ids; 404 unknown; 503 | `earth1/api/routes/civilization.py:212` |

### 3.4 Earthlings (all sub-resources)

World: daemon; `*/history`, `status`, `events`, `presence` also read
history. `person_id` is the **permanent** id; `slot` is the reusable array
index. `_slot` resolves person_id → slot and 404s when the person is not in
the current arrays (`earth1/api/routes/civilization.py:17-25`,
`earth1/api/readouts.py:28-33`).

| Endpoint | Purpose | Params (defaults) | Response top keys | Errors | Ref |
|---|---|---|---|---|---|
| `GET /earthlings` | list/search | `country?, locality?:int, alive:bool=true, employed?:bool, min_age?:float, max_age?:float` (age in years, canonical scale 18+72·a), `limit:int=200 (le=5000), offset:int=0` | `identity, total` (all matches), `offset, limit, earthlings:[{person_id, slot, country, age_years, alive}]` | **unknown `country` → 500** (`.index`, line 230); 503 world | `earth1/api/routes/civilization.py:221` |
| `GET /earthlings/{person_id}` | complete dossier; falls back to the history record when the slot was reused | `person_id:int` | live: `identity` + earthling readout (sections: `identity` (person_status), `demographics` (incl. region, locality, age_years, education, income_tier), `traits`(15), `forces`, `work`, `health`, `needs`, `housing`, `social`, `knowledge`, `class`, `presence`, `last_life_event`). Historical: `identity, coverage, person_id, status:"historical", alive:false, note, slot_at_death, died_day, cause_of_death, born_day, parent_id, events, last_force_sample` | 404 when in neither world nor record; 503 world | `earth1/api/routes/civilization.py:242`, `earth1/api/readouts.py:60-97,149-165` |
| `GET /earthlings/slot/{slot}` | dossier by slot (current occupant, alive or deceased) | `slot:int` | `identity` + earthling readout | 404 "no such slot" outside 0..n-1; 503 | `earth1/api/routes/civilization.py:257` |
| `GET /earthlings/{person_id}/status` | alive/deceased + lineage | — | `identity, coverage, person_id, slot, alive, status, cause_of_death, parent_id, generation` + with history: `first_recorded_day, last_recorded_day, slot_previous_occupant_person_id` | 404 (no history fallback); 503 | `earth1/api/routes/civilization.py:265`, `earth1/api/readouts.py:36-50` |
| `GET /earthlings/{person_id}/history` | life events | `kind?:str` filter | `identity, coverage, person_id, events:[{day, slot, kind, detail:dict}]` (day ASC) | 404 only when in neither world nor record; 503 | `earth1/api/routes/civilization.py:271` |
| `GET /earthlings/{person_id}/forces` | stored vs effective forces today | — | `identity, person_id, stored{8}, effective{8}, cascade_overlay_by_rule:{rule:{8}}, memory_press_today{8}, conviction, susceptibility{8}\|null, locality` | 404; 503 | `earth1/api/routes/civilization.py:284`, `earth1/api/readouts.py:100-126` |
| `GET /earthlings/{person_id}/forces/history` | 30-day force samples | — | `identity, coverage, person_id, samples:[{day, forces{8}, conviction}]` | 404; 503 | `earth1/api/routes/civilization.py:290` |
| `GET /earthlings/{person_id}/memories` | standing memories carried | — | `identity, person_id, memories:[memory_view]` | 404; 503 | `earth1/api/routes/civilization.py:297` |
| `GET /earthlings/{person_id}/events` | history + memories + local cascades now | — | `identity, coverage, person_id, history, memories_now, cascades_now` | 404; 503 | `earth1/api/routes/civilization.py:303` |
| `GET /earthlings/{person_id}/relationships` | direct ties | `scope:str="all"` (`"living"` hides deceased alters) | `identity, person_id, scope, ties:[{person_id, slot, type, weight, alive}], partner, household, edge_semantics` | 404; 503 | `earth1/api/routes/civilization.py:312`, `earth1/api/readouts.py:241-254` |
| `GET /earthlings/{person_id}/family` | household/partner/parent/children | — | `identity, person_id, household:{id, members}, partner\|null, parent\|null, children` | 404; 503 | `earth1/api/routes/civilization.py:318` |
| `GET /earthlings/{person_id}/work` | job + money | — | `identity, person_id, occupation, employed, in_labour_force, firm_id\|null, tenure_days, job_losses, money:{wage_daily, wealth_days_of_cost, daily_cost, deprivation, durables, policy_net}` | 404; 503 | `earth1/api/routes/civilization.py:324`, `earth1/api/readouts.py:183-191` |
| `GET /earthlings/{person_id}/work/history` | job events | — | `…events` filtered kinds `hired, lost_job, firm_changed` | 404; 503 | `earth1/api/routes/civilization.py:330` |
| `GET /earthlings/{person_id}/health` | condition now | — | `identity, person_id, alive, condition\|null, diagnosed_day, in_treatment, declining, falls, lifetime_illnesses, cause_of_death\|null, mental, physical, addiction` | 404; 503 | `earth1/api/routes/civilization.py:338`, `earth1/api/readouts.py:205-213` |
| `GET /earthlings/{person_id}/health/history` | illness events | — | `…events` filtered kinds `illness_onset, recovered, died` | 404; 503 | `earth1/api/routes/civilization.py:344` |
| `GET /earthlings/{person_id}/consumption` | today's receipt | — | `identity, person_id, day, income, subsistence, housing, durables, net, savings_days, welfare_transfer, units:"daily cost of living = 1.0"` | 404; 503 | `earth1/api/routes/civilization.py:352`, `earth1/api/readouts.py:194-202` |
| `GET /earthlings/{person_id}/consumption/history` | material trajectory | — | `identity, coverage, person_id, samples` (force samples), `work_events` (kinds `hired, lost_job, firm_changed, homeless, housed, evicted`) | 404; 503 | `earth1/api/routes/civilization.py:358` |
| `GET /earthlings/{person_id}/needs` | needs + country food system | — | `identity, person_id, hunger, thirst, air, deprivation, hope, meaning, belonging, satisfaction, curiosity, country_food_system\|null` | 404; 503 | `earth1/api/routes/civilization.py:367`, `earth1/api/readouts.py:216-223` |
| `GET /earthlings/{person_id}/presence` | where + mobility | — | `identity, coverage, person_id, locality, density, gathering, owns_car, flights_per_year, commute_minutes, trips_taken, moves` (migrated events) | 404; 503 | `earth1/api/routes/civilization.py:373`, `earth1/api/readouts.py:226-233` |

### 3.5 Social graph & households & firms

World: daemon.

| Endpoint | Purpose | Params (defaults) | Response top keys | Errors | Ref |
|---|---|---|---|---|---|
| `GET /social-graph/{person_id}/ego` | BFS ego network | `depth:int=1` (clamped 1..3 internally; **response `depth` echoes the raw request**), `living_only:bool=true` | `identity, person_id, depth, layer_sizes, layers:[[person_id]≤500 each], truncated_at:500` | 404; 503 | `earth1/api/routes/civilization.py:381`, `earth1/api/readouts.py:269-285` |
| `GET /households/{hid}` | household members | `hid:int` | `identity, id, members:[{person_id, slot, alive, age_years}]` | 404 "no such household" when empty; 503 | `earth1/api/routes/civilization.py:387` |
| `GET /firms` | firm list | `country?:str` (iso2; unknown → empty list, no error), `limit:int=500` | `identity, firms:[{id, country, health, employees}]` | 503 world | `earth1/api/routes/civilization.py:457`, `earth1/api/readouts.py:437-448` |
| `GET /firms/{fid}` | one firm | `fid:int` | `identity, id, country, health, employees:int, employee_person_ids[:1000], payroll_daily, mean_tenure_days\|null` | 404 "no firm N"; 503 | `earth1/api/routes/civilization.py:463`, `earth1/api/readouts.py:451-458` |
| `GET /firms/{fid}/employees` | employee ids | `fid:int` | `identity, id, employees:int (count), person_ids` | 404; 503 | `earth1/api/routes/civilization.py:469` |

### 3.6 Memories & cascades

World: daemon; historical lookups read history.

`memory_view` keys (`earth1/api/readouts.py:292-296`): `id, label, day,
origin, salience, half_life_days, rehearsals, force_signature{8}, scope_n`.
Cascade item keys (`earth1/api/readouts.py:313-328`): `firing_index, rule,
locality, locality_name, day, half_life_days, effects{8},
current_level{8}|null`.

| Endpoint | Purpose | Params | Response top keys | Errors | Ref |
|---|---|---|---|---|---|
| `GET /memories` | all standing memories | — | `identity, standing:[memory_view], forgotten_total, total_ever` | 503 world | `earth1/api/routes/civilization.py:400` |
| `GET /memories/{mid}` | one memory, standing or forgotten | `mid:str` | standing: `identity` + memory_view; forgotten (from history): `identity, id, day, label, origin, scope_n, force_signature, status:"forgotten (historical record)"` | 404 "no such memory"; 503 | `earth1/api/routes/civilization.py:407` |
| `GET /memories/{mid}/impacts` | who carries it, what it presses | `mid:str` | `identity, id, carriers, carriers_alive, daily_press_per_carrier{8}, localities:[{id,name,carriers}]×≤25, carrier_person_ids[:1000]` | 404 "no standing memory with that id" (forgotten ones 404 here); 503 | `earth1/api/routes/civilization.py:421`, `earth1/api/readouts.py:299-310` |
| `GET /cascades` | active residues + open episodes | `rule?:str` filter | `identity, active_residues:[cascade item], firings_recorded_all_time:int\|null (null without history), episodes_open:[[rule, locality]]` | 503 world | `earth1/api/routes/civilization.py:430` |
| `GET /cascades/{firing_index}/impacts` | one active firing's receipt | `firing_index:int` (index into the **active** residue list — unstable across days) | `identity` + cascade item + `exposed_alive, exposed_person_ids[:1000], downstream_locality_series:[{day, eff_identity_mean, residues}]` | 404 "no such cascade firing in the active set"; 503 | `earth1/api/routes/civilization.py:439`, `earth1/api/readouts.py:331-344` |
| `GET /cascades/history` | recorded firings | `loc?:int, limit:int=1000` | `identity, coverage, firings:[{id, day, rule, locality, effects, half_life}]` (day DESC); `[]` without history | 503 world | `earth1/api/routes/civilization.py:445` |

### 3.7 Branches (futures as addressable objects)

Router prefix `/branches` (`earth1/api/routes/branches.py:15`); store in
`earth1/api/branches.py`. **Write semantics**: a branch is a **deep clone of
the complete live canonical world** (`clone_world`,
`earth1/api/branches.py:33`) with its own RNG and its own **in-memory**
SQLite history. Advancing a branch runs `alive.live_one_day` on the clone —
**the live world is never touched** (`earth1/api/branches.py:66-74`).
Branches live in process memory only: they do not survive a restart, and the
store is bounded by `EARTH1_API_MAX_BRANCHES` (default **2**,
`earth1/api/branches.py:17`).

**Caveat**: unlike `/forecast/futures`, branch creation has **no population
guard** — `EARTH1_API_MAX_BRANCH_POP` is not consulted here; each branch
costs roughly a whole world of memory.

Branch `meta` shape (`earth1/api/branches.py:57-63`): `id, created_at,
scenario, seed, parent` (live-world identity at fork time),
`branched_at_day, day, days_advanced, alive, physics_version,
history:"in-memory (per branch)"`.

| Endpoint | Purpose | Params / body (defaults) | Response | Errors | Ref |
|---|---|---|---|---|---|
| `GET /branches` | list | — | `{identity, max_branches, branches:[meta]}` | 503 world | `earth1/api/routes/branches.py:40` |
| `POST /branches` | fork the live world, apply scenario on branch day 0 | body `{scenario?: {id:"scenario", label?:str, forces:{force:delta}={}, countries?:[iso2], firm_damage:float=0.0, trade_shock:float=0.0, persists_days:int=30}, seed?:int}` (seed default: time-derived) | `meta` | 429 "branch store full (N); delete one first"; 503 world | `earth1/api/routes/branches.py:46`, `earth1/api/branches.py:26-47` |
| `GET /branches/{bid}` | inspect | `bid:str` (uuid) | `meta` | 404 "no branch X" | `earth1/api/routes/branches.py:55` |
| `DELETE /branches/{bid}` | delete | — | `{deleted: bid}` | 404 | `earth1/api/routes/branches.py:60` |
| `POST /branches/{bid}/advance` | evolve the clone N days (synchronous, in-process — slow for large worlds) | `days:int=1` query, must be 1..365 | `meta` | 400 "days must be 1..365"; 404 | `earth1/api/routes/branches.py:65` |
| `GET /branches/{bid}/compare` | branch vs control | `against?:str` — omitted or `"live"` = the live daemon world; else another branch id | `{branch, control, branch_day, control_day, comparable_persons, delta_forces_mean{8}, delta_forces_abs_mean{8}, frac_persons_moved_gt_0.01, delta_unemployment, delta_wealth_gini, per_country[:50], most_moved_persons[:50]}` | 404 unknown bid/against | `earth1/api/routes/branches.py:73`, `earth1/api/branches.py:86-113` |
| `GET /branches/{bid}/history` | branch-local events | `limit:int=1000` | `{branch:bid, events:[{day, person_id, slot, kind, detail}] (day DESC; **`detail` is a raw JSON string here, not parsed**), cascades:[{day, rule, locality}]}` | 404 | `earth1/api/routes/branches.py:82-87` |

In-branch readouts — same functions as the live surface, answered from the
branch clone and its own recorder; responses carry `branch: meta` instead of
the live `identity` envelope:

| Endpoint | Same shape as | Note | Ref |
|---|---|---|---|
| `GET /branches/{bid}/world` | rich world summary (`readouts.world_summary`) | **`identity` key holds `{"branch": meta}`**, not the live envelope. Keys: `identity, day, population, alive, deceased_slots, persons_ever, unemployment, deprived, homeless, forces_mean, flourishing, knowledge, countries_at_war, countries, localities_occupied, cities, memories_standing, cascade_residues_active, episodes_open, wealth_gini` | `earth1/api/routes/branches.py:95`, `earth1/api/readouts.py:461-476` |
| `GET /branches/{bid}/earthlings/{person_id}` | `/earthlings/{person_id}` (no historical-person fallback; 404 if not in branch arrays) | `branch` + readout | `earth1/api/routes/branches.py:100` |
| `GET /branches/{bid}/earthlings/{person_id}/forces` | `/earthlings/{pid}/forces` | | `earth1/api/routes/branches.py:109` |
| `GET /branches/{bid}/earthlings/{person_id}/history` | `/earthlings/{pid}/history` | coverage starts at branch creation (in-memory recorder) | `earth1/api/routes/branches.py:118` |
| `GET /branches/{bid}/countries/{iso2}` | `/countries/{iso2}` | 404 on unknown iso2 | `earth1/api/routes/branches.py:124` |
| `GET /branches/{bid}/localities/{loc}` | `/localities/{loc}` | | `earth1/api/routes/branches.py:133` |
| `GET /branches/{bid}/localities/{loc}/forces/history` | `/localities/{loc}/forces/history` | | `earth1/api/routes/branches.py:142` |
| `GET /branches/{bid}/cascades` | `active_residues` only | `{branch, active_residues}` | `earth1/api/routes/branches.py:148` |
| `GET /branches/{bid}/memories` | standing list only | `{branch, standing}` | `earth1/api/routes/branches.py:154` |

### 3.8 Forecast

World: daemon + full deep clone per request.

| Endpoint | Purpose | Params (defaults, clamps) | Response | Errors | Ref |
|---|---|---|---|---|---|
| `GET /forecast/futures/{idx}` | one person's distribution over possible lives. **`idx` is the SLOT index, not person_id** | `idx:int` path; `branches:int=24` clamped **4..64**; `days:int=90` clamped **7..365** | `{identity, branches, days, futures:{who (observe view), branches, horizon_days, P_employed_at_end, P_ever_jobless, P_ever_destitute, P_destitute_at_end, P_isolated_at_end, savings_days:{p10,median,p90}, fear:{median,spread_p10_p90}, fear_if_destitute\|null, fear_if_not\|null}}` | 404 "no such living earthling"; **503 `branch_too_large`** when `population > EARTH1_API_MAX_BRANCH_POP` (default 500000); 503 world | `earth1/api/routes/forecast.py:35`, `earth1/observe.py:87-157` |
| `GET /forecast/multiverse` | **PENDING** | — | — | **503** `{"detail":{"error":"living_scenario_surface_pending","detail":"scenario/branch product surfaces land with the Phase-2 domain adapters; the retired engine will not answer in their place","identity":…}}`. Working replacement today: the `/branches` lifecycle (§3.7) | `earth1/api/routes/forecast.py:51-62` |
| `POST /forecast/scenarios` | **PENDING** | — | — | same 503 | `earth1/api/routes/forecast.py:52` |
| `GET /forecast/timeline` | **PENDING** | — | — | same 503 | `earth1/api/routes/forecast.py:53` |
| `GET /forecast/tree` | **PENDING** | — | — | same 503 | `earth1/api/routes/forecast.py:54` |

Cost note: `futures` deep-clones the world once at route level and then
**once per branch** inside `observe.futures` (`earth1/observe.py:106`) —
expect long wall time even under the population cap.

### 3.9 Predictions register

Prefix `/predictions` (`earth1/api/routes/predictions.py:17`). World:
**none** — DB only (`DATABASE_URL` via `earth1.db`). Every route except
`/status` and `/accuracy` returns `503 "Database not configured. Set
DATABASE_URL to enable persistence."` when the DB is off
(`earth1/api/routes/predictions.py:66-71`).

**Governance semantics**: a prediction is *derived from a run* — `create`
copies `question_text`, `predicted_yes_pct` (from the run's `yes_pct`) and
`confidence_regime` from the stored run; the caller cannot supply its own
probability (`earth1/api/routes/predictions.py:143-153`). `arm` freezes it:
sets `prediction_hash = sha256(question|yes_pct|horizon)`, `armed`,
`armed_at`, and refuses re-arming (`earth1/db/store.py:459-477`). `resolve`
records the actual outcome and `error = |actual − predicted|`, flipping
status to `resolved` (`earth1/db/store.py:98-126`). `expire` flips open
predictions past `target_date` to `expired`. Status lifecycle: `open`
(default, `earth1/db/models.py` Prediction.status) → `resolved` | `expired`.

**Honest caveats**: `resolve` does **not** require the prediction to be
armed, and nothing prevents resolving twice (each call adds another outcome
row — `earth1/db/store.py:98-126` has no status guard). `arm` maps *both*
"not found" and "already armed" to **400** (not 404)
(`earth1/api/routes/predictions.py:226-232`).

| Endpoint | Purpose | Params / body (defaults) | Response | Errors | Ref |
|---|---|---|---|---|---|
| `GET /predictions/status` | is persistence on | — | `{enabled: bool}` *(captured: `{"enabled":false}` without DB)* | none | `earth1/api/routes/predictions.py:74` |
| `GET /predictions/runs` | list runs | `run_type?:str, limit:int=50, offset:int=0` | `[{id, created_at, run_type, question_text, yes_pct, dominant, confidence_regime}]` | 503 no DB | `earth1/api/routes/predictions.py:79` |
| `GET /predictions/runs/{run_id}` | full run | `run_id:str` | `{id, created_at, run_type, question_text, binary_question, question_id, country_scope, temporal_context, yes_pct, frac_yes, dominant, conviction, fragility, confidence_regime, confidence_similarity, force_anatomy, parameters, narration, country_splits, predictions:[{id, predicted_yes_pct, horizon_days, target_date, status}]}` | 404 "Run not found"; 503 | `earth1/api/routes/predictions.py:97` |
| `POST /predictions/create` | register a prediction from a run | body `{run_id:str (required), horizon_days:int=90, country_code?:str, tags?:[str]}`; `target_date = now + horizon_days` | `{id, run_id, created_at, question_text, predicted_yes_pct, confidence_regime, country_code, horizon_days, target_date, status:"open", tags}` | 404 "Run not found"; 503 | `earth1/api/routes/predictions.py:136` |
| `GET /predictions/list` | list predictions | `status?:str, limit:int=50, offset:int=0`; ordered by `target_date` asc | `[PredictionSummary]` (same keys as create response) | 503 | `earth1/api/routes/predictions.py:169` |
| `POST /predictions/{prediction_id}/arm` | freeze (hash + timestamp) | — | `{id, armed, armed_at, prediction_hash}` | **400** "…not found" / "…already armed"; 503 | `earth1/api/routes/predictions.py:226` |
| `POST /predictions/{prediction_id}/resolve` | record ground truth | body `{actual_yes_pct:float (required), source:str (required), source_url:str=""}` | `{id, prediction_id, recorded_at, actual_yes_pct, source, error}` | 404 "Prediction … not found"; 503 | `earth1/api/routes/predictions.py:191` |
| `POST /predictions/expire` | expire overdue open predictions | — | `{expired: n}` | 503 | `earth1/api/routes/predictions.py:219` |
| `GET /predictions/accuracy` | resolved-error rollup | `limit:int=100` (last N resolved) | with DB: `{enabled:true, n_resolved, mean_error\|null, by_regime:{regime:{n, mean_error, max_error}}}`; **without DB: 200 `{"enabled": false}`, not 503** | none | `earth1/api/routes/predictions.py:214`, `earth1/db/store.py:171-231` |
| `GET /predictions/atlas` | force-anatomy atlas of resolved outcomes | `dominant_force?:str, min_fragility?:float, limit:int=100` | `[{id, prediction_id, dominant_force, force_signature, fragility_at_prediction, predicted_yes_pct, actual_yes_pct, error, resolved_at\|null}]` | 503 | `earth1/api/routes/predictions.py:241` |

### 3.10 Observatory & snapshots & physics

World: daemon. (`/snapshots/current` and `/physics` are listed in §3.2 with
the epoch endpoints.)

| Endpoint | Purpose | Response | Errors | Ref |
|---|---|---|---|---|
| `GET /observatory/standing-readings` | standing civilization gauges | `{identity, entropy, wealth_gini, mean_conviction, mental_ill` (share with mental < 0.3)`, isolated` (share with relationship < 0.25)`, memories_standing}` | 503 world | `earth1/api/routes/observatory.py:12` |

### 3.11 Billing

Prefix `/billing` (`earth1/api/routes/billing.py:12`). World: none.

Tier table (`earth1/api/billing.py:8-12`), *(captured)*:

| tier | price (USD/mo) | daily_cap | rate_limit |
|---|---|---|---|
| free | 0 | 100 | 30 |
| pro | 99 | 10000 | 300 |
| enterprise | 499 | 100000 | 1000 |

(`daily_cap`/`rate_limit` are stored on the key; see §2 caveats 1–2 on what
is actually enforced.)

| Endpoint | Purpose | Params / body | Response | Auth layer | Errors | Ref |
|---|---|---|---|---|---|---|
| `GET /billing/tiers` | tier catalogue | — | `{tier: {price, daily_cap, rate_limit}}` *(captured)* | Layer 1 only | none | `earth1/api/routes/billing.py:22` |
| `POST /billing/checkout` | Stripe subscription checkout | body `{tier:str (required), customer_email:str (required), success_url?:str (default https://earth1.dev/billing/success), cancel_url?:str (default …/cancel)}` | `{checkout_url}` | Layer 1 only | 400 unknown tier / `"Free tier does not require checkout"` / no `STRIPE_PRICE_{TIER}` configured; 503 stripe pkg missing or `STRIPE_SECRET_KEY` unset | `earth1/api/routes/billing.py:30`, `earth1/api/billing.py:36-59` |
| `POST /billing/webhook` | Stripe webhook — **signed-only** | raw body + `Stripe-Signature` header | handler result: `{action:"upgrade", customer_email, tier}` \| `{action:"subscription_change", status, subscription_id, customer_email}` \| `{action:"ignored", event_type}` | Stripe signature (`STRIPE_WEBHOOK_SECRET`); **no secret configured → request refused** (hardened 2026-09-08, `earth1/api/billing.py:62-71`). See §2 caveat 3: Layer 1 also applies when auth is on | 400 `"Webhook error: …"` on any verification/parse failure | `earth1/api/routes/billing.py:46` |
| `GET /billing/usage` | **authenticated + self-scoped** usage | header `X-API-Key` (or the middleware-attached key when Layer 1 is on) | `{api_key_id, owner, tier, daily_cap, daily_usage:{requests, tokens, compute_ms}}` — answers **for the caller's key only** (fixed from the prior leak of every key, `earth1/api/routes/billing.py:84-96`) | route-level X-API-Key check even when Layer 1 is off | 401 "X-API-Key header required"; 403 invalid/inactive; 503 "Database not configured" *(captured)* / "Database not available" | `earth1/api/routes/billing.py:73` |

Webhook side effects (`earth1/api/routes/billing.py:56-68`):
`checkout.session.completed` upgrades the active key whose `owner` equals
`customer_email`; `customer.subscription.deleted/updated` with status
`canceled`/`unpaid` drops that owner's key to `free`
(`earth1/api/billing.py:101-118`). No DB → side effects skipped, result
still returned.

### 3.12 Retired / pending endpoints (contract by refusal)

| Endpoint(s) | Status code + body | Replacement pointer | Ref |
|---|---|---|---|
| `GET\|POST /ask`, `POST /ask/segment`, `POST /ask/freetext`, `POST /ask/mind` | **503** `{"detail":{"error":"living_calibration_pending","detail":"the living answer path requires per-question calibration (Benchmark A, Phase 1)…","identity":…}}` | Benchmark A / Phase 1 calibration; no serving alternative — the retired engine will not answer in its place | `earth1/api/routes/ask.py:25-41` |
| `GET /forecast/multiverse`, `POST /forecast/scenarios`, `GET /forecast/timeline`, `GET /forecast/tree` | **503** `{"detail":{"error":"living_scenario_surface_pending",…,"identity":…}}` | Phase-2 domain adapters; interim: `/branches` lifecycle | `earth1/api/routes/forecast.py:51-62` |
| `GET\|POST /world/tick` | **410** `{"detail":"evolution via API is retired (0.5e): the daemon earth1-alive.service is the single writer…"}` *(captured)* | the daemon `earth1-alive.service` — permanent, no endpoint replaces it | `earth1/api/routes/world.py:66-72` |

Note the precedence *(captured)*: the `/ask` and pending-forecast handlers
call `get_world()` first, so when the canonical snapshot is unavailable they
return the app-level `503 canonical_world_unavailable` **instead of** their
own pending-503. The pending body (with `identity`) only appears when the
world is resolvable. Also retired and **not mounted at all** (plain 404):
the `lab`, `loop` and `receiver` routers (`earth1/api/main.py:9-11`).

---

## 4. Support-status table

| Group | Endpoints | Status | Notes |
|---|---|---|---|
| App-level (`/health`, `/civ`) | 2 | **LIVE** (read-only) | `/health` bypasses all middleware |
| World & epochs (`/world`, `/world/countries`, `/world/earthling/{idx}`, `/epochs/current`, `/snapshots/current`, `/physics`) | 6 | **LIVE / READ-ONLY** | daemon is the single writer |
| Countries / regions / continents / cities / localities | 18 | **LIVE / READ-ONLY** | history-backed sub-routes degrade honestly via `coverage` |
| Earthlings + sub-resources | 19 | **LIVE / READ-ONLY** | person_id permanent; slot reusable |
| Social graph & households & firms | 5 | **LIVE / READ-ONLY** | |
| Memories & cascades | 6 | **LIVE / READ-ONLY** | cascade `firing_index` unstable across days |
| Observatory (`/observatory/standing-readings`) | 1 | **LIVE / READ-ONLY** | |
| Branches | 14 | **LIVE** (writes confined to in-process clones) | ephemeral, max 2 by default, never touches the live world |
| Forecast `/forecast/futures/{idx}` | 1 | **LIVE** (population-capped) | 503 `branch_too_large` above `EARTH1_API_MAX_BRANCH_POP` |
| Forecast legacy (`multiverse`, `scenarios`, `timeline`, `tree`) | 4 | **PENDING-503** | Phase-2 domain adapters |
| Predictions register | 10 | **LIVE** (requires `DATABASE_URL`) | 503 without DB (except `/status`, `/accuracy`) |
| Billing | 4 | **LIVE** (requires Stripe env + DB for effects) | usage metering currently records nothing (§2 caveat 1) |
| `/ask` family | 4 | **RETIRED-503** (calibration pending) | Benchmark A, Phase 1 |
| `/world/tick` | 1 | **RETIRED-410** (permanent) | daemon-only evolution |

Total: 95 non-`/v1` paths (of 108 in `docs/openapi.json`), less the 13
`/v1/*` paths documented separately.
