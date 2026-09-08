# APPARATUS CYCLE 1 — 2026-09-08

One named apparatus batch: every FREE fix from the external-review triage
(ops/alive/EXTERNAL_REVIEW_VERIFICATION_2026-09-08.md), implemented with a
regression test per fix. ZERO frozen-physics changes: the full working
tree reproduces pristine HEAD's day-10 v1 trajectory hash bit-for-bit
(2k c2plus, seed 42, freeze09 env, fresh processes):
32084351ea66b02966a580e248b98add9129dabbc4aa304de38be920d6e0eea3 == HEAD.

## Fixed (finding -> mechanism)

| finding | fix |
|---|---|
| M01b | One age convention: every serving interface (profile, filters, cohorts, custom-model predicates) converts through the canonical engine scale; the divergent 18+82a / a*100 / 87.6a conversions removed. Explicitly-set legacy env scale still honoured. |
| M02a/b | configstamp parses scripts/env/freeze09.env as the single source of truth (all 11 frozen degrees of freedom incl. the four coefficients, floats at rel tol), and verifies LOADED module state, so an import that precedes the exports now fails the stamp with a named loaded_mismatch. assert refuses on both. |
| M02c | v1 API serves a freeze tag DERIVED from the stamp ('unfrozen-dev:<n>' on mismatch), logs the degradation, and /health reports physics_stamp ok/degraded. |
| M02d | genesis defaults its substrate from EARTH1_SUBSTRATE_FLAG when the argument is None — the daemon's empty-state birth path can no longer silently birth the incumbent under the frozen env. Unknown substrates now raise before the calibration guard. |
| M03a | v1 world hash FROZEN as an explicit field list (recorded digests stay reproducible); new world_hash_full() covers the declared stragglers (civ.sex, life.firm_distress(+companions), chronicle.cascade_residues) via a registry with absent-value sentinels. |
| M03b | Rebirth policy covers sex; newborn sex drawn from a slot-keyed spawned generator — main rng stream provably untouched (twin worlds bitwise-equal). |
| M03c | Checkpoint load guards: missing digest sidecar refuses (override param); new .meta.json sidecar carries both world hashes + pickle and graph digests, graph tampering refuses; physics-label mismatch refuses (override param). Legacy sidecars load as checksum='legacy'; legacy .sha256 format unchanged for ops tooling; run_backup.sh stages the new sidecar. |
| M04 | Public branch.run pairs each control arm with a persists_days-matched null scenario (the adapter's contract); the reviewer's zero-impact probe now reads exactly 0 with identical arm hashes. |
| M05b | Indexed Chronicle CSC cache is provenance-checked against the live adjacency object; indexed path stays disabled for V1. |
| M05c | Partner sampler returns absent partners on an empty graph instead of raising; rng draw order untouched on non-empty graphs. |
| M06a | Geography delta_people carries the same world-population scale as the global line; people_per_agent included for reconciliation. |
| M06b | Substituted snapshot days are labelled with the day actually measured (requested_day/measured_day), never silently relabelled. |
| M06c | SEM divisor corrected to sqrt(n) at both sites. All previously committed ± values were ~3.3% too wide (conservative); frozen artifacts keep their recorded values — this line is the erratum. GFC direction t=2.2 is 2.28 corrected. |
| M06d | A DeathWatch per arm now reports deaths_cumulative in consequence reports; the old current-dead-slot stock is renamed dead_slots_now and labelled as a stock. |
| M07b | Binary calibration tier keys on a binary_calibrated marker the binary path actually consumes; temperature_fitted remains the softmax key. /health reads through the adapter (registered + overlay). |
| M07c | Conditional door uses YES/NO keys for two-outcome questions — the KeyError('O0') crash on the real path is gone. |
| M07d | Request-time class registration goes to question_classes_auto.json (overlay, registered-wins); templates deep-copied before conditional mutation; the registered file is byte-identical after any request (asserted by test). |
| M09 | Editable/wheel install works (explicit package discovery); earth1-benchmark entry point repointed to the module that exists; torch tests importorskip. |
| S03a | v1 auth fails CLOSED on an empty allowlist (EARTH1_DEV_OPEN=1 is the explicit dev override). |
| S03b | /billing/usage authenticated and self-scoped. |
| S03d | Cancelled/unpaid subscriptions downgrade to free, idempotently. |
| S02+ | Async jobs bounded (EARTH1_MAX_JOBS, 429 when full), TTL-evicted, horizon/seeds clamped. |
| S04 | Backup stages history.sqlite (sqlite3 .backup, wal/shm aware) + the new checkpoint meta sidecar; model-store exclusion stated explicitly. |
| — | Session lifecycle: auth middleware and budget middleware close their DB sessions on all paths. |
| — | Pre-existing: unknown-substrate validation ordered before the calibration guard; billing webhook tests rewritten to the signed path; unit-suite template pins its substrate explicitly (ambient-env sensitivity removed); rehome sabotage control made composition-robust. |

## Discovered during implementation

**M05a RECLASSIFIED: LIVE physics defect, not latent.** The whole-matrix
clamp in tie-adding mass-collapses plasticity-drifted weak ties to the
nominal weight on every migration day, partially undoing echo-chamber
formation. Repairing it moves the frozen trajectory (bisect-proven), so
the repair ships FLAG-GATED default-off (EARTH1_REHOME_LOCAL_CLAMP=1)
and joins the founder's physics-ruling queue with M01a.

## Prepared, awaiting founder rulings (physics)

1. M01a urban-axis fix: EARTH1_URBAN_AXIS_FIX, default off (bitwise
   identical), prereg ops/alive/cycles/URBAN_FIX_PREREG.md — poverty
   anchors GATED, five physics consumers' observables named.
2. M05a rehome clamp: EARTH1_REHOME_LOCAL_CLAMP, default off (bitwise
   identical); needs its own prereg before promotion.
3. M07a binary readout: ops/alive/RULING_REQUEST_BINARY_READOUT.md
   (options KEEP+relabel / calibrate map / redesign; recommendation A
   then B).

## Verification

- Trajectory neutrality: full tree == pristine HEAD, day-10 v1 hash
  bitwise (above). Per-cluster A/Bs recorded in the workflow reports.
- Tests: 9 new regression files, 89 tests, all passing; review's two
  targeted suites 51 + 64 all passing in flag-free AND freeze-sourced
  shells; billing suite 19 passing.
- Note for API consumers: served OUTPUTS change where the fixes bit —
  profile/cohort ages, consequence units/SEM/deaths, /health tiers,
  auth failure modes. No committed board or frozen artifact value was
  restated; erratum noted at M06c.
