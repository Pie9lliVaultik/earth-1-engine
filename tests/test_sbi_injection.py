"""Injection KAs for the SBI synthetic twin (THREE_TRACK_PREREG_v1 A2).

KA-0 identity, KA-1 determinism, KA-2 leverage. Standing Rule 2: a
harness in which some theta changes nothing must FAIL here.
critical_fraction's KA-2 needs populated localities and runs inside the
prime screen scorer (run_screen.py asserts it and VOIDs otherwise);
everything else proves locally at small scale.
"""
import hashlib
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sbi.theta import CANONICAL, apply_theta, prior_ppf, run_days

POP, DAYS, SEED = 2000, 10, 4242


def _traj_hash(theta):
    from earth1.alive import birth_world
    kw = apply_theta(theta)
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    daily = run_days(w, rng, DAYS, kw)
    h = hashlib.sha256()
    h.update(repr([(d["alive"], d["employment_rate"], d["wealth_mean"],
                    d["force_mean"], d["cum_deaths"])
                   for d in daily]).encode())
    return h.hexdigest()


@pytest.fixture(autouse=True)
def _restore_canonical():
    yield
    apply_theta(CANONICAL)


def test_ka0_canonical_theta_is_identity():
    """theta=canonical must reproduce the unpatched engine exactly."""
    from earth1.alive import birth_world, live_one_day
    from earth1.observables import collect
    apply_theta(CANONICAL)          # ensure pristine before baseline
    w = birth_world(POP, SEED)
    rng = np.random.default_rng(SEED)
    cum = {}
    rows = []
    for _ in range(DAYS):
        st = live_one_day(w, rng)   # NO theta kwargs at all
        for k in ("deaths", "births", "disease_deaths", "rehomed_migrants",
                  "rehomed_workers", "cascades_fired", "firms_failed"):
            cum[k] = cum.get(k, 0) + int(st.get(k, 0) or 0)
        d = collect(w, cum)
        rows.append((d["alive"], d["employment_rate"], d["wealth_mean"],
                     d["force_mean"], d["cum_deaths"]))
    base = hashlib.sha256(repr(rows).encode()).hexdigest()
    assert _traj_hash(CANONICAL) == base


def test_ka1_determinism():
    assert _traj_hash(CANONICAL) == _traj_hash(CANONICAL)


@pytest.mark.parametrize("name", ["relax", "informal_floor_scale",
                                  "conviction_gain_dyadic"])
def test_ka2_trajectory_leverage(name):
    """p90 of each continuous-path theta must move the trajectory."""
    hi = dict(CANONICAL); hi[name] = prior_ppf(name, 0.9)
    assert _traj_hash(hi) != _traj_hash(CANONICAL), \
        f"{name} at prior p90 changed NOTHING - injection broken"


def test_ka2_unit_hardship_gain():
    """The mortality-gain constant must be read at call time."""
    import earth1.health as health
    age = np.array([50.0, 70.0]); tier = np.array([0, 2])
    dep = np.array([1.0, 1.0]);   add = np.array([0.0, 0.0])
    health.HARDSHIP_GAIN = 1.0
    h1 = health.cancer_hazard(age, tier, add, dep)
    health.HARDSHIP_GAIN = 3.0
    h3 = health.cancer_hazard(age, tier, add, dep)
    health.HARDSHIP_GAIN = 1.0
    assert np.all(h3 > h1), "HARDSHIP_GAIN not consumed at call time"


def test_ka2_unit_memory_press():
    """PRESS must be read at call time and scale the memory push.
    (Trajectory leverage for memory_press needs event-rich worlds and is
    asserted in the prime screen scorer, like critical_fraction.)"""
    import earth1.memory as memory

    class _Civ:
        forces = None

    def _mk():
        civ = _Civ()
        civ.forces = np.full((4, 8), 0.5)
        ch = memory.Chronicle()
        ev = memory.Memory(
            id="ka", label="ka", day=0.0, salience=0.5, half_life=200.0,
            force_signature=np.full(8, 0.1),
            scope=np.array([True, True, False, False]))
        ch.events.append(ev)
        return civ, ch

    memory.PRESS = 0.02
    civ1, ch1 = _mk(); ch1.tick(civ1, 1.0)
    d1 = float(np.abs(civ1.forces - 0.5).sum())
    memory.PRESS = 0.08
    civ2, ch2 = _mk(); ch2.tick(civ2, 1.0)
    d2 = float(np.abs(civ2.forces - 0.5).sum())
    memory.PRESS = 0.02
    assert d2 > d1 * 2, "PRESS not consumed at call time"


def test_ka2_informal_prior_never_saturates_clip():
    """The 0.95 clip must be a no-op across the whole prior range —
    otherwise the prior has a flat (unidentifiable-by-construction)
    region at the top."""
    import earth1.life as life
    assert life.INFORMAL_SCALE == 1.0
    assert max(life.INFORMAL.values()) * 1.3 <= 0.95
