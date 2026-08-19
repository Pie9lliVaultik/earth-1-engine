"""THE RELEASE GATE — is this Earth-1 build structurally eligible?

Phase 0.3. One command answers it:

    python3 -m earth1.release_gate

Exit 0 = ELIGIBLE. Exit 1 = REFUSED, with the broken invariant named.
A machine-readable verdict is written to `data/release_gate_report.json`
(generated, never hand-maintained — BIBLE §15).

This is not "more tests". It is the refusal condition: a candidate
build that breaks any invariant Phase 0 EARNED — each one paid for with
a production incident or a signed-off audit finding — does not ship,
whatever else is green. The gate maps every earned invariant to the
suite that enforces it, and each suite contains the negative controls
proving its checks can fail (Standing Rule 2: a test that cannot
demonstrate failure is not yet evidence).

The gate itself is under test: tests/test_release_gate.py sabotages a
gate invariant end-to-end and proves release is REFUSED.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ── the earned invariants, each mapped to its enforcing suite ────────
# Order tells the story of Phase 0. A gate entry is only added when its
# invariant has been accepted in production; nothing speculative lives
# here.
GATE = {
    "one_canonical_world_and_loop":
        "tests/test_one_loop.py",              # 0.2: one alive.World,
                                               # one live_one_day, one
                                               # CANONICAL_DAY, every
                                               # subsystem exactly once,
                                               # one cascade, RNG parity
    "declared_persistence_policy":
        "tests/test_persistence_roundtrip.py", # 0.0c: schema-driven
                                               # save, fail-closed load,
                                               # RNG/state continuation,
                                               # atomic + loadable
                                               # snapshots
    "provenance_and_deployment_identity":
        "tests/test_provenance.py",            # 0.0e: running SHA ==
                                               # intended, clean tree,
                                               # service in git
    "daemon_startup_contract":
        "tests/test_daemon_startup.py",        # empty-state birth, v0
                                               # fail-closed, atomic
                                               # graph, v1 load priority
    "chronological_aging":
        "tests/test_alive_semantics.py",       # 0.0a: the clock and
                                               # only the clock
    "virgin_slot_rebirth":
        "tests/test_rebirth.py",               # 0.0b: reset schema,
                                               # zero inherited ties,
                                               # graph validity at birth
    "fabric_rehoming":
        "tests/test_rehome.py",                # 0.0d: context changes
                                               # re-home ties; no stale
                                               # locality/workplace;
                                               # mutuality
    "mortality_and_cause_accounting":
        "tests/test_correctness_0_1.py",       # 0.1: end-of-tick
                                               # identity, CauseOfDeath
                                               # contract, decay OFF
    "doctrine_present":
        "tests/test_doctrine_present.py",      # XI.A cannot quietly
                                               # disappear
    "gate_canary":
        "tests/test_gate_canary.py",           # proves THIS GATE can
                                               # refuse (sabotage hook)
}


def run(suites: dict | None = None, extra_args: list | None = None) -> dict:
    """Run the gate. Returns the verdict dict and writes the report."""
    suites = suites or GATE
    results = {}
    for invariant, path in suites.items():
        p = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--no-header",
             str(ROOT / path)] + (extra_args or []),
            capture_output=True, text=True, cwd=ROOT)
        tail = (p.stdout.strip().splitlines() or [""])[-1]
        results[invariant] = {"suite": path,
                              "passed": p.returncode == 0,
                              "summary": tail[-120:]}
    return evaluate(results)


def evaluate(results: dict) -> dict:
    """Pure verdict logic — REFUSED if ANY invariant is broken."""
    broken = sorted(k for k, v in results.items() if not v["passed"])
    verdict = {
        "eligible": not broken,
        "verdict": "ELIGIBLE" if not broken else "REFUSED",
        "broken_invariants": broken,
        "invariants": results,
    }
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"],
                                capture_output=True, text=True,
                                cwd=ROOT).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True,
                               cwd=ROOT).stdout.strip()
        verdict["commit"] = commit
        verdict["dirty_worktree"] = bool(dirty)
    except OSError:
        verdict["commit"] = None
    out = ROOT / "data" / "release_gate_report.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(verdict, indent=1))
    return verdict


def main() -> int:
    v = run()
    print(f"\nEARTH-1 RELEASE GATE: {v['verdict']}"
          f"  (commit {str(v.get('commit'))[:12]},"
          f" dirty={v.get('dirty_worktree')})")
    for name, r in v["invariants"].items():
        mark = "ok " if r["passed"] else "BROKEN"
        print(f"  [{mark:6s}] {name:38s} {r['summary']}")
    if not v["eligible"]:
        print(f"\nREFUSED — broken: {', '.join(v['broken_invariants'])}")
        print("A build that violates an earned invariant does not ship, "
              "whatever else is green.")
        return 1
    print("\nStructurally eligible for release. (Eligibility is "
          "necessary, not sufficient: benchmarks are Part VI's job.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
