"""Recorder v2 regression (founder ruling 2026-08-26).

The v1 recorder matched cascade residues on r["day"] == post-tick w.day,
but firings are stamped PRE-increment (alive.py writes residues before
w.day += 1), so zero cascade rows were ever persisted while the tick
journal counted them. These tests pin the alive->recorder contract.
"""
import hashlib
import os
import sqlite3
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from earth1.alive import birth_world, live_one_day
from earth1.history import Recorder, _SCHEMA
from earth1.types import Force

POP, SEED = 2000, 4242


def _fresh_recorder(tmp_path):
    con = sqlite3.connect(str(tmp_path / "hist.sqlite"))
    con.executescript(_SCHEMA)
    return Recorder(con), con


def _force_panic(w):
    """Meet panic_cascade (ECONOMICS<0.3, FEAR>0.5) everywhere, with
    margins wide enough to survive one day of dynamics."""
    w.civ.forces[:, Force.ECONOMICS] = 0.05
    w.civ.forces[:, Force.FEAR] = 0.95


def test_fired_cascade_yields_persisted_rows(tmp_path):
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    rec, con = _fresh_recorder(tmp_path)
    rec.record(w)                              # attach (floor = today)
    _force_panic(w)
    st = live_one_day(w, rng)
    assert st["cascades_fired"] > 0, \
        "physics precondition failed - the test itself is broken"
    out = rec.record(w, st)
    n = con.execute("SELECT COUNT(*) FROM cascades").fetchone()[0]
    assert out["history_cascades"] >= 1, \
        "REGRESSION: fired cascades produced zero history rows"
    assert n == out["history_cascades"]
    day, rule, loc = con.execute(
        "SELECT day, rule, loc FROM cascades LIMIT 1").fetchone()
    assert rule in ("panic_cascade", "identity_collapse",
                    "collective_surge", "polarization_lock",
                    "economic_boom")
    assert day == w.day - 1                    # pre-increment stamp


def test_no_duplicates_on_rerecord_or_quiet_tick(tmp_path):
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    rec, con = _fresh_recorder(tmp_path)
    rec.record(w)
    _force_panic(w)
    st = live_one_day(w, rng)
    rec.record(w, st)
    n1 = con.execute("SELECT COUNT(*) FROM cascades").fetchone()[0]
    assert n1 >= 1
    out2 = rec.record(w, st)                   # same-state re-record
    st3 = live_one_day(w, rng)                 # cooldown blocks refire
    out3 = rec.record(w, st3)
    n3 = con.execute("SELECT COUNT(*) FROM cascades").fetchone()[0]
    assert out2["history_cascades"] == 0
    assert n3 == n1 + out3["history_cascades"]
    dup = con.execute("SELECT day, rule, loc, COUNT(*) c FROM cascades "
                      "GROUP BY day, rule, loc HAVING c > 1").fetchall()
    assert not dup, f"duplicate cascade rows: {dup}"


def test_recorder_is_observation_only(tmp_path):
    """Recording every tick must not change the trajectory: the
    recorder reads state and draws no randomness."""
    def run(with_recorder):
        w = birth_world(POP, SEED)
        rng = np.random.default_rng(SEED)
        rec = None
        if with_recorder:
            rec, _ = _fresh_recorder(tmp_path / f"r{with_recorder}")
            rec.record(w)
        h = hashlib.sha256()
        for _ in range(6):
            st = live_one_day(w, rng)
            if rec is not None:
                rec.record(w, st)
            h.update(np.ascontiguousarray(w.civ.forces).tobytes())
            h.update(w.health.alive.tobytes())
            h.update(np.ascontiguousarray(w.life.wealth).tobytes())
        return h.hexdigest()

    (tmp_path / "rTrue").mkdir()
    (tmp_path / "rFalse").mkdir()
    assert run(True) == run(False)
