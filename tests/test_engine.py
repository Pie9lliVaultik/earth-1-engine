"""Engine integration tests — verify the civilization produces sane results."""
import sys
sys.path.insert(0, ".")

import numpy as np
from earth1.engine import build_civilization, run_question, run_segment, run_multiverse, civ_breakdown
from earth1.questions import QUESTIONS, question_by_id
from earth1.types import Force, PERISHABILITY_HALF_LIFE
from earth1.superposition import born_readout, sequential_measurement
from earth1.perishability import decay_curve
from earth1.cube import build_cube, aggregate_read
from earth1.calibration import calibrate_weights

POP = 10_000
civ = build_civilization(POP, seed=42)


def test_population_size():
    assert civ.n == POP
    assert civ.forces.shape == (POP, 8)
    assert civ.alpha.shape == (POP,)
    assert civ.means.shape == (8,)


def test_forces_bounded():
    assert civ.forces.min() >= 0.0
    assert civ.forces.max() <= 1.0


def test_alpha_bounded():
    assert civ.alpha.min() >= 0.0
    assert civ.alpha.max() <= 1.0


def test_graph_structure():
    from scipy import sparse
    assert sparse.issparse(civ.adj)
    assert civ.adj.shape == (POP, POP)
    assert civ.adj.nnz > POP * 4


def test_svb_high_yes():
    q = question_by_id("svb")
    r = run_question(q, civ)
    assert r.yes_pct > 0.7, f"SVB should be high-yes, got {r.yes_pct}"
    assert r.dominant == Force.FEAR


def test_ssm_identity_dominant():
    q = question_by_id("ssm")
    r = run_question(q, civ)
    assert r.dominant == Force.IDENTITY
    assert 0.4 < r.yes_pct < 0.75


def test_rain_abstains():
    q = question_by_id("rain")
    r = run_question(q, civ)
    assert r.abstained is not None
    assert "not the cause" in r.abstained.lower()


def test_segment_country():
    q = question_by_id("ssm")
    cells = run_segment(q, civ, "country")
    assert len(cells) == 50
    total = sum(c.n for c in cells)
    assert total == POP


def test_segment_age():
    q = question_by_id("ssm")
    cells = run_segment(q, civ, "age_bucket")
    assert len(cells) == 5
    assert cells[0].label == "18-29"


def test_multiverse():
    q = question_by_id("svb")
    mv = run_multiverse(q, civ)
    assert mv["present"].yes_pct > 0.5
    assert len(mv["branches"]) == 2
    assert all(b.contortion >= 0 for b in mv["branches"])


def test_breakdown():
    bd = civ_breakdown(civ)
    assert len(bd) == 50
    assert sum(c["n"] for c in bd) == POP


def test_born_readout():
    q = question_by_id("ssm")
    p = born_readout(civ, q)
    assert p.shape == (POP,)
    assert 0 <= p.min() <= p.max() <= 1


def test_order_effect():
    q1 = question_by_id("ssm")
    q2 = question_by_id("ai_trust")
    result = sequential_measurement(civ, q1, q2)
    assert "order_effect_q2" in result
    assert isinstance(result["order_effect_q2"], float)


def test_decay_curve():
    curve = decay_curve(0.87, Force.FEAR)
    assert curve["half_life_days"] == 14
    assert curve["actual"][0] == 0.87
    # fear-dominant decays fast — should be closer to 0.5 after 2 years
    assert curve["actual"][-1] < curve["durable_baseline"][-1]


def test_cube_aggregate():
    q = question_by_id("svb")
    r = run_question(q, civ)
    from earth1.forces import project_all
    from earth1.diffusion import diffuse
    s0 = project_all(civ, q)
    snaps = diffuse(s0, civ.alpha, civ.adj, 0.18, 8)
    cube = build_cube(civ, q, snaps[-1])
    agg = aggregate_read(cube)
    assert agg["n"] == POP
    assert abs(agg["yes_pct"] - r.yes_pct) < 0.01


def test_calibration():
    targets = [
        {"id": "test_ssm", "text": "SSM", "domain": "belief_causal", "target_yes_pct": 0.62},
    ]
    results = calibrate_weights(civ, targets)
    assert len(results) == 1
    assert results[0]["error"] < 0.1


def test_reproducibility():
    civ2 = build_civilization(POP, seed=42)
    np.testing.assert_array_equal(civ.forces, civ2.forces)
    np.testing.assert_array_equal(civ.alpha, civ2.alpha)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])


class TestWorldReadsAreEventAware:
    """Re-audit P0 (2026-08-16): /ask answered 58.9% while the event-
    aware world read said 83.4% — same Earth, same moment. Civilization
    is the population substrate; WorldState is Earth-1. Every read path
    must consult the event log at world time."""

    def test_run_question_sees_active_events(self):
        import numpy as np
        from earth1.engine import run_question, build_genesis_civilization
        from earth1.event_log import EventLog, WorldEvent
        from earth1.questions import QUESTIONS
        civ = build_genesis_civilization(5000, seed=3)
        q = next(x for x in QUESTIONS if x.domain != "external_substrate")
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"fear": 0.2, "collective": 0.15},
            region_pattern="*", decay_half_life=60.0))
        blind = run_question(q, civ)
        aware = run_question(q, civ, event_log=log, t=1.0)
        assert abs(aware.yes_pct - blind.yes_pct) > 1e-4, \
            "active event invisible to run_question"

    def test_run_segment_sees_active_events(self):
        from earth1.engine import run_segment, build_genesis_civilization
        from earth1.event_log import EventLog, WorldEvent
        from earth1.questions import QUESTIONS
        civ = build_genesis_civilization(5000, seed=3)
        q = next(x for x in QUESTIONS if x.domain != "external_substrate")
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"fear": 0.25, "collective": 0.2,
                                          "economics": -0.15},
            region_pattern="*", decay_half_life=60.0))
        blind = run_segment(q, civ, "income")
        aware = run_segment(q, civ, "income", event_log=log, t=1.0)
        diffs = [abs(a.yes_pct - b.yes_pct)
                 for a, b in zip(aware, blind)]
        assert max(diffs) > 1e-4, "active event invisible to run_segment"

    def test_ask_route_reads_the_world(self):
        """The route itself: inject into THE WorldState, /ask must move."""
        import os
        from fastapi.testclient import TestClient
        prev_pop = os.environ.get("EARTH1_POP")
        os.environ["EARTH1_POP"] = "4000"
        from earth1.api import deps
        deps.reset_civ()
        from earth1.api.main import app
        from earth1.event_log import WorldEvent
        client = TestClient(app)
        from earth1.questions import QUESTIONS
        qid = next(x.id for x in QUESTIONS if x.domain != "external_substrate")
        before = client.get(f"/ask?q={qid}").json()["yes_pct"]
        state = deps.get_world_state()
        state.event_log.append(WorldEvent.create(
            timestamp=state.t, force_deltas={"fear": 0.25, "collective": 0.2},
            region_pattern="*", decay_half_life=60.0))
        state.t += 1.0
        after = client.get(f"/ask?q={qid}").json()["yes_pct"]
        # restore the environment — leaking EARTH1_POP=4000 broke later
        # API tests expecting 5000 (re-audit: order-dependent suite)
        if prev_pop is None:
            os.environ.pop("EARTH1_POP", None)
        else:
            os.environ["EARTH1_POP"] = prev_pop
        deps.reset_civ()
        assert abs(after - before) > 1e-4, \
            "/ask is event-blind — it reads the substrate, not the world"
