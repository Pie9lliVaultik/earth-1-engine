"""C2+ substrate KAs (MISSION v2 WS1)."""
import hashlib
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from earth1.genesis import GENESIS_COUNTRIES, genesis

TABLES = os.path.join(ROOT, "data", "c2plus_tables_v1.json")


def _hash_civ(civ):
    h = hashlib.sha256()
    for a in ("age", "education", "income", "urban", "forces", "alpha",
              "openness", "religiosity", "ideology"):
        h.update(np.ascontiguousarray(getattr(civ, a)).tobytes())
    return h.hexdigest()


def test_default_path_byte_identical():
    """substrate=None must be the incumbent genesis, bit for bit."""
    assert _hash_civ(genesis(3000, 11)) == _hash_civ(
        genesis(3000, 11, substrate=None))


def test_unknown_substrate_raises():
    with pytest.raises(ValueError):
        genesis(1000, 11, substrate="nope")


@pytest.mark.skipif(not os.path.exists(TABLES),
                    reason="tables not built yet (prime artifact)")
def test_c2plus_substrate_margins_and_sex():
    civ = genesis(20000, 11, substrate="c2plus_v1")
    assert hasattr(civ, "sex") and set(np.unique(civ.sex)) <= {0, 1}
    import json
    tab = json.load(open(TABLES))
    # spot-check the sex margin for the largest country present
    ci = np.bincount(civ.country).argmax()
    iso2 = GENESIS_COUNTRIES[ci]["iso2"]
    t = np.asarray(tab["tables"][iso2])
    m = civ.country == ci
    want = t.sum(axis=(1, 2, 3, 4))[0]
    got = float((civ.sex[m] == 0).mean())
    assert abs(got - want) < 0.04
    # education/income joints come from the table, not independence:
    e = np.zeros((3, 3))
    np.add.at(e, (civ.education[m], civ.income[m]), 1.0)
    e /= e.sum()
    te = t.sum(axis=(0, 1, 4))
    assert np.abs(e - te).max() < 0.05
