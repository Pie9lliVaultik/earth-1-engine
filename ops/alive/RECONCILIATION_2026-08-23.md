# RECONCILIATION PASS — 2026-08-23 (no physics, thresholds, criteria or API semantics changed; Epoch 3 NOT deployed)

## 1. GitHub state
`git fetch origin`; `HEAD == main == origin/main == 2e28a4e` (3cfe0a7 is an ancestor, present on origin/main); 0 local commits ahead, 0 behind; tree clean (8 untracked diagnostic pickles/logs under data/diag1, data/h_cascade_1 — raw recorder dumps, deliberately unversioned; their derived JSONs are committed). v1-unification = 843f596 (superseded by main, kept).
**GITHUB_UNIFIED_STATE: COMPLETE.**

## 2. API-COMPLETE-1 true status — the five non-DIRECT families

| family | original audit requirement | implementation | live endpoint | persistent state | why not DIRECT | pre-existing ruling / deferral | acceptance-criterion status |
|---|---|---|---|---|---|---|---|
| tie formation / dissolution | per-edge formation/dissolution history | plasticity totals (ties_strengthened/weakened/pruned/rewired) are in the daily journal; per-edge history is not recorded | `/world` (totals only) | no per-edge log | a per-edge event log is new recorder scope, not in the frozen gap matrix (matrix row "social graph: direct ties" covers current edges — DELIVERED) | none | **declared gap** (not in matrix) |
| perishability / resource modules | expose readout "where represented" | `perishability.py` is a legacy pure readout with no product meaning (ONE_EARTH_ACCEPTANCE_0_5: READOUT-ADAPTER disposition) | none | n/a | no canonical state behind it | Phase 0.5 disposition (47ab046 era) | **declared exclusion** |
| equations / readouts (`/ask`) | active equations/readouts where exposed | `answer_living` exists in-process; `/ask` returns 503 "living_calibration_pending" | 503 by design | n/a | founder ruling: no `/ask` answers before calibration (Benchmark A) | ask route docstring + CANONICALIZATION_PROGRAM | **declared exclusion (ruling predates)** |
| timeline / scrub | state at arbitrary supported time | `timeline.py` design exists; the snapshot store (`data/history/`, 2015 timeline) was never built (BIBLE.md: "never actually been run") | none | none | **neither first-class state nor a derivable surface** — this IS NOT_IMPLEMENTED in API terms; I classified it INTERNAL because code exists; that was too generous | Bible item (Epoch born from `timeline.build` = a later epoch, CASCADE_PUBLIC_BENCHMARK_PREREG §7) | **NOT_IMPLEMENTED → API-COMPLETE-1 PARTIAL on this row** |
| assimilation | — (audit listed it as a surface) | `assimilate.py` likelihood functions exist; the ensemble filter is design-only (Bible §IV.8) | none | none | no executable capability to expose | Bible item | **NOT_IMPLEMENTED → PARTIAL** |

Corrected counts (78 families): DIRECT 73, INDIRECT 1, INTERNAL 1 (perishability, excluded), **NOT_IMPLEMENTED 2** (timeline/scrub, assimilation). The gap matrix's 39 items are all implemented; the audit's 78-family ledger is not fully closed. **API-COMPLETE-1: PARTIAL** (73/78 direct; 2 families require the timeline/assimilation infrastructure the Bible schedules separately; 1 excluded by ruling; 1 legacy readout excluded; 1 per-edge history gap declared).

Reconciliation-only code changes (frozen requirement "get Earthling by stable ID"): history coverage metadata on every history response; persons whose slot was reused are served from the record (`status: historical`). Commit 2e28a4e.

