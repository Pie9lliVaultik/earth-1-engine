"""Tests for the living world — bifurcation, persistence, drift guard (§21.2, §34)."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.living import LivingWorld, pop_hash, _DRIFT_TRAITS
from earth1.types import Question
from earth1.calibration import calibrate_single
from earth1.rng import logit

POP = 5_000
SEED = 7


@pytest.fixture(scope="module")
def questions():
    w = np.array([1.5, 0.0, 0.8, -0.5, 1.2, -0.9, 0.3, 0.0])
    return [Question(id="lw_q", text="Do people trust their institutions?",
                     domain="belief_causal", baseline=0.1, weights=w, lens="wvs")]


def test_create_persists_to_disk(tmp_path):
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    assert (tmp_path / "world" / "civ.npz").exists()
    assert (tmp_path / "world" / "adj.npz").exists()
    assert (tmp_path / "world" / "world.json").exists()
    assert w.meta["frozen_pop_hash"] == w.meta["living_pop_hash"]  # not yet ticked


def test_load_is_same_world(tmp_path):
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    h = pop_hash(w.state.civ)
    w2 = LivingWorld.load(tmp_path / "world")
    assert pop_hash(w2.state.civ) == h
    assert w2.state.tick_count == 0
    assert w2.state.civ.n == POP


def test_tick_evolves_and_persists(tmp_path, questions):
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    frozen_hash = w.meta["frozen_pop_hash"]
    w.tick(questions, days=3, use_force_dynamics=True,
           residue_rate=0.01, enable_rewire=False,
           enable_event_generation=False)
    assert w.state.tick_count == 3
    # the living copy has diverged from the frozen anchor
    assert pop_hash(w.state.civ) != frozen_hash

    w2 = LivingWorld.load(tmp_path / "world")
    assert w2.state.tick_count == 3
    assert pop_hash(w2.state.civ) == pop_hash(w.state.civ)
    assert w2.meta["frozen_pop_hash"] == frozen_hash  # anchor unchanged


def test_deterministic_continuation(tmp_path, questions):
    """Tick 2 days in one life = tick 1, die, reload, tick 1."""
    kw = dict(use_force_dynamics=True, residue_rate=0.01,
              enable_rewire=False, enable_event_generation=False)

    a = LivingWorld.create(tmp_path / "a", pop=POP, seed=SEED)
    a.tick(questions, days=2, **kw)

    b = LivingWorld.create(tmp_path / "b", pop=POP, seed=SEED)
    b.tick(questions, days=1, **kw)
    b2 = LivingWorld.load(tmp_path / "b")
    b2.tick(questions, days=1, **kw)

    assert pop_hash(a.state.civ) == pop_hash(b2.state.civ)
    assert a.state.t == b2.state.t


def test_event_log_survives_reload(tmp_path):
    from earth1.event_log import WorldEvent
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    w.state.event_log.append(WorldEvent.create(
        timestamp=1.0, force_deltas={0: 0.3}, source="test"))
    w.save()
    w2 = LivingWorld.load(tmp_path / "world")
    assert len(w2.state.event_log) == 1
    e = w2.state.event_log.events()[0]
    assert e.force_deltas == {"fear": 0.3}
    assert e.source == "test"


def test_drift_report_zero_at_birth(tmp_path):
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    report = w.drift_report()
    assert report
    assert all(v["max_abs"] < 1e-12 for v in report.values())


def test_re_anchor_pulls_back_drifted_cell(tmp_path):
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    civ = w.state.civ
    c = int(civ.country[0])
    mask = civ.country == c
    civ.openness[mask] = np.clip(civ.openness[mask] + 0.2, 0, 1)  # heavy drift

    before = w.drift_report()[str(c)]["openness"]
    assert before > 0.05

    fixed = w.re_anchor(tolerance=0.05)
    assert fixed >= 1
    after = w.drift_report()[str(c)]["openness"]
    assert abs(after) <= 0.06  # back inside tolerance (clip slack)
    # variance preserved: agents not collapsed to a point
    assert civ.openness[mask].std() > 0.05


def test_question_history_survives_reload(tmp_path):
    """Re-audit: reload dropped question_history, giving the endogenous
    detectors amnesia. The scalar skeleton must survive."""
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    from earth1.questions import QUESTIONS
    qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:2]
    w.tick(qs, days=2)
    assert len(w.state.question_history) >= 2
    w2 = LivingWorld.load(tmp_path / "world")
    assert len(w2.state.question_history) >= 2
    latest = list(w2.state.question_history[-1].values())[0]
    assert 0.0 <= latest.yes_pct <= 1.0


def test_coupling_matrix_rebuilt_at_tick(tmp_path):
    """Re-audit: the persistent world ran with coupling permanently
    empty. Ticking with 2+ coupled questions must populate it."""
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    from earth1.questions import QUESTIONS
    qs = [q for q in QUESTIONS if q.domain != "external_substrate"][:4]
    assert w.state.coupling_matrix == {}
    w.tick(qs, days=1)
    assert len(w.state.coupling_matrix) > 0, \
        "coupling matrix still empty after ticking coupled questions"


def test_pop_hash_full_sees_alpha_and_graph(tmp_path):
    """Re-audit: v1 hash (forces only) was blind to alpha and edge
    changes that alter output. v2 must see both."""
    from earth1.living import pop_hash, pop_hash_full
    w = LivingWorld.create(tmp_path / "world", pop=POP, seed=SEED)
    civ = w.state.civ
    h1_before, h2_before = pop_hash(civ), pop_hash_full(civ)
    civ.alpha[0] += 0.1
    assert pop_hash(civ) == h1_before          # v1 blindness, documented
    assert pop_hash_full(civ) != h2_before     # v2 sees it
    h2_alpha = pop_hash_full(civ)
    civ.adj = civ.adj.tolil()
    civ.adj[0, 1] = 0.5
    assert pop_hash_full(civ) != h2_alpha      # v2 sees graph changes
