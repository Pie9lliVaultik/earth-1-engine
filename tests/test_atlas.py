"""Tests for standing record (armed predictions) and Force-Outcome Atlas."""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from earth1.db.models import Base, Prediction, Run, ForceOutcome
from earth1.db.store import (
    save_run, save_prediction, arm_prediction,
    resolve_with_atlas, query_atlas,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def _make_run(session):
    return save_run(
        session,
        run_type="mind",
        question_text="Test question",
        yes_pct=0.65,
        frac_yes=0.65,
        dominant="economics",
        conviction=0.8,
        fragility=0.3,
        force_anatomy={"economics": 0.4, "fear": 0.2, "identity": 0.15,
                       "culture": 0.1, "collective": 0.05, "desire": 0.05,
                       "experience": 0.03, "temperament": 0.02},
    )


class TestArmPrediction:
    def test_arm_creates_hash(self, db_session):
        run = _make_run(db_session)
        pred = save_prediction(
            db_session, run.id, "Test question", 0.65, "forward_estimate", 90)
        armed = arm_prediction(db_session, pred.id)
        assert armed.armed is True
        assert armed.armed_at is not None
        assert armed.prediction_hash is not None
        assert len(armed.prediction_hash) == 64

    def test_arm_is_idempotent_error(self, db_session):
        run = _make_run(db_session)
        pred = save_prediction(
            db_session, run.id, "Test", 0.65, "forward_estimate", 90)
        arm_prediction(db_session, pred.id)
        with pytest.raises(ValueError, match="already armed"):
            arm_prediction(db_session, pred.id)

    def test_arm_nonexistent_raises(self, db_session):
        with pytest.raises(ValueError, match="not found"):
            arm_prediction(db_session, "nonexistent")

    def test_none_session(self):
        assert arm_prediction(None, "x") is None


class TestResolveWithAtlas:
    def test_resolve_creates_atlas_entry(self, db_session):
        run = _make_run(db_session)
        pred = save_prediction(
            db_session, run.id, "Test question", 0.65, "forward_estimate", 90)
        pred.force_anatomy = {"economics": 0.4, "fear": 0.3}
        pred.fragility = 0.3
        db_session.commit()

        fo = resolve_with_atlas(db_session, pred.id, 0.62, "poll")
        assert fo is not None
        assert fo.dominant_force == "economics"
        assert fo.predicted_yes_pct == 0.65
        assert fo.actual_yes_pct == 0.62
        assert abs(fo.error - 0.03) < 0.001

    def test_resolve_updates_prediction_status(self, db_session):
        run = _make_run(db_session)
        pred = save_prediction(
            db_session, run.id, "Test", 0.65, "forward_estimate", 90)
        resolve_with_atlas(db_session, pred.id, 0.70, "survey")
        db_session.refresh(pred)
        assert pred.status == "resolved"

    def test_none_session(self):
        assert resolve_with_atlas(None, "x", 0.5, "s") is None


class TestQueryAtlas:
    def test_query_all(self, db_session):
        run = _make_run(db_session)
        for i in range(3):
            pred = save_prediction(
                db_session, run.id, f"Q{i}", 0.5 + i * 0.1, "forward_estimate", 90)
            pred.force_anatomy = {"fear": 0.5, "economics": 0.3}
            pred.fragility = 0.1 * (i + 1)
            db_session.commit()
            resolve_with_atlas(db_session, pred.id, 0.55, "poll")

        results = query_atlas(db_session)
        assert len(results) == 3

    def test_query_by_dominant(self, db_session):
        run = _make_run(db_session)

        pred1 = save_prediction(db_session, run.id, "Q1", 0.5, "forward_estimate", 90)
        pred1.force_anatomy = {"fear": 0.6, "economics": 0.2}
        pred1.fragility = 0.2
        db_session.commit()
        resolve_with_atlas(db_session, pred1.id, 0.55, "poll")

        pred2 = save_prediction(db_session, run.id, "Q2", 0.7, "forward_estimate", 90)
        pred2.force_anatomy = {"economics": 0.5, "fear": 0.3}
        pred2.fragility = 0.1
        db_session.commit()
        resolve_with_atlas(db_session, pred2.id, 0.68, "poll")

        fear_entries = query_atlas(db_session, dominant_force="fear")
        assert len(fear_entries) == 1
        assert fear_entries[0].dominant_force == "fear"

    def test_query_by_min_fragility(self, db_session):
        run = _make_run(db_session)
        for frag in [0.1, 0.3, 0.5]:
            pred = save_prediction(db_session, run.id, f"Q{frag}", 0.5, "forward_estimate", 90)
            pred.force_anatomy = {"fear": 0.5}
            pred.fragility = frag
            db_session.commit()
            resolve_with_atlas(db_session, pred.id, 0.55, "poll")

        results = query_atlas(db_session, min_fragility=0.25)
        assert len(results) == 2

    def test_none_session(self):
        assert query_atlas(None) == []
