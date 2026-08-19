"""Phase 0.3 — the gate itself is under test.

Two obligations: the verdict logic refuses on ANY broken invariant, and
the refusal works END TO END through the real subprocess machinery —
sabotage a gate invariant and the command answers REFUSED.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from earth1 import release_gate
from earth1.release_gate import GATE, evaluate

ROOT = Path(__file__).resolve().parents[1]


def _fake(passed: dict) -> dict:
    return {k: {"suite": f"tests/{k}.py", "passed": v, "summary": ""}
            for k, v in passed.items()}


# ── verdict logic ───────────────────────────────────────────────────

def test_all_green_is_eligible(tmp_path):
    v = evaluate(_fake({k: True for k in GATE}))
    assert v["eligible"] and v["verdict"] == "ELIGIBLE"
    assert v["broken_invariants"] == []


@pytest.mark.parametrize("broken", sorted(GATE))
def test_any_single_broken_invariant_refuses(broken):
    """ONE broken invariant refuses the build — no majority voting,
    no severity tiers, no exceptions."""
    flags = {k: (k != broken) for k in GATE}
    v = evaluate(_fake(flags))
    assert not v["eligible"]
    assert v["verdict"] == "REFUSED"
    assert v["broken_invariants"] == [broken]


def test_report_is_generated_not_hand_maintained():
    evaluate(_fake({k: True for k in GATE}))
    rep = json.loads((ROOT / "data" / "release_gate_report.json")
                     .read_text())
    assert rep["verdict"] == "ELIGIBLE"
    assert "commit" in rep


# ── the gate covers every earned invariant ──────────────────────────

def test_gate_covers_the_earned_invariants():
    """The founder's 0.3 list, each present in the gate map. Removing
    one from GATE fails here — the gate cannot quietly shrink."""
    required = {
        "one_canonical_world_and_loop",
        "declared_persistence_policy",
        "provenance_and_deployment_identity",
        "daemon_startup_contract",
        "chronological_aging",
        "virgin_slot_rebirth",
        "fabric_rehoming",
        "mortality_and_cause_accounting",
        "doctrine_present",
        "gate_canary",
    }
    assert required <= set(GATE), \
        f"gate lost invariants: {required - set(GATE)}"
    for path in GATE.values():
        assert (ROOT / path).exists(), f"gate suite missing: {path}"


# ── end-to-end refusal through the real machinery ───────────────────

def test_sabotaged_build_is_refused_end_to_end():
    """The one that makes the gate real: with a sabotaged invariant the
    actual command exits 1 and prints REFUSED."""
    env = dict(os.environ, EARTH1_GATE_SABOTAGE="1")
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header",
         str(ROOT / "tests/test_gate_canary.py")],
        capture_output=True, text=True, cwd=ROOT, env=env)
    assert p.returncode != 0, "canary did not trip under sabotage"

    # and the verdict logic converts that into a refusal
    results = release_gate.run(
        suites={"gate_canary": "tests/test_gate_canary.py"})
    assert results["eligible"], "canary must pass in an honest run"
    # now the sabotaged pass through run() itself
    old = os.environ.get("EARTH1_GATE_SABOTAGE")
    os.environ["EARTH1_GATE_SABOTAGE"] = "1"
    try:
        v = release_gate.run(
            suites={"gate_canary": "tests/test_gate_canary.py"})
    finally:
        if old is None:
            os.environ.pop("EARTH1_GATE_SABOTAGE", None)
        else:
            os.environ["EARTH1_GATE_SABOTAGE"] = old
    assert not v["eligible"]
    assert v["verdict"] == "REFUSED"
    assert v["broken_invariants"] == ["gate_canary"]
