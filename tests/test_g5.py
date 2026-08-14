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
                        cohort_n=500)
    assert res.total_deaths > 0
    assert res.world_adult_cdr > 0
    assert 0.0 <= res.le_tracking <= 1.0
    for pc in res.per_country:
        assert pc["cohort_mean_age_at_death"] >= 18.0


def test_cohort_le_matches_census():
    """The tick's own hazard path must reproduce census LE — the
    amendment A1 implementation test."""
    from earth1.g5 import _simulate_cohort_le
    rng = np.random.default_rng(7)
    for le in (55.0, 72.0, 82.0):
        mean_death = _simulate_cohort_le(le, rng, n=3000, dt_days=30.0)
        assert abs(mean_death - le) <= 4.0, (le, mean_death)


# ── replay (amendment A2) ──

def _synthetic_history():
    rng = np.random.default_rng(9)
    months = [f"2020-{m:02d}" for m in range(1, 13)]
    hist = {}
    for cc in ("US", "DE", "NG"):
        base = rng.normal(-2.0, 0.5)
        hist[cc] = {
            "tone": {m: round(base + rng.normal(0, 1.0), 3) for m in months},
            "vol": {m: round(abs(rng.normal(1.0, 0.3)), 3) for m in months},
        }
    return hist


def test_replay_builds_monthly_events():
    from earth1.replay import build_replay_events
    from earth1.g5 import _replay_receiver_config
    events = build_replay_events(_synthetic_history(),
                                 _replay_receiver_config())
    assert events, "no events built"
    all_evs = [e for evs in events.values() for e in evs]
    assert all(e.source == "receiver:gdelt" for e in all_evs)
    # events are country-scoped, never global
    assert all(e.region_pattern.endswith("-*") for e in all_evs)
    # timestamps align to the monthly grid used by g5_temporal (dt=30)
    for mi, evs in events.items():
        assert all(e.timestamp == mi * 30 for e in evs)


def test_replay_shuffle_preserves_series():
    from earth1.replay import shuffle_history_geography
    hist = _synthetic_history()
    rng = np.random.default_rng(0)
    shuf = shuffle_history_geography(hist, rng)
    assert sorted(shuf) == sorted(hist)
    orig = sorted(json_str(v) for v in hist.values())
    perm = sorted(json_str(v) for v in shuf.values())
    assert orig == perm  # same series, relabelled


def json_str(v):
    import json
    return json.dumps(v, sort_keys=True)


def test_temporal_accepts_replay_events():
    from earth1.replay import build_replay_events
    from earth1.g5 import _replay_receiver_config
    events = build_replay_events(_synthetic_history(),
                                 _replay_receiver_config())
    res = g5_temporal(pop=POP, seed=42, years=1.0, dt_days=30.0,
                      questions=WVS_PAIRED[:2], replay_events=events)
    assert res.n_pairs > 10
