# Earth-1 API Reference — integration guide for external apps

_Generated against the live code at this commit. Three artifacts travel
together and supersede older API notes:_

| artifact | purpose |
|---|---|
| `docs/openapi.json` | machine-readable schema, dumped from the mounted app (108 paths) — import into Postman / client codegen |
| `docs/API_REFERENCE.md` | this file: auth, envelopes, the v1 ship surface in full, semantics, errors |
| `docs/API_LEGACY_SURFACE.md` | the ~90 legacy/live-world read routes, grouped, with per-route params and status |
| `docs/api_examples.json` | golden request/response pairs captured in-process against a real (tiny) world |

Base URL: the serving host, default port 8100 (`uvicorn earth1.api.main:app`).
Interactive docs are served at `/docs` (Swagger) and `/redoc`.

---

## 1. Authentication — two layers, know both

**Layer A — app-wide `X-API-Key` middleware** (`earth1/api/auth.py`).
Active only when `EARTH1_AUTH_REQUIRED` is set on the server. DB-backed
keys with tiers and daily caps (`/billing/tiers`); budget middleware
returns `429 daily_cap_exceeded` past the cap. When inactive, this layer
passes requests through.

**Layer B — `/v1` Bearer allowlist** (`earth1/api/v1.py:_auth`).
Header: `Authorization: Bearer <token>` where the token is listed in the
server's `EARTH1_API_KEYS` (comma-separated). **Fail-closed**: if the
allowlist is empty, every v1 call returns `503 no API keys configured`
unless the server explicitly sets `EARTH1_DEV_OPEN=1` (anonymous dev
mode). Per-token rate limit: `EARTH1_API_RPM` requests/minute (default
30) → `429 rate limit`. Errors: `401` missing/malformed header, `403`
unknown token.

When **both** layers are enabled the caller needs both headers. The
identity used for v1 model ownership and audit logs is
`sha256(token)[:12]` — raw tokens are never stored.

## 2. The v1 envelope

Every `/v1` response wraps its payload with:

```json
{
  "epoch": "3-lab",
  "freeze_tag": "freeze-0.9",
  "tree_hash": "<git short-sha of the serving tree>",
  "fidelity": "20k",
  "ledger_cutoff_day": 123.0,
  ...payload
}
```

`freeze_tag` is **derived from the physics configuration stamp at
runtime**, never hardcoded: a process whose loaded physics does not
match the frozen configuration serves `unfrozen-dev:<n-mismatches>` and
`/v1/health` reports `physics_stamp: "degraded"` with the mismatch
list. An integrating app SHOULD refuse to present numbers from a
degraded envelope as comparable to published boards.

`fidelity` ∈ {`20k`, `200k`}: which lab snapshot served the request.
Branch runs execute on deep copies; the serving snapshots and the
canonical worlds are never mutated by requests.

## 3. The v1 ship surface (13 endpoints)

### 3.1 `POST /v1/ask` — one door for any question

Request body:

| field | type | default | notes |
|---|---|---|---|
| `text` | string | required | the question, natural language |
| `question_id` | string | auto `api:<10hex>` | idempotency/reference id |
| `class` | string | auto-classified | registered question class |
| `outcomes` | string[] | binary YES/NO | ≥3 entries → softmax multi-outcome |
| `country` | ISO-2 | null | scopes the question |
| `fidelity` | `20k`\|`200k` | `20k` | `200k` is async (below) |
| `p_market` | number | null | display-only; never blended |
| `horizon_days` | int | 45 sync / 60 async | clamped to [1, 365] |

**Synchronous (`20k`)** → envelope + `payload` from the grounding-first
router. Always includes a deterministic `answer` sentence and a `tier`:

- `FACT` — resolved by live grounding (astronomy, price thresholds,
  Wikipedia-checkable facts); `p` is 0.999/0.0001 style.
- `GROUNDED` — grounded context, no simulation claim (`p: null`).
- Simulation tiers (from the multiverse adapter): `CALIBRATED` /
  `UNCALIBRATED` / `ABSTAIN` / `KNOWN-DEFECT`, with for binary
  questions: `p_model`, `distances`, `branch_hashes`, and — per the
  2026-09-08 semantics ruling — `"semantics": "branch_consistency"` +
  `semantics_note`: the number is a normalized branch-displacement
  ratio, **not a calibrated event probability**. Multi-outcome payloads
  carry `p_by_outcome`.
