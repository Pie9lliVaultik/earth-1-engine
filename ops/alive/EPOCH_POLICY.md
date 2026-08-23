# EPOCH POLICY (founder ruling 2026-08-23, registered before the Epoch-2 transition)

`DEPLOYED CANONICAL PHYSICS CHANGE => NEW LIVE EPOCH`

- A live epoch is one world (one UUID, one genesis seed, one physics
  version, one continuous synthetic clock) evolved by the single-writer
  daemon. Its state is never hot-swapped into a different physics.
- When the canonical `PHYSICS_VERSION` deployed to production changes,
  the running epoch is ARCHIVED (final daemon checkpoint, stop, off-box
  backup with far-end verification, restore rehearsal, archive manifest)
  and a NEW epoch is born from genesis under the new physics.
- Development experiments, candidates, branches, Stage/KA runs and
  benchmarks do NOT create epochs. They run on lab worlds or on
  registered snapshots/branches of the live epoch; the live trajectory is
  never perturbed by a measurement.
- Archived epochs are READ-ONLY / HISTORICAL: reproducible (snapshot +
  RNG + commit + physics version), accessible only through an explicit
  archive path, never resolved by an official surface.
- Epoch identity lives in `data/alive/EPOCH.json` (written once at birth:
  epoch, world_uuid, seed, population, physics_version,
  genesis_world_hash, genesis_commit, born_at), echoed into `state.json`
  on every save and into every API/readout identity.

## Registry

| epoch | status | seed | physics | code | genesis | notes |
|---|---|---|---|---|---|---|
| 0 | archived (v0 pre-schema; migrated into Epoch 1 at day ~110) | 42 | incumbent | 14401ea lineage | — | `tainted-epoch1-attempt1` retained |
| 1 | **ARCHIVED / READ-ONLY / HISTORICAL** (2026-08-23 08:54 UTC) | 42 | incumbent (pre-76a574c: instant-write cascades, contagion on, old COLLECTIVE law) | 2396094 (tag `epoch1-production-lineage`) | 4,000,000 agents; FINAL day 3845, alive 3,337,113; snapshot sha256 89e0d33a…; world hash f34a80f1…; RNG persisted; archive `data/archive/epoch1-final-day3845` (read-only) + Storage Box `earth1/archive/epoch1-final-day3845` (far-end verified, restore rehearsal PASSED) | physics_version `null` in that code (pre-declaration incumbent); accessible only via the archive path |
| 2 | **ARCHIVED / READ-ONLY / HISTORICAL** (2026-08-23 12:16 UTC; final day 185, alive 3,975,065, sha 0a0a85af…, hash 085d0c1f…, off-box verified, restore rehearsal PASSED) | **20260823** (fresh; never used — burned/reserved list in SESSION_STATE) | `0.8-candidate-v3/39994f0-canonical` | deployed 69ee9d0 (`DEPLOYED`), service matches, worktree clean | world_uuid `ad0e4af4-9cc5-4d1f-8f5e-28710de6b731`; genesis hash 98bc601c…; first checkpoint day 30 sha 55a8d551… (world hash 3627ea31…); ONE_EARTH_LIVE PASS; smoke PASS; off-box backup verified | scientific status PRE-BENCHMARK / NOT VALIDATED; genesis Earth (no calendar alignment — C1-PRED stays blocked; a timeline-born Earth would be a later epoch) |

Seed 20260823 is hereby burned for Epoch 2 only.

| 3 | **LIVE CANONICAL EARTH** (born 2026-08-23 12:16:49 UTC; uuid bf5359fa-3ddd-4389-be8e-9083b428576c; genesis hash f4dc68ca…; commit 81b1bac; ONE_EARTH_LIVE PASS @day 30 sha 9659ecb6…; smoke PASS 10/10) | **20260824** (fresh; burned for Epoch 3 only) | `0.8-candidate-v4.1/posthumous-invariant-rc` | main ≥ be6c0c6 (EPOCH_3_RELEASE_GATE: SHIP) | 4,000,000 agents, `birth_world(POP, SEED)`; history recorder ON from day 0 | EPOCH_3_DEPLOYMENT_VALIDATED by the 16 targeted regressions; PHASE_0_8_SCIENTIFIC_STATUS remains IN PROGRESS |

## 4M pilot (prime, 2026-08-23, main 802e124, daemon path `scripts/world_alive.py`)
genesis 4,000,000 @ seed 20260823 ≈ 2.5 min; 27–30 s per world-day (production period 60 s → no backlog); RSS ≈ 15 GB; `EPOCH.json` written (uuid 468a3dfa…, genesis hash 2d9a7c2a…); SIGTERM checkpoint at day 10 (sha 25201b12…); reload: 139 open episodes, 50 cooldown entries, 83 residues, RNG continued; two independent reload + 2-day replays → identical world hash f34c55f2…. PASS. (Pilot world discarded; it is not Epoch 2.)
