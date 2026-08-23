# 0.3 — THE SEMANTIC RELEASE GATE

**2026-08-19 · delivered. One command answers one question:**

    python3 -m earth1.release_gate
    → EARTH-1 RELEASE GATE: ELIGIBLE | REFUSED (exit 0 | 1)

Verdict is machine-readable (`data/release_gate_report.json`, generated
never hand-maintained) and names the broken invariant on refusal.

## The earned invariants — the refusal conditions

Each entry was paid for with a production incident or a signed-off
audit finding; nothing speculative is in the gate.

| invariant | earned by | suite (checks) |
|---|---|---|
| one canonical world + loop + config, every subsystem ×1, cascade ×1, RNG parity | 0.2 | test_one_loop (13) |
| declared persistence policy, fail-closed load, exact continuation, atomic snapshots | 0.0c | test_persistence_roundtrip (21) |
| provenance / deployment identity | 0.0e | test_provenance (14) |
| daemon startup contract, v0 fail-closed, atomic graph, v1 load priority | 0.0c/0.0a-era misses | test_daemon_startup (9) |
| chronological aging, clock-only | 0.0a | test_alive_semantics (8) |
| virgin-slot rebirth + graph validity at birth | 0.0b | test_rebirth (13) |
| fabric re-homing, no stale context, mutuality | 0.0d | test_rehome (16) |
| mortality/population accounting + CauseOfDeath contract + decay OFF | 0.1 | test_correctness_0_1 (17) |
| doctrine present in all three places | XI.A | test_doctrine_present (18) |
| the gate can refuse | 0.3 | test_gate_canary (1) |

**130 invariant checks**, every suite carrying negative controls proven
to fail (Standing Rule 2).

## The gate itself is under test

- verdict logic: ANY single broken invariant → REFUSED (parametrized
  over all ten — no majority, no severity tiers)
- the gate cannot quietly shrink: removing an invariant from the map
  fails CI
- **end-to-end refusal proven**: with a sabotaged invariant the real
  command prints `REFUSED — broken: gate_canary` and exits 1; honest
  run exits 0

## Boundary of the claim

Eligibility is necessary, not sufficient: the gate answers *structural*
release-worthiness only. Benchmarks (Part VI) and the 0.8 re-measurement
decide everything else.
