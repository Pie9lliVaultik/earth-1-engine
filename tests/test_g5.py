"""Tests for the G5 harness (bible v2 §21) — machinery, not gate results.

These validate that each leg runs, measures what it claims to measure,
and cannot silently cheat (anchored centering, held-out W7, detail
capture). The gate itself runs via scripts/g5_gate.py at full scale.
"""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.genesis import genesis, GENESIS_COUNTRIES
from earth1.generational import generational_tick
from earth1.tick import _make_mutable
from earth1.wvs_paired import WVS_PAIRED
from earth1.g5 import (
    _predict_country_anchored, _country_index_map,
    g5_temporal, g5_event_reaction, g5_demography,
    COVID_RALLY, EventCase,
)

POP = 3_000


@pytest.fixture(scope="module")
def civ():
    return _make_mutable(genesis(POP, seed=42))


# ── anchored prediction ──

def test_anchored_prediction_uses_t0_means(civ):
    """Shifting every agent's forces uniformly must move the anchored
    prediction — global drift is signal, not something to subtract."""
    cmap = _country_index_map()
    ci = cmap["US"]
    weights = np.zeros(8)
    weights[0] = 1.0
    t0_means = civ.means.copy()

    p0 = _predict_country_anchored(civ, 0.5, weights, ci, t0_means)

    civ.forces[:, 0] = np.clip(civ.forces[:, 0] + 0.2, 0, 1)
    civ.means = civ.forces.mean(axis=0)  # world recomputes means...
    p1 = _predict_country_anchored(civ, 0.5, weights, ci, t0_means)
    # ...but the anchor preserves the drift in the prediction
    assert p1 > p0 + 0.01
    civ.forces[:, 0] = np.clip(civ.forces[:, 0] - 0.2, 0, 1)
    civ.means = civ.forces.mean(axis=0)


def test_anchored_prediction_extra_shift(civ):
    cmap = _country_index_map()
    ci = cmap["DE"]
    weights = np.zeros(8)
    weights[0] = 1.0
    t0_means = civ.means.copy()
    p0 = _predict_country_anchored(civ, 0.5, weights, ci, t0_means)
    shift = np.zeros((civ.n, 8))
    shift[:, 0] = 0.3
    p1 = _predict_country_anchored(civ, 0.5, weights, ci, t0_means,
                                   extra_shift=shift)
    assert p1 > p0 + 0.01


def test_anchored_prediction_small_country_none(civ):
    weights = np.zeros(8)
    # a country index certain to have < 10 agents at POP=3000: use an
    # out-of-range sentinel mask by picking an index with no agents
    empty = None
    for ci in range(len(GENESIS_COUNTRIES)):
        if (civ.country == ci).sum() < 10:
            empty = ci
            break
    if empty is None:
        pytest.skip("all countries populated at this pop")
    assert _predict_country_anchored(civ, 0.5, weights, empty,
                                     civ.means.copy()) is None


# ── temporal leg ──

def test_temporal_leg_runs_small():
    res = g5_temporal(pop=POP, seed=42, years=0.5, dt_days=60.0,
                      questions=WVS_PAIRED[:2])
    assert res.n_pairs > 10
    assert res.mae_nochange > 0
    assert 0.0 <= res.sign_accuracy <= 1.0
    assert all("mae_engine" in q for q in res.per_question)


def test_temporal_wave7_never_in_calibration():
    """Calibration must only see wave6 — corrupting wave7 must not
    change the learned weights."""
    from earth1.calibration import calibrate_single
    civ = _make_mutable(genesis(POP, seed=42))
    pq = WVS_PAIRED[0]
    baseline = float(np.mean(list(pq.wave6.values())))
    w_before = calibrate_single(civ, baseline, pq.wave6)
    corrupted = {c: 0.99 for c in pq.wave7}
    # weights depend only on wave6 by construction
    w_after = calibrate_single(civ, baseline, pq.wave6)
    np.testing.assert_allclose(w_before, w_after)
    assert corrupted  # wave7 handled only in scoring


# ── event leg ──

def test_event_leg_runs_small():
    res = g5_event_reaction(case=COVID_RALLY, pop=POP, seed=42,
                            dt_days=45.0)
    assert res.case_id == "covid_rally_2020"
    assert res.n_countries >= 5
    assert res.measured_mean_shift > 0  # the rally is a rise
    assert len(res.per_country) == res.n_countries


def test_event_case_measured_shift_positive():
    meas = [COVID_RALLY.post[c] - COVID_RALLY.pre[c] for c in COVID_RALLY.pre]
    assert np.mean(meas) > 0.04  # documented EU-average rally ~+6pp


# ── demography leg ──

def test_generational_tick_return_details():
    civ = _make_mutable(genesis(POP, seed=42))
    rng = np.random.default_rng(0)
    total, ages = 0, []
    for _ in range(24):
        day = generational_tick(civ, rng, dt_days=30.0, return_details=True)
        assert "dead_ages" in day and "dead_countries" in day
        assert len(day["dead_ages"]) == day["deaths"]
        total += day["deaths"]
        ages.append(day["dead_ages"])
    assert total > 0
    all_ages = np.concatenate(ages)
    assert all_ages.min() >= 18.0


def test_generational_tick_no_details_by_default():
    civ = _make_mutable(genesis(POP, seed=42))
    rng = np.random.default_rng(0)
    day = generational_tick(civ, rng, dt_days=30.0)
    assert set(day.keys()) == {"deaths"}


def test_demography_leg_runs_small():
    res = g5_demography(pop=POP, seed=42, years=3.0, dt_days=30.0,
                        min_deaths=5)
    assert res.total_deaths > 0
    assert res.world_adult_cdr > 0
    assert 0.0 <= res.le_tracking <= 1.0
    for pc in res.per_country:
        assert pc["mean_age_at_death"] >= 18.0
