# Earth-1 API — endpoint inventory (API-COMPLETE-1, 2026-08-23)

Every response from a live surface carries `identity` (epoch, world_uuid, snapshot sha256, physics_version, world_day). The same readouts serve `/branches/{id}/…`, so a query means the same thing inside a future.

Interactive docs: `GET /docs` · machine schema: `GET /openapi.json`.

| method | path | summary |
|---|---|---|
| GET | `/ask` | Ask Pending |
| POST | `/ask` | Ask Pending |
| POST | `/ask/freetext` | Ask Variants Pending |
| POST | `/ask/mind` | Ask Variants Pending |
| POST | `/ask/segment` | Ask Variants Pending |
| POST | `/billing/checkout` | Checkout |
| GET | `/billing/tiers` | List Tiers |
| GET | `/billing/usage` | Usage |
| POST | `/billing/webhook` | Webhook |
| GET | `/branches` | List Branches |
| POST | `/branches` | Create Branch |
| GET | `/branches/{bid}` | Inspect |
| DELETE | `/branches/{bid}` | Delete |
| POST | `/branches/{bid}/advance` | Advance |
| GET | `/branches/{bid}/cascades` | B Cascades |
| GET | `/branches/{bid}/compare` | Compare |
| GET | `/branches/{bid}/countries/{iso2}` | B Country |
| GET | `/branches/{bid}/earthlings/{person_id}` | B Earthling |
| GET | `/branches/{bid}/earthlings/{person_id}/forces` | B Forces |
| GET | `/branches/{bid}/earthlings/{person_id}/history` | B History |
| GET | `/branches/{bid}/history` | History |
| GET | `/branches/{bid}/localities/{loc}` | B Locality |
| GET | `/branches/{bid}/localities/{loc}/forces/history` | B Locality History |
| GET | `/branches/{bid}/memories` | B Memories |
| GET | `/branches/{bid}/world` | B World |
| GET | `/cascades` | Cascades |
| GET | `/cascades/history` | Cascade History |
| GET | `/cascades/{firing_index}/impacts` | Cascade Impacts |
| GET | `/cities` | Cities |
| GET | `/cities/{loc}` | City |
| GET | `/civ` | Civ Stats |
| GET | `/continents` | Continents |
| GET | `/continents/{name}` | Continent |
| GET | `/countries` | Countries List |
| GET | `/countries/{iso2}` | Country |
| GET | `/countries/{iso2}/flows` | Country Flows |
| GET | `/countries/{iso2}/localities` | Country Localities |
| GET | `/countries/{iso2}/mortality` | Country Mortality |
| GET | `/countries/{iso2}/needs` | Country Needs |
| GET | `/countries/{iso2}/regions` | Country Regions |
| GET | `/earthlings` | Earthlings |
| GET | `/earthlings/slot/{slot}` | Earthling By Slot |
| GET | `/earthlings/{person_id}` | Earthling |
| GET | `/earthlings/{person_id}/consumption` | Earthling Consumption |
| GET | `/earthlings/{person_id}/consumption/history` | Earthling Consumption History |
| GET | `/earthlings/{person_id}/events` | Earthling Events |
| GET | `/earthlings/{person_id}/family` | Earthling Family |
| GET | `/earthlings/{person_id}/forces` | Earthling Forces |
| GET | `/earthlings/{person_id}/forces/history` | Earthling Force History |
| GET | `/earthlings/{person_id}/health` | Earthling Health |
| GET | `/earthlings/{person_id}/health/history` | Earthling Health History |
| GET | `/earthlings/{person_id}/history` | Earthling History |
| GET | `/earthlings/{person_id}/memories` | Earthling Memories |
| GET | `/earthlings/{person_id}/needs` | Earthling Needs |
| GET | `/earthlings/{person_id}/presence` | Earthling Presence |
| GET | `/earthlings/{person_id}/relationships` | Earthling Relationships |
| GET | `/earthlings/{person_id}/status` | Earthling Status |
| GET | `/earthlings/{person_id}/work` | Earthling Work |
| GET | `/earthlings/{person_id}/work/history` | Earthling Work History |
| GET | `/epochs/current` | Epoch Current |
| GET | `/firms` | Firms |
| GET | `/firms/{fid}` | Firm |
| GET | `/firms/{fid}/employees` | Firm Employees |
| GET | `/forecast/futures/{idx}` | Futures |
| GET | `/forecast/multiverse` | Legacy Forecast Pending |
| POST | `/forecast/scenarios` | Legacy Forecast Pending |
| GET | `/forecast/timeline` | Legacy Forecast Pending |
| GET | `/forecast/tree` | Legacy Forecast Pending |
| GET | `/health` | Health |
| GET | `/households/{hid}` | Household |
| GET | `/localities` | Localities |
| GET | `/localities/{loc}` | Locality |
| GET | `/localities/{loc}/cascades` | Locality Cascades |
| GET | `/localities/{loc}/events` | Locality Events |
| GET | `/localities/{loc}/forces/history` | Locality Force History |
| GET | `/localities/{loc}/population` | Locality Population |
| GET | `/memories` | Memories |
| GET | `/memories/{mid}` | Memory |
| GET | `/memories/{mid}/impacts` | Memory Impacts |
| GET | `/observatory/standing-readings` | Standing Readings |
| GET | `/physics` | Physics |
| GET | `/predictions/accuracy` | Accuracy |
| GET | `/predictions/atlas` | Atlas |
| POST | `/predictions/create` | Create Prediction |
| POST | `/predictions/expire` | Expire |
| GET | `/predictions/list` | List Preds |
| GET | `/predictions/runs` | Runs |
| GET | `/predictions/runs/{run_id}` | Run Detail |
| GET | `/predictions/status` | Status |
| POST | `/predictions/{prediction_id}/arm` | Arm |
| POST | `/predictions/{prediction_id}/resolve` | Resolve |
| GET | `/regions/{iso2}/{index}` | Region |
| GET | `/snapshots/current` | Snapshot Current |
| GET | `/social-graph/{person_id}/ego` | Social Graph Ego |
| GET | `/world` | World Summary |
| GET | `/world/countries` | Countries |
| GET | `/world/earthling/{idx}` | Earthling |
| GET | `/world/tick` | Tick Retired |
| POST | `/world/tick` | Tick Retired |