- Impossibility guard: predicted >30% national-scale change within 31
  days without a named mechanism → structured abstention.

Every ask is appended to a hash-chained question log (`/v1/health`
exposes the chain head).

**Asynchronous (`200k`)** → `{job_id, status:"queued"}` immediately.
Concurrency is bounded (`429 job queue full` beyond `EARTH1_MAX_JOBS`,
default 2).

### 3.2 `GET /v1/jobs/{jid}`

Async result retrieval: `{job_id, status: queued|done|error, payload?}`.
Jobs are process-local, TTL-evicted (`EARTH1_JOB_TTL`, default 3600 s)
→ `404` after expiry or restart; the 404 message says so.

### 3.3 `POST /v1/consequences` — structured consequence report

Body: `question_id`/`text` (scenario), `country?`,
`horizon_days` (clamp [1,365]), `seeds` (clamp [8,16] — 8 is the
registered statistical floor). Response payload (`report`):

- `order0` — the question and scenario echo.
- `order1..order4` — lines of `{observable, unit, tier, value, sem,
  requested_day, measured_day, note?}`. Units carry the day actually
  measured; substituted horizons are labelled, never silently relabelled.
  Mortality rows report `deaths_cumulative` (identity-aware DeathWatch)
  beside `dead_slots_now` (a stock, labelled as such). SEM is
  std/√n.
- `order2_geography` — per-country deltas in **people** (world-scaled;
  `people_per_agent` included for reconciliation) with `basis`.
- Any line the physics cannot support is `tier: "ABSTAIN"` with the
  register's named missing channel — never a number.

### 3.4 `GET /v1/forecast/{qid}`

Displays a registered forecast: `{question, class, p_model, abstain,
abstain_reason?, market_first_seen_display_only, resolution_date?,
resolution?, status: open|abstained|resolved, tag, line_sha256}`.
Read-only display of the hash-chained register; `404` unknown id.

### 3.5 `GET /v1/world/state`

Per-country live view: `{countries: [{country, centroid, adm1: null,
forces: {fear..temperament: float}, conviction_index, agents}],
note_adm1}`. Countries with <30 live agents are omitted.

### 3.6 `GET /v1/world/hash`

The reproducibility claim, exercisable: `{world_hash, day,
config_stamp, note}`. An identical (seed, day, config) reconstruction
must reproduce `world_hash` exactly; a different hash falsifies the
determinism claim. `config_stamp` is the full physics stamp (env +
loaded state + mismatch lists).

### 3.7 `GET /v1/world/history`

Live cascade-episode window: `{cascade_episodes_active: [{rule, day,
loc}], note}` (date-range history pending the recorder store — the
note says so).

### 3.8 `GET /v1/world/events`

The observation-only hash-chained event wire: `?since_day&n` (n ≤ 1000)
→ `{events, count, wire: open|closed, chain_head}`. Each event carries
`_prev`/`_hash`; an app can verify the chain client-side.

### 3.9 `GET /v1/capabilities`

Feature discovery: supported operations, fidelities present,
`freezeTag` (derived), calibration table, and the population-frame
contract version. Poll this before feature-gating UI.

### 3.10 `GET /v1/health`

`{calibration_table: {class: CALIBRATED|UNCALIBRATED}, physics_stamp:
ok|degraded, physics_stamp_mismatch?, question_log_head,
question_log_dropped, fidelities: {20k: bool, 200k: bool}}`.
Binary-class tiers key on `binary_calibrated` (the marker the binary
path actually consumes); softmax tiers on `temperature_fitted`.

### 3.11 `POST /v1/models` — create a custom population model

Body: `{model_id, description?, context?, population?}`.
`model_id` must match `[A-Za-z0-9][A-Za-z0-9_-]{0,63}` (`422`
otherwise — this blocks path traversal). `409` if the id exists under
another key; ownership is the hashed principal. Response: the model
meta (`calibration_tier` starts `UNCALIBRATED`; context attributes are
marked synthetic).

