# API-COMPLETE-1 — IMPLEMENTATION REPORT (main, 2026-08-23)

Objective: make Earth-1 an API-addressable civilization. Input:
EARTH1_API_COMPLETENESS_AUDIT.md (78 state families: 9 direct / 19
indirect / 37 internal / 13 not implemented). Gap matrix:
`data/api_completeness/api_gap_matrix.json` (39 items: 20 existing-
internal, 10 derivable, 9 not-modeled). Endpoint inventory:
`data/api_completeness/endpoint_inventory.json`; docs: `docs/API.md`;
OpenAPI at `/openapi.json` and `/docs`.

## What was built

New first-class state (state only — dynamics proven bit-identical:
forces/alpha/alive/wealth/employment/traits hash f347329a… equal before
and after; world-hash pin re-pinned with that justification):
- `civ.person_id`, `civ.parent_id`, `civ.person_counter` — stable
  person identity; rebirth draws a fresh id (never reused), lineage kept.
- `life.partner` — romantic partnership edge (genesis pairing inside a
  household; widowed at death; newborns single; formation over time not
  modelled — stated in the API).
- `earth1/geography.py` — continent table (194 ISO2), city = urban
  locality of a region, locality naming/keys.
- `earth1/history.py` — the append-only record (SQLite beside the
  snapshot; in-memory per branch): person events (13 kinds), monthly
  force samples per person, daily locality means + episode flags +
  residues, daily country flow ledger (wages/subsistence/rent/durables/
  wealth), cascades, memories. Hooked into the daemon after every tick;
  never read by the dynamics.
- `persistence.fill_identity_fields` — older snapshots load with
  derived ids (slot) and partners; reported in `info["filled"]`.

New API (67 routes in the new families; 99 total):
- `earth1/api/readouts.py` — every answer as a function of (world,
  history) so live and branch queries are the same code.
- `/epochs/current`, `/snapshots/current`, `/physics`
- `/continents[/…]`, `/countries[/{iso2}[/regions|localities|flows|mortality|needs]]`,
  `/regions/{iso2}/{i}`, `/localities[/{id}[/population|forces/history|cascades|events]]`,
  `/cities[/{id}]`
- `/earthlings` (search: country, locality, alive, employed, age),
  `/earthlings/{id}` (+ `/status /history /forces /forces/history
  /memories /events /relationships?scope= /family /work /work/history
  /health /health/history /consumption /consumption/history /needs
  /presence`), `/earthlings/slot/{idx}`, `/social-graph/{id}/ego`,
  `/households/{id}`
- `/memories[/{id}[/impacts]]`, `/cascades`, `/cascades/history`,
  `/cascades/{i}/impacts` (exposed persons + downstream locality series)
- `/firms[/{id}[/employees]]`
- `/branches` POST/GET, `/branches/{id}` GET/DELETE, `…/advance`,
  `…/compare?against=`, `…/history`, and inside-branch queries
  `…/world …/earthlings/{id}[/forces|/history] …/countries/{iso2}
  …/localities/{loc}[/forces/history] …/cascades …/memories`.
- Deceased Earthlings are addressable (status, cause, final state,
  history); the living-only vs historical edge semantics are explicit.

Tests: `tests/test_api_complete.py` (7: identity/physics, geography,
earthling surfaces, memories/cascades/firms, stable id across rebirth,
branches end-to-end incl. live world untouched, OpenAPI lists every
route); estate 1,105 passed / 6 skipped. Gates: release gate eligible;
ONE_EARTH_CODE_PATH PASS (no legacy imports on any official surface).

## Coverage after (data/api_completeness/coverage_after.json)

| class | before | after |
|---|---|---|
| DIRECT_API | 9 (11.5%) | **73 (93.6%)** |
| INDIRECT_API | 19 | 1 (tie formation/dissolution — totals only) |
| INTERNAL_ONLY | 37 | 4 (perishability readout; `/ask` equations — 503 by ruling until calibration; timeline/scrub and assimilation — Bible items, store not built) |
| NOT_IMPLEMENTED | 13 | 0 |

Acceptance criteria: (1) every audit item implemented as live endpoint
or state+endpoint — YES except the four listed, which are governed by
other rulings (calibration, timeline); (2) stable Earthling ID — YES;
(3) branch lifecycle fully queryable — YES; (4) city + continent — YES;
(5) force history — YES; (6) event/memory/cascade history — YES;
(7) no legacy imports — YES (gate); (8) OpenAPI/docs — YES; (9) tests —
YES; (10) this report.

## Deployment note
`main` now carries physics `0.8-candidate-v4/posthumous-invariant`
plus these state fields. The live Epoch 2 runs v3 from commit 69ee9d0;
by EPOCH_POLICY deploying main = Epoch 3 (founder ruling required).
Until then the live API on CCX33 serves the v3 world through the new
routes only after redeploy; history for Epoch 2 starts when the recorder
is deployed. Branch memory on CCX33 (30 GB): 1 branch at 4M.
