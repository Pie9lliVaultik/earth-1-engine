"""Branch-engine contrast contract (validated 2026-08-27).

Pins two properties the scenario machinery depends on:
1. null-vs-null branches are bit-identical (CRN pairing exact and
   content-independent);
2. a real scenario separates from the null branch.
A third pin documents the KNOWN artifact: any branch desynchronizes
from an unbranched control, so that contrast is invalid.
"""
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from earth1.alive import birth_world, live_one_day
from earth1.branch import Scenario, apply, null_branch

POP, DAYS, SEED = 2000, 15, 4242


def _run(sc):
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(977 * 13)
    if sc is not None:
        apply(w, sc, rng)
    tr = []
    for _ in range(DAYS):
        live_one_day(w, rng)
        tr.append(w.civ.forces.mean(axis=0).copy())
    return np.array(tr)


def test_null_branches_bit_identical():
    a = _run(null_branch())
    b = _run(Scenario(id="other_null", label="x", forces={},
                      countries=None, firm_damage=0.0, trade_shock=0.0,
                      persists_days=365))
    assert np.array_equal(a, b)


def test_real_scenario_separates_from_null():
    base = _run(null_branch())
    shock = _run(Scenario(id="shock", label="s",
                          forces={"fear": 0.3}, countries=None,
                          firm_damage=0.2, trade_shock=0.1,
                          persists_days=365))
    assert np.abs(shock - base).max() > 1e-6


def test_unbranched_control_is_a_desynced_baseline():
    """Documents the artifact: branch-vs-control differs even for a
    null branch. If this ever becomes identical, the rng accounting
    changed and every paired-contrast convention must be revisited."""
    ctrl = _run(None)
    nb = _run(null_branch())
    assert not np.array_equal(ctrl, nb)
