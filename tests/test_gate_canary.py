"""The gate's own negative control.

A release gate that cannot refuse is decoration. This canary passes in
any honest run and fails when EARTH1_GATE_SABOTAGE is set — giving
tests/test_release_gate.py an end-to-end path to prove the gate returns
REFUSED through the real subprocess machinery, without corrupting any
actual invariant suite.
"""
import os


def test_gate_canary():
    assert os.environ.get("EARTH1_GATE_SABOTAGE") != "1", \
        "sabotage flag set — the gate must refuse this build"
