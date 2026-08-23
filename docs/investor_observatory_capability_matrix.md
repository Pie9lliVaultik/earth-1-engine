# Earth-1 Investor Observatory — capability matrix

Audit date 2026-08-21, commit at build time. Classification:
A = already computable · B = physics exists, read-only
instrumentation added · C = needs a Bible-specified domain adapter
(shown as limitation in UI) · D = scientifically unsupported today.

## World / identity

| feature | class | route |
|---|---|---|
| world day, population, alive, countries, seed, commit | A | `/api/identity` (canonical `World` via `birth_world`/`live_one_day`) |
| canonical 4M production world served locally | C | production is read-only on its box; local runs a DEMO-SCALE world born through the same engine, labeled as such in the UI header |
| force field means (8 channels) | A | `/api/identity` |
| standing memories count | A | chronicle |

## Live pulse (all REAL diffs of engine state, tick = one live_one_day)

| feature | class | notes |
|---|---|---|
| employment transitions | B | day-over-day diff of `life.employed` (read-only instrumentation) |
| firm health-state changes | B | diff of `firm_health < 0.4` |
| deprivation-line crossings | B | diff of `deprivation > 0.5` |
| wealth-reserve transitions | B | diff of `wealth < 5 days` |
| deaths / births | A | `health.alive` diff, tick stats |
| memory creation/decay, spread | A | chronicle count + `memory_spread` |
| threshold cascades fired | A | `cascades_fired` (instrumented in 0.8) |
| force-field daily movement | A | mean force diff |
| per-encounter social feed | C | dyadic encounter objects exist only in the experimental 0.8 lab (flag-gated OFF here); incumbent propagate has no per-encounter log |

## News → WorldEvent

| feature | class | notes |
|---|---|---|
| live headline ingestion | B | Google News RSS via stdlib; NO canned headlines; failure shown honestly |
| historical daily real-news feed | A | `timeline.py` DailySignals (2015 cold-start corpus; not today's news) |
| ranking / category / force-signature adapter | B | editorial layer, explicitly labeled separate from simulation |
| full per-headline LLM structuring | C | no LLM is wired into the local server; adapter is deterministic and labeled |
| statuses READY / PARTIAL / INSUFFICIENT | A | per-category adapter table; energy prices, central banks, tech launches marked INSUFFICIENT CAUSAL ADAPTER |

## Branching (the product)

| feature | class | notes |
|---|---|---|
| paired control/scenario, common dice, multiple pairs | A | `branch.Scenario`/`apply` + `live_one_day`; demo 2 pairs × 30d |
| outcome diffs: employment, deprivation, FEAR, firm health, alive | A | affected-cohort means, pair spread shown as uncertainty |
| 90d / 365d horizons | C | scientifically runnable but not within demo latency; marked on scrubber |
| oil price / inflation | C/D | missing energy-shipping-price adapters (Bible: Hormuz not benchmark-grade) — shown as NOT YET COMPUTABLE |
| migration per-event | C | no event-conditional migration adapter |
| opinion readout in-branch | B* | observer machinery exists; not wired into demo horizon — labeled |
| WHY causal graph | B | shown as MODEL ARCHITECTURE (executable pathway); per-write causal receipts NOT YET INSTRUMENTED — labeled, not faked |
| WHO cohort decomposition | A* | affected-country cohort implemented; income/age/sector splits computable, not yet in UI |
| WHERE geographic map | C | country-level only; no sub-national map manufactured |
| Earthling drilldown, same person control vs scenario | A | 3 agents pre-selected (deterministic, before outcomes), full state timeline both worlds |
| per-write causal receipt (writer/module attribution) | C | requires the write-attribution instrumentation layer; NOT invented |
| counterfactual component removal | C | scenario components separable in principle (forces vs firm_damage vs trade_shock); not exposed in demo UI |

## Guardrails honored

Real engine only; no second simulator; no mocked outputs; no physics
added or tuned (0.8 experimental flags OFF); production untouched;
Hormuz-class energy events explicitly marked INSUFFICIENT CAUSAL
ADAPTER; every unavailable mechanism labeled NOT YET COMPUTABLE in
the UI.

## Launch

    ./scripts/run_observatory.sh          # http://127.0.0.1:8811
    EARTH1_OBS_N=50000 ./scripts/run_observatory.sh   # bigger world
