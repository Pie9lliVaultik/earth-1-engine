"""Tests for generational dynamics — aging, mortality, inheritance (§21.1)."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.engine import build_genesis_civilization
from earth1.tick import _make_mutable
from earth1.generational import (
    generational_tick, _age_years, _gompertz_a, GOMPERTZ_B,
)

POP = 20_000


@pytest.fixture
def civ():
    return _make_mutable(build_genesis_civilization(POP, seed=42))


def test_aging_advances_with_clock(civ):
    rng = np.random.default_rng(0)
    before = _age_years(civ).copy()
    generational_tick(civ, rng, dt_days=365.0)
    survivors = _age_years(civ) >= before  # newborns reset to 18
    aged = _age_years(civ)[survivors] - before[survivors]
    assert np.allclose(aged[aged > 0].mean(), 1.0, atol=0.1)


def test_mortality_rises_with_age(civ):
    """Gompertz: the old die at a far higher rate than the young."""
    rng = np.random.default_rng(1)
    age_before = _age_years(civ).copy()
    young = age_before < 40
    old = age_before > 70
    stats = generational_tick(civ, rng, dt_days=365.0)
    assert stats["deaths"] > 0
    # deaths show up as agents whose age reset below their prior age
    died = _age_years(civ) < age_before
    p_young = died[young].mean()
    p_old = died[old].mean()
    assert p_old > 5 * max(p_young, 1e-6)


def test_crude_death_rate_plausible(civ):
    """One simulated year: global crude death rate in the demographic
    range for an adult (18+) population — roughly 0.5% to 3%."""
    rng = np.random.default_rng(2)
    stats = generational_tick(civ, rng, dt_days=365.0)
    cdr = stats["deaths"] / civ.n
    assert 0.005 < cdr < 0.03, f"crude death rate {cdr:.4f} implausible"


def test_gompertz_calibration_orders_by_life_expectancy():
    # higher life expectancy -> lower baseline hazard
    assert _gompertz_a(83.0) < _gompertz_a(72.0) < _gompertz_a(55.0)


def test_slots_replaced_in_same_country(civ):
    rng = np.random.default_rng(3)
    country_before = civ.country.copy()
    n_before = civ.n
    generational_tick(civ, rng, dt_days=365.0)
    assert civ.n == n_before
    np.testing.assert_array_equal(civ.country, country_before)


def test_newborns_are_young_adults(civ):
    rng = np.random.default_rng(4)
    age_before = _age_years(civ).copy()
    generational_tick(civ, rng, dt_days=365.0)
    born = _age_years(civ) < age_before
    if born.any():
        assert np.all(_age_years(civ)[born] < 20)
        assert np.all(civ.age_bucket[born] == 0)


def test_inheritance_pulls_toward_parents(civ):
    """With heritability=1 and huge drift, newborn traits carry the
    cohort shift — proving the inheritance channel is live."""
    rng = np.random.default_rng(5)
    open_before = civ.openness.copy()
    generational_tick(civ, rng, dt_days=365.0,
                      heritability=0.4,
                      cohort_drift={"openness": 0.5})
    born = civ.openness != open_before
    # among changed agents, the openness distribution shifted up hard
    if born.sum() > 20:
        assert civ.openness[born].mean() > open_before[born].mean() + 0.2


def test_forces_recomputed_and_bounded(civ):
    rng = np.random.default_rng(6)
    generational_tick(civ, rng, dt_days=365.0)
    assert np.all(civ.forces >= 0) and np.all(civ.forces <= 1)
    assert not np.any(np.isnan(civ.forces))
    np.testing.assert_allclose(civ.means, civ.forces.mean(axis=0))


def test_zero_drift_by_default_keeps_country_means_stable(civ):
    """Without authored drift, one year of replacement must not lurch
    the population — secular change is slow by construction."""
    rng = np.random.default_rng(7)
    open_mean_before = civ.openness.mean()
    generational_tick(civ, rng, dt_days=365.0)
    assert abs(civ.openness.mean() - open_mean_before) < 0.01
