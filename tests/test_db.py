"""Tests for the persistence layer using SQLite in-memory."""
import sys
sys.path.insert(0, ".")

import os
import pytest
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite://"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from earth1.db.models import Base, Run, Prediction, Outcome
from earth1.db.store import (
    save_run, save_prediction, record_outcome,
    list_runs, get_run,
    list_predictions, get_prediction,
    prediction_accuracy, expire_predictions,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSaveRun:
    def test_creates_run(self, db):
        run = save_run(
            db,
            run_type="mind",
            question_text="Do people support SSM?",
            yes_pct=0.58,
            frac_yes=0.62,
            dominant="identity",
        )
        assert run is not None
        assert run.id is not None
        assert run.yes_pct == 0.58
        assert run.run_type == "mind"

    def test_run_has_timestamp(self, db):
        run = save_run(
            db, run_type="mind",
            question_text="Test", yes_pct=0.5,
            frac_yes=0.5, dominant="fear",
        )
        assert run.created_at is not None
        assert isinstance(run.created_at, datetime)

    def test_run_stores_metadata(self, db):
        run = save_run(
            db, run_type="mind",
            question_text="Do people trust government?",
            binary_question="Do people trust their national government?",
            question_id="gov_trust",
            country_scope="US",
            temporal_context="post-2024 election",
            yes_pct=0.20,
            frac_yes=0.25,
            dominant="economics",
            conviction=0.45,
            fragility=0.32,
            confidence_regime="transitional",
            confidence_similarity=0.72,
            force_anatomy={"economics": 0.35, "identity": 0.28},
            parameters={"epsilon": 0.18, "layers": 8},
            narration={"headline": "Economics drives distrust"},
        )
        assert run.country_scope == "US"
        assert run.temporal_context == "post-2024 election"
        assert run.force_anatomy["economics"] == 0.35
        assert run.narration["headline"] == "Economics drives distrust"

    def test_none_session_returns_none(self):
        assert save_run(None, run_type="x", question_text="x", yes_pct=0, frac_yes=0, dominant="x") is None


class TestListRuns:
    def test_list_returns_runs(self, db):
        save_run(db, run_type="mind", question_text="Q1", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        save_run(db, run_type="mind", question_text="Q2", yes_pct=0.6, frac_yes=0.6, dominant="identity")
        runs = list_runs(db)
        assert len(runs) == 2

    def test_list_filters_by_type(self, db):
        save_run(db, run_type="mind", question_text="Q1", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        save_run(db, run_type="timeline", question_text="Q2", yes_pct=0.6, frac_yes=0.6, dominant="identity")
        mind_runs = list_runs(db, run_type="mind")
        assert len(mind_runs) == 1
        assert mind_runs[0].run_type == "mind"

    def test_list_respects_limit(self, db):
        for i in range(10):
            save_run(db, run_type="mind", question_text=f"Q{i}", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        runs = list_runs(db, limit=5)
        assert len(runs) == 5

    def test_get_run_by_id(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        found = get_run(db, run.id)
        assert found is not None
        assert found.question_text == "Test"

    def test_get_run_not_found(self, db):
        assert get_run(db, "nonexistent") is None

    def test_none_session(self):
        assert list_runs(None) == []
        assert get_run(None, "x") is None


class TestPredictions:
    def test_create_prediction(self, db):
        run = save_run(db, run_type="mind", question_text="SSM?", yes_pct=0.58, frac_yes=0.62, dominant="identity",
                       confidence_regime="calibrated", confidence_similarity=0.87)
        pred = save_prediction(
            db, run_id=run.id,
            question_text="SSM?",
            predicted_yes_pct=0.58,
            confidence_regime="calibrated",
            horizon_days=90,
        )
        assert pred is not None
        assert pred.predicted_yes_pct == 0.58
        assert pred.status == "open"
        assert pred.target_date > datetime.utcnow()

    def test_prediction_with_country(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        pred = save_prediction(
            db, run_id=run.id,
            question_text="Test",
            predicted_yes_pct=0.71,
            confidence_regime="calibrated",
            horizon_days=30,
            country_code="US",
        )
        assert pred.country_code == "US"

    def test_prediction_with_tags(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        pred = save_prediction(
            db, run_id=run.id,
            question_text="Test",
            predicted_yes_pct=0.5,
            confidence_regime="forward_estimate",
            horizon_days=180,
            tags=["culture", "ssm"],
        )
        assert "culture" in pred.tags

    def test_list_predictions(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        save_prediction(db, run_id=run.id, question_text="A", predicted_yes_pct=0.5,
                        confidence_regime="calibrated", horizon_days=30)
        save_prediction(db, run_id=run.id, question_text="B", predicted_yes_pct=0.6,
                        confidence_regime="transitional", horizon_days=60)
        preds = list_predictions(db)
        assert len(preds) == 2

    def test_list_predictions_filter_status(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        save_prediction(db, run_id=run.id, question_text="A", predicted_yes_pct=0.5,
                        confidence_regime="calibrated", horizon_days=30)
        open_preds = list_predictions(db, status="open")
        assert len(open_preds) == 1
        resolved_preds = list_predictions(db, status="resolved")
        assert len(resolved_preds) == 0

    def test_none_session(self):
        assert save_prediction(None, run_id="x", question_text="x", predicted_yes_pct=0,
                               confidence_regime="x", horizon_days=0) is None
        assert list_predictions(None) == []


class TestOutcomes:
    def test_record_outcome(self, db):
        run = save_run(db, run_type="mind", question_text="SSM?", yes_pct=0.58, frac_yes=0.62, dominant="identity")
        pred = save_prediction(db, run_id=run.id, question_text="SSM?", predicted_yes_pct=0.58,
                               confidence_regime="calibrated", horizon_days=90)
        outcome = record_outcome(db, prediction_id=pred.id, actual_yes_pct=0.55, source="Pew 2024")
        assert outcome is not None
        assert outcome.error == pytest.approx(0.03, abs=0.001)
        assert outcome.source == "Pew 2024"

        pred_refreshed = get_prediction(db, pred.id)
        assert pred_refreshed.status == "resolved"

    def test_outcome_bad_prediction_id(self, db):
        with pytest.raises(ValueError, match="not found"):
            record_outcome(db, prediction_id="nonexistent", actual_yes_pct=0.5, source="test")

    def test_none_session(self):
        assert record_outcome(None, prediction_id="x", actual_yes_pct=0, source="x") is None


class TestAccuracy:
    def test_accuracy_with_outcomes(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.58, frac_yes=0.62, dominant="identity")
        pred = save_prediction(db, run_id=run.id, question_text="Test", predicted_yes_pct=0.58,
                               confidence_regime="calibrated", horizon_days=90)
        record_outcome(db, prediction_id=pred.id, actual_yes_pct=0.55, source="survey")

        acc = prediction_accuracy(db)
        assert acc["enabled"]
        assert acc["n_resolved"] == 1
        assert acc["mean_error"] is not None
        assert acc["mean_error"] == pytest.approx(0.03, abs=0.001)
        assert "calibrated" in acc["by_regime"]

    def test_accuracy_empty(self, db):
        acc = prediction_accuracy(db)
        assert acc["enabled"]
        assert acc["n_resolved"] == 0
        assert acc["mean_error"] is None

    def test_accuracy_disabled(self):
        acc = prediction_accuracy(None)
        assert not acc["enabled"]


class TestExpire:
    def test_expire_past_predictions(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        pred = save_prediction(db, run_id=run.id, question_text="Test", predicted_yes_pct=0.5,
                               confidence_regime="calibrated", horizon_days=1)
        pred.target_date = datetime.utcnow() - timedelta(days=1)
        db.commit()

        n = expire_predictions(db)
        assert n == 1

        pred_refreshed = get_prediction(db, pred.id)
        assert pred_refreshed.status == "expired"

    def test_expire_future_not_touched(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        save_prediction(db, run_id=run.id, question_text="Test", predicted_yes_pct=0.5,
                        confidence_regime="calibrated", horizon_days=365)
        n = expire_predictions(db)
        assert n == 0

    def test_none_session(self):
        assert expire_predictions(None) == 0


class TestRunPredictionRelationship:
    def test_run_has_predictions(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        save_prediction(db, run_id=run.id, question_text="Test", predicted_yes_pct=0.5,
                        confidence_regime="calibrated", horizon_days=30)
        save_prediction(db, run_id=run.id, question_text="Test", predicted_yes_pct=0.5,
                        confidence_regime="calibrated", horizon_days=90)

        run_loaded = get_run(db, run.id)
        assert len(run_loaded.predictions) == 2

    def test_prediction_has_outcomes(self, db):
        run = save_run(db, run_type="mind", question_text="Test", yes_pct=0.5, frac_yes=0.5, dominant="fear")
        pred = save_prediction(db, run_id=run.id, question_text="Test", predicted_yes_pct=0.5,
                               confidence_regime="calibrated", horizon_days=30)
        record_outcome(db, prediction_id=pred.id, actual_yes_pct=0.48, source="survey1")
        record_outcome(db, prediction_id=pred.id, actual_yes_pct=0.52, source="survey2")

        pred_loaded = get_prediction(db, pred.id)
        assert len(pred_loaded.outcomes) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