## Entity model

- **Earthling** — addressed by stable `person_id` (never reused; a rebirth draws a new id, `parent_id` links lineage); `slot` is the array index and IS reused. Deceased Earthlings remain addressable (status, cause of death, final state, history).
- **Geography** — continent (static UN-style table) → country (ISO2) → region (genesis profile) → locality (`country*1000+region*2+urban`) ; a **city** is the urban locality of a region.
- **Forces** — stored (the evolving state), effective (stored + cascade overlay), overlay by rule, memory press, conviction, susceptibility; history = monthly per-person samples + daily locality means.
- **History** — `history.sqlite` beside the snapshot: person events (born/died/hired/lost_job/firm_changed/illness_onset/recovered/migrated/homeless/housed/evicted/widowed/life), force samples, locality daily, country daily flow ledger, cascades, memories.
- **Events** — memories (chronicle) with impacts (carriers, daily press, localities); cascade firings with impacts (exposed persons, downstream locality series).
- **Social graph** — typed ties with weights and person ids (household, colleagues, neighbours, friends, weak, diaspora, media); `scope=living` shows the view the dynamics use; household/family/partner/children.
- **Branches** — create (complete clone + scenario), advance, compare (vs live or another branch), delete; every entity queryable inside.

## Known limits (honest)

- Branches live in the API process memory (EARTH1_API_MAX_BRANCHES, default 2); at 4M agents each clone is ~10 GB.
- Force history is sampled every 30 days per person (daily at locality level).
- Partnership is a genesis condition dissolved by death; formation over time is not modelled.
- History starts when the recorder starts (epochs born before API-COMPLETE-1 have none until redeployed).