## 3. Stable person-id invariant — concrete trace (2000 agents, seed 77)
slot 5 → person_id 5 (parent −1, genesis) → dies day 3 (cvd) → `person_status` = deceased/cvd, still addressable by id 5 → slot 5 reused at day 26 → new person_id **2000**, parent_id 1436 (lineage to a living parent) → id 5 no longer in arrays; `GET /earthlings/5` now answers from the record: status historical, died day 3, cause cvd, events, last force sample → `GET /earthlings/2000/status` shows `slot_previous_occupant_person_id: 5`. `person_id 5` is never reassigned (counter is monotone; `test_stable_person_id_across_rebirth` asserts reborn slots carry ids ≥ N, the previous occupants' ids are absent from the arrays, parent ids are set, and the counter equals N + births). **INVARIANT PASS.** "Stable ID across rebirth" means exactly: the slot changes occupant, the id does not change person.

## 4. History semantics (all history routes now carry `coverage`)
| item | value |
|---|---|
| person events | daily state-diff detection (13 kinds) from `history_available_from_day` |
| force samples | every **30 days** per person (+ day 0 when the recorder starts at genesis); NOT continuous |
| locality / country series | daily |
| first day with data | `MIN(day)` in the record = the day the recorder started; **Epoch 2 has NO record yet** (recorder not deployed; `coverage.history_available=false`) |
| backfill of pre-recorder days | **unavailable, not backfilled** (stated in `coverage.note`) |
| restart persistence | SQLite file beside the snapshot; survives daemon restart; recorder re-establishes yesterday's state on startup (the first post-restart day emits no events) |
| snapshot behaviour | the file is part of `data/alive/` → copied by the backup script (not part of world.pkl) |
| branch behaviour | each branch has its own in-memory record starting at branch creation; live and branch histories do not share storage |
| retention | append-only, unbounded (≈5 GB/year at 4M) |
| overhead at 4M (Epoch-2 snapshot, prime) | 7.6 s/day normal, 20 s on a sampling day, 10–15k events/day; tick 28–29 s → 37 s total < 60 s period |

## 5. Exact physics candidate
- Epoch 2 live: 69ee9d0, `0.8-candidate-v3/39994f0-canonical`.
- main: 2e28a4e, `0.8-candidate-v4/posthumous-invariant`.
Diff 69ee9d0 → main, physics-relevant (`earth1/alive.py`):
**B — can alter civilization evolution:** (1) rows dead at tick start are snapshot/restored (no living-agent update); (2) `_living_view` zero-weights edges into dead rows for `propagate`, `update_conviction`, trait feedback, and the media feed; (3) cascade detector fractions over living residents only; (4) employment released at death. Measured: living forces |Δ| mean 0.0007, max 0.06 at 0.6% dead over 30 days; grows with the dead fraction.
**A — state/API only (dynamics proven bit-identical by forces/alpha/alive/wealth/employment/traits hash f347329a… before/after):** person_id/parent_id/person_counter, life.partner (+ pairing at genesis, widowing at death), geography, history recorder, readouts/routes, loader fill. `integration.py` change = instrument repair (consciousness profile), not daemon physics.
**Conclusion: v4 ≠ v3. Phase 0.8 Stage H has validated v3 only.**

## 6. Frozen Phase-0.8 acceptance battery (ACCEPTANCE_BATTERY_0_8.md, 334afb5) — ledger
| stage / arm | frozen registration | commit tested | physics | seeds | result | report |
|---|---|---|---|---|---|---|
| A endurance | 334afb5 + GEO_1 v2 prereg | 5ce9812 (candidate v2 lab; lab==canonical bitwise per PORT_EQUIVALENCE fb78729) | v2 = v3 dynamics (v3 adds only H-CASCADE-1 episode semantics) | 9301–9303 | PASS 3/3 | STAGE_A_REPORT.md |
| B adversarial / broken twins | e89c98a | cc29b8f / a177d05 | v2 | 9101–9112 (+9106/9110 B11) | PASS 13/13 (B11 scored from record; same-seed twin footnoted) | STAGE_B_REPORT.md |
| C force/cascade census | e89c98a | e2bf34d (v2) + 39994f0 (v3 = H-CASCADE-1) | v2 → v3 | 9501, 9502 | CHARACTERIZED; E3 miss → resolved by H-CASCADE-1 (accepted) | STAGE_C_REPORT.md, H_CASCADE_1_REPORT.md |
| D timescale map / held-out Chronicle T2 | c81bd33 (T2 holdout), STAGE_CD_METHOD_LOCK | **not run** | — | 9201–9206 reserved | OUTSTANDING (founder: returns only against the canonical Earth — now possible on Epoch 2) | — |
| E transmission | 334afb5 (sub-registration pending) | **not run** | — | — | OUTSTANDING | — |
| F India recession probe | 334afb5 | **not run on any candidate** (pre-0.8 gate run 1081a4e was on incumbent physics) | — | — | OUTSTANDING | — |
| G opinion causal receipt | 334afb5 | **not run** | — | — | OUTSTANDING | — |
| H butterfly / FSLE / noise / consciousness | 334afb5 + BIBLE_0_8_REMEASUREMENT (cdca6a2) | 69ee9d0 / 633c5fd (Epoch-2 day-30 snapshot; noise+consciousness fresh genesis) | **v3** | Epoch-2 seed 20260823; noise 101/907; consciousness 42 | placebo 0.0; FSLE λ +0.224/d (8/8, 3–4 d doubling, reach 100%); noise slope +0.203 (< 0.25 bar → "genuinely chaotic" stands); consciousness φ 0.028, no anticipation, phase scan flat; **butterfly running** | BIBLE_0_8_REPORT.md (pending butterfly) |
| I long-horizon / network invariants | 334afb5 | **not run** (Epoch smoke PASS and KA5/KA6 persistence are partial evidence, not Stage I) | — | — | OUTSTANDING | — |

Founder ruling 2026-08-22/23 (recorded in CASCADE_RULE_PROVENANCE_AUDIT / SESSION_STATE): the A–I campaign is E3 evidence; **Bible row 0.8 = Stage H** ("butterfly, FSLE, noise floor, consciousness — same preregs, same thresholds"). Under that ruling "4 arms" = Stage H exactly; Stages D–G, I are NOT superseded by any pre-result ruling — they are outstanding E3/V1 work and must not be reported as closed.

**Did Phase 0.8 validate the exact candidate intended for Epoch 3?** **NO.** Stage H ran on v3. v4 (posthumous invariant) has: KA-style acceptance tests A–F, full estate, a 30-day 20k magnitude check — no Stage A/B/C/H evidence. Under the campaign rules (candidate change ⇒ re-run the frozen stages on the new candidate; no post-hoc rescue), v4 requires at minimum: Stage A endurance (3 fresh seeds), Stage B broken twins, Stage C census (9501/9502 twin comparison v3→v4), then Stage H on a v4 Epoch (or v4 snapshot of Epoch 2's genesis). Only then Epoch 3.

## 7. Roadmap correction
0.5 exit criteria are now all met (live One-Earth invariant by Epoch 2; benchmark imports clean since Program 3). 0.6 accepted earlier. Therefore **HIGHEST CONTIGUOUS FULLY COMPLETED = 0.6** (0.7 partial: hardware ensemble target deferred by ruling; 0.8 = Stage H on v3 in progress). The earlier "0.5 contiguous / 0.6 complete" line was a bookkeeping error.

## 8. DEPLOY EPOCH 3: **NO** (v4 unvalidated by the frozen battery; butterfly arm still running; this pass makes no ruling).