### 3.12 `POST /v1/models/{model_id}/scenario`

Runs a scenario on the caller's model: `404` unknown, `403` another
tenant's. Body: scenario fields + `fidelity`, `seeds` [1,16],
`horizon_days` [1,365]. Response: `{result}` with the same
consequence-line schema as 3.3. With `seeds=1` every `sem` is `null`
(a single-seed standard error is undefined); send `seeds>=2` for
numeric sems.

### 3.13 `POST /v1/models/{ref}/population-frame`

Maps owner-vocabulary cohorts onto the census joint. Body:
`{cohorts: [{id, name, description?}], country?, tier_size?}`.
Response: `{allocation: [{cohortId, weight, provenance:
survey_measured|tier_fallback, surveyMeasuredShare, peopleRepresented,
agentsAtTier, cellsMatched, cellsTotal, constraints,
matchedVocabulary, contradictoryAxes, unmatched, note?}],
peoplePerAgent, effectiveN, scopePopulation, scope, limitations,
frameProvenance}`. Contradictory vocabulary yields weight 0 (never the
whole population); unmatched vocabulary is flagged, not guessed.

## 4. Error model (v1)

| code | meaning |
|---|---|
| 401 | bearer header missing/malformed |
| 403 | unknown token · sealed data-role path (fail-closed guard) · another tenant's model |
| 404 | unknown forecast id · unknown job (incl. TTL/restart) · unknown model |
| 409 | model id already exists |
| 422 | invalid model id · non-integer clamped field |
| 429 | rate limit (per-token RPM) · job queue full · daily cap (layer A) |
| 503 | no API keys configured (and no `EARTH1_DEV_OPEN`) · missing fidelity snapshot · data-role registry unreadable |

## 5. Integration quickstart

```bash
# capabilities + health
curl -s -H "Authorization: Bearer $KEY" http://HOST:8100/v1/capabilities
# ask (sync)
curl -s -X POST -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"text":"Will unemployment in Spain rise this quarter?","country":"ES"}' \
  http://HOST:8100/v1/ask
# custom model + cohort frame
curl -s -X POST -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model_id":"acme_launch","description":"EU luxury buyers"}' \
  http://HOST:8100/v1/models
curl -s -X POST -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"cohorts":[{"id":"c1","name":"affluent urban women"}]}' \
  http://HOST:8100/v1/models/acme_launch/population-frame
```

Client rules of thumb: treat `tier` as load-bearing (never display an
`ABSTAIN` line's absence of a number as zero); show `p_model` with its
`semantics_note`; check `freeze_tag`/`physics_stamp` before comparing
numbers across sessions; verify the event-wire chain if you archive it.

## 6. Legacy surface

The ~90 non-`/v1` routes (world/countries/earthlings/branches/
cascades/memories/firms/predictions/observatory/billing) are read-only
views over the daemon's persisted world plus the prediction register
and billing. Full per-route documentation: `docs/API_LEGACY_SURFACE.md`.
Note the deliberate refusals: the legacy `/ask` family returns `503`
pointing to `/v1/ask`; `/world/tick` is retired (the world is advanced
by its daemon, never by API callers).

## 7. Known integration caveats (found while documenting — fixes queued)

1. Unknown ISO-2 on `/countries/{iso2}/mortality`, `/needs`, and
   `/earthlings?country=` returns `500`, not `404` — validate country
   codes client-side against `/countries`.
2. With app-wide auth enabled, `/billing/webhook` currently requires an
   X-API-Key before signature verification (Stripe cannot send one) —
   webhook integration needs the exemption fix first.
3. Usage metering records nothing yet (daily caps never trip;
   `/billing/usage` reports zero) and per-key rate limits are stored but
   unenforced — the effective limiter is per-IP + the v1 per-token RPM.
4. `POST /branches` deep-clones the full serving world per branch
   (max 2 branches); budget memory accordingly.
5. `POST /predictions/{id}/resolve` permits double-resolution; treat
   resolution as idempotent on the client.

(Resolved 2026-09-08: `POST /v1/models/{id}/scenario` no longer 500s on
`seeds=1` — `sem` is served as `null` for single-seed runs; see 3.12.
Regression test: `tests/test_model_scenario_seeds.py`.)
