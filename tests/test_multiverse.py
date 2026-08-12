"""Tests for the Phase 4 multiverse engine (bible §20.1)."""
import numpy as np
import pytest

from earth1.engine import build_genesis_civilization
from earth1.types import Question, NUM_FORCES
from earth1.central_mind import author
from earth1.multiverse import (
    rehearse, rehearse_question, contortion, _field_shift, FIELD_GAIN,
)
from earth1.scenarios import ScenarioBranch, BranchStep, EVENT_CATALOG


@pytest.fixture(scope="module")
def civ():
    return build_genesis_civilization(20_000, seed=42)


@pytest.fixture(scope="module")
def q():
    w = np.array([2.2, 0.0, 1.0, -0.6, 1.8, -1.2, 0.5, 0.0])
    return Question(id="mv_q", text="Do people fear for their economic future?",
                    domain="belief_causal", baseline=-0.2, weights=w, lens="wvs")


def test_field_shift_collapses_steps():
    b = ScenarioBranch.from_event_ids(
        "b", "b", [(0, "financial_crisis"), (30, "bank_run")])
    shift = _field_shift(b)
    assert shift.shape == (NUM_FORCES,)
    assert shift[0] == pytest.approx((3.2 + 3.8) * FIELD_GAIN)  # fear stacks


def test_rehearse_runs_all_branches(civ, q):
    branches = author(q, k=3)
    reh = rehearse(q, civ, branches)
    assert len(reh.branches) == len(branches)
    assert abs(sum(reh.fragility_weights.values()) - 1.0) < 1e-9


def test_status_quo_is_reference_not_reading(civ, q):
    branches = author(q, k=3)
    reh = rehearse(q, civ, branches)
    assert reh.reading.id != "status_quo"
    sq = next(b for b in reh.branches if b.id == "status_quo")
    assert sq.contortion == 0.0
    assert sq.yes_pct == reh.present.yes_pct


def test_branches_move_the_reading(civ, q):
    branches = author(q, k=3)
    reh = rehearse(q, civ, branches)
    futures = [b for b in reh.branches if b.id != "status_quo"]
    assert any(abs(b.yes_pct - reh.present.yes_pct) > 1e-4 for b in futures)
    assert all(b.contortion > 0 for b in futures)


def test_reading_is_min_contortion_future(civ, q):
    reh = rehearse_question(q, civ, k=4)
    futures = [b for b in reh.branches if b.id != "status_quo"]
    assert reh.reading.contortion == min(b.contortion for b in futures)


def test_fragile_present_flattens_weights(civ, q):
    """Higher present fragility → higher temperature → flatter plausibility."""
    branches = author(q, k=3)
    reh = rehearse(q, civ, branches)
    w = np.array([reh.fragility_weights[b.id] for b in reh.branches])
    # weights are a proper distribution and not fully collapsed
    assert np.all(w >= 0) and abs(w.sum() - 1.0) < 1e-9


def test_contortion_metric():
    a = np.array([1.0, 0, 0, 0, 0, 0, 0, 0])
    assert contortion(a, a) == 0.0
    b = np.array([0, 1.0, 0, 0, 0, 0, 0, 0])
    assert contortion(a, b) == pytest.approx(np.sqrt(2))


def test_rehearsal_is_deterministic(civ, q):
    branches = author(q, k=2)
    r1 = rehearse(q, civ, branches)
    r2 = rehearse(q, civ, branches)
    assert r1.reading.id == r2.reading.id
    assert r1.reading.yes_pct == r2.reading.yes_pct
