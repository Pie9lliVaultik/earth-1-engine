# CANONICALIZATION OF CANDIDATE 76a574c — PROGRAMS 1 + 2 (frozen)

Founder ruling 2026-08-22: return to Bible v4.1 execution. Sequence
locked: finish Stage C → port 76a574c → prove equivalence → finish
One-Earth wiring (0.4/0.5) → close 0.7 → canonical 0.8 → Epoch 2 →
benchmarks. Stage D NOT launched; A–I chain stops after Stage C.
Objective: canonical Earth-1 physics == validated lab candidate
76a574c. Mechanical port; no new mechanisms, no parameter/threshold
changes, no coefficient search, no production deployment.

## PROGRAM 1 — component map (lab → canonical target)

| lab component (where it lives today) | canonical destination |
|---|---|
| `field_lab._sample_partners`, `dyadic_move`, `_accumulate_drive`, `make_dyadic_propagate_v6(3, 0.05)` | `earth1/influence.py`: canonical `propagate` becomes the dyadic law (k=3, mu=0.05, tie-weighted inverse-CDF partner sampling); the day's DRIVE_ACC/ENC_COUNT become per-tick scratch carried on the World (not module globals) |
| it6/it11 `conv` closure (C3 log-odds, gain 0.003, encounter-driven; `conviction_lab.c3_logodds_symmetric` family) | `earth1/influence.py`: canonical `update_conviction` := that law, consuming the tick's encounter drive |
| `field_lab.make_dyadic_feed_v6(0.05)` (+ `AROUSAL` vector from `feed.AROUSAL_WEIGHT`) | `earth1/feed.py`: `feed_tick` := dyadic feed law |
| `cont.CONTAGION_GAIN = 0.0` (runtime patch) | `earth1/contagion.py`: declared canonical constant 0.0 |
| `field_lab.flourishing_level_map` (FEAR/DESIRE/COLLECTIVE/CULTURE/EXPERIENCE level terms; centered belonging under flag) | `earth1/life.py` `life_force_target`: terms absorbed natively; centered belonging as the law |
| `field_lab.flourishing_writes_disabled` (restore-after wrapper) | `earth1/flourishing.py`: the force-write lines removed (equivalence requires those writes are the tick's final force operations — verified during port) |
| `EARTH1_CASCADE_COOLDOWN`, `EARTH1_DECAY_RESIDUE` (alive.py) | unconditional canonical semantics; flags removed |
| `EARTH1_COLLECTIVE_CENTERED` (life.py + field_lab) | the law; reference constants as registry-tagged module constants |
| `CANONICAL_DAY.relax = 0.25` | `0.045` (the validated value) |
| `EARTH1_TEST_CLOSED_LOOP`, `EARTH1_TEST_DETECTOR_EFFECTIVE` | retained under the single `EARTH1_TEST_*` namespace, excluded by the release gate from production |
| `field_lab`/`conviction_lab` instrumentation (SAMPLES, DOSE_STATS, PASS_LOG, `_DAY`) | not physics; stays in lab/instrument code, never on the canonical path |
| `scripts/it6_dyadic.py` assembly (op/cnv/flr/cas/relax keys) | becomes a thin runner over canonical `live_one_day`; "ALL" == flagless canonical; ablation keys re-point to canonical alternatives only where a registered ablation still needs them |

After equivalence: `field_lab`/`conviction_lab` move to archive
(`experiments/lab_archive/`) and join `legacy_gate.QUARANTINED`;
one authoritative implementation remains. Physics version string
declared in `earth1/alive.py` (PHYSICS_VERSION) and stamped by
`earth1/manifest.py` provenance.

## PROGRAM 2 — port-equivalence battery (registered BEFORE port code)

Compared objects, lab 76a574c (it6 "ALL" assembly + three flags)
vs canonical port (flagless `live_one_day`), identical initial
world / seed / RNG stream / events / horizon:
- all eight stored force arrays (`civ.forces`) — bitwise;
- conviction (`civ.alpha`) — bitwise;
- Chronicle state (events list: ids, salience, scope, rehearsals;
  `cascade_last_fired`; `cascade_residues`) — exact;
- effective-force readout (`effective_forces`) — bitwise;
- flourishing state arrays — bitwise;
- life/material state (deprivation, wealth, employed, firm, wage,
  firm_health, political, social_need, addiction, mental) — bitwise;
- population/alive, births/deaths counters — exact;
- social fabric touched by candidate mechanisms (adjacency nnz and
  tie-type matrices after plasticity) — exact;
- `persistence.world_hash` — equal.
Cases:
1. KA-short: N=20k, seeds 8890 and 424243, 10 days, full state
   comparison every day (bitwise).
2. GEO-1 KA battery on the canonical port (flagless) — ALL PASS.
3. PF-DECAY-2 KA battery (12) on the canonical port — ALL PASS.
4. IT6 social-dynamics invariants: it6 "ALL" @8890 120d through the
   canonical port must reproduce `data/geo1/it6_all.json` panels/tau/
   transmission EXACTLY (the candidate-v2 recorded values) and the
   forces bitwise vs a lab re-run.
5. One complete 365-day comparison on development seed 9301 (Stage A
   v2 seed): canonical port vs lab assembly, full state bitwise at
   every 10-day census point and at day 365; the endurance census
   must equal `data/acceptance_0_8/stageA_v2/endurance.json`
   END_9301 exactly.
TOLERANCE (registered now): bitwise equality (tolerance 0) on every
floating array. The port moves evaluation order verbatim; if any
step's evaluation order must change, the affected array, the reason,
and a numerically justified tolerance are recorded in this file
BEFORE the comparison is run. Absent such an entry, any nonzero
difference is a PORT BUG: STOP, diagnose the port, never touch
physics.
Decision: all five cases green ⇒ Program 2 PASS ⇒ Program 3
(One-Earth wiring). Any red ⇒ STOP.

## Provenance stamping (Program 4 requirement, applied from the port)

Every run records: git commit + dirty flag, world schema version,
PHYSICS_VERSION, snapshot id/sha, parameter registry hash, seed/RNG
stream, host, thresholds, artifact checksums (`earth1/manifest.py`).
