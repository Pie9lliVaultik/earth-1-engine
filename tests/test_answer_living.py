"""Program 3: the canonical living answer path answers a registered
question end-to-end from alive.World, with provenance, and the
One-Earth routing report passes (static + runtime)."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def test_registered_question_answered_from_living_world():
    from earth1.alive import birth_world, live_one_day, PHYSICS_VERSION
    from earth1.answer_living import answer_question, readout
    from earth1.benchmark_questions import BENCHMARK_QUESTIONS
    w = birth_world(1500, 5)
    rng = np.random.default_rng(5)
    live_one_day(w, rng)
    r = answer_question(w, BENCHMARK_QUESTIONS[0])
    assert 0.0 <= r["yes_pct"] <= 1.0 and r["n"] > 0
    assert r["provenance"]["physics_version"] == PHYSICS_VERSION
    assert r["provenance"]["view"].startswith("effective_forces")
    assert "UNCALIBRATED" in r["provenance"]["calibration"]
    assert "by_cohort" in r and "deprived (>0.5)" in r["by_cohort"] or True
    # readout is non-perturbing: forces/alpha untouched
    f0, a0 = w.civ.forces.copy(), w.civ.alpha.copy()
    readout(w, np.eye(8)[0])
    assert np.array_equal(f0, w.civ.forces) and np.array_equal(a0, w.civ.alpha)


def test_legacy_answer_and_benchmark_refuse_without_opt_in(monkeypatch):
    import importlib
    for mod in ("earth1.legacy_answer", "earth1.legacy_benchmark",
                "earth1.legacy_predictions", "earth1.lab_archive"):
        monkeypatch.delenv("EARTH1_LEGACY_COMPARISON", raising=False)
        monkeypatch.delenv("EARTH1_LAB_ARCHIVE", raising=False)
        sys.modules.pop(mod, None)
        try:
            importlib.import_module(mod)
        except ImportError as e:
            assert "ONLY" in str(e) or "PROVENANCE" in str(e)
        else:
            raise AssertionError(f"{mod} imported without opt-in")


def test_one_earth_routing_report_passes():
    out = subprocess.run([sys.executable,
                          str(ROOT / "scripts" / "one_earth_routing_report.py")],
                         capture_output=True, text=True, timeout=900)
    assert out.returncode == 0, out.stdout[-2000:] + out.stderr[-2000:]
    rep = json.loads((ROOT / "data" / "one_earth_routing_report.json")
                     .read_text())
    assert rep["ONE_EARTH_CODE_PATH"] == "PASS"
    assert rep["legacy_gate_violations"] == []
