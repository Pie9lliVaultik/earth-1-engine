"""Shared fixtures for the live-path suite.

The repo had no conftest.py at all until Phase 0.3 — every test file
carried its own `sys.path.insert(0, ".")` prologue and there was no
shared way to build a world. That is why the living substrate had zero
coverage: there was nothing to hang a test on.

Sizing: `birth_world(2_000)` gives 194 countries at 10-11 agents each,
births in ~1.2s, and is the smallest population that is not degenerate
(`_be_born` needs `living.size >= 10`, alive.py:244).

CAVEAT, documented deliberately: at this size locality populations fall
below the `pop_l >= 10` cascade gate (alive.py:197), so cascades never
fire. No invariant here depends on them — but nothing else may be
smoke-tested at this size without re-deriving that floor first.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TINY_POP = 2_000
TINY_SEED = 42


@pytest.fixture(scope="session")
def _tiny_template():
    """One birth per session — birthing is the expensive part, not ticking.

    PINNED SUBSTRATE (apparatus cycle 1): the M02d fix makes ambient
    EARTH1_* exports steer birth, so a suite run from a freeze-sourced
    shell births a different template than the flag-free run the suite's
    guarantees were derived on. The template now selects its substrate
    EXPLICITLY, consistent with the import-bound income calibration (the
    genesis guard refuses a mismatched pair), so collection works from
    any shell and the choice is visible here rather than ambient.
    Freeze-configuration behaviour has its own tests
    (test_review_configstamp.py), which spawn fresh processes on purpose.
    """
    from earth1.alive import birth_world
    from earth1.life import INCOME_CALIBRATION
    sub = "c2plus_v1" if INCOME_CALIBRATION != "off" else None
    return birth_world(TINY_POP, TINY_SEED, substrate=sub)


@pytest.fixture
def tiny_world(_tiny_template):
    """A fresh, isolated 2,000-agent world.

    Deep-copied from a session template so a test that mutates the world
    cannot leak into the next one.
    """
    import copy
    return copy.deepcopy(_tiny_template)


@pytest.fixture
def rng():
    return np.random.default_rng(7)
