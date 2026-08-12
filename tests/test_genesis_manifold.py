"""Tests for genesis manifold — run all questions, validate, freeze."""
import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from earth1.genesis_manifold import (
    run_all_questions, compute_holdout_mae, compute_training_mae,
    freeze_genesis_manifold, save_frozen_manifold, QuestionResult,
)
from earth1.genesis import genesis
from earth1.holdout import HOLDOUT_IDS
from earth1.questions import QUESTIONS
from earth1.db.models import Base, ManifoldVersion, HoldoutResult
from earth1.db.store import (
    compute_pop_hash, save_manifold, save_agent_batch,
    get_manifold, list_manifolds,
)
from earth1.engine import build_genesis_civilization


@pytest.fixture(scope="module")
def civ():
    return genesis(pop=10_000, seed=42, min_per_country=10)


@pytest.fixture(scope="module")
def results(civ):
    return run_all_questions(civ)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestRunAllQuestions:
    def test_all_belief_causal_covered(self, results):
        belief_ids = {q.id for q in QUESTIONS if q.domain == "belief_causal"}
        result_ids = {r.id for r in results}
        assert belief_ids == result_ids

    def test_rain_excluded(self, results):
        ids = {r.id for r in results}
        assert "rain" not in ids

    def test_holdout_flagged(self, results):
        for r in results:
            if r.id in HOLDOUT_IDS:
                assert r.is_holdout
            else:
                assert not r.is_holdout

    def test_yes_pct_bounded(self, results):
        for r in results:
            assert 0 <= r.yes_pct <= 1, f"{r.id}: yes_pct={r.yes_pct}"

    def test_dominant_valid(self, results):
        from earth1.types import Force
        valid = {f.name for f in Force}
        for r in results:
            assert r.dominant in valid, f"{r.id}: dominant={r.dominant}"

    def test_conviction_positive(self, results):
        for r in results:
            assert r.conviction >= 0, f"{r.id}: conviction={r.conviction}"


class TestMAE:
    def test_holdout_mae_bounded(self, results):
        mae = compute_holdout_mae(results)
        assert 0 <= mae < 0.5

    def test_training_mae_bounded(self, results):
        mae = compute_training_mae(results)
        assert 0 <= mae < 0.5

    def test_empty_holdout(self):
        results = [QuestionResult("x", "test", "belief_causal", 0.5, "FEAR", 0.8, 0.1, False)]
        assert compute_holdout_mae(results) == 0.0


class TestFreezeManifold:
    def test_report_structure(self):
        report = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        assert report.pop >= 4_900
        assert report.seed == 42
        assert report.country_count == 194
        assert len(report.pop_hash) == 64
        assert len(report.results) >= 27
        assert isinstance(report.holdout_mae, float)
        assert isinstance(report.training_mae, float)

    def test_calibration_runs(self):
        report = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        assert len(report.calibration) > 0
        for cal in report.calibration:
            assert "id" in cal
            assert "weights" in cal

    def test_deterministic(self):
        r1 = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        r2 = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        assert r1.pop_hash == r2.pop_hash
        for a, b in zip(r1.results, r2.results):
            assert abs(a.yes_pct - b.yes_pct) < 1e-10


class TestSaveFrozenManifold:
    def test_save_and_retrieve(self, db_session):
        report = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        mv_id = save_frozen_manifold(report, db_session)
        assert mv_id is not None

        mv = get_manifold(db_session, mv_id)
        assert mv.kind == "frozen"
        assert mv.country_count == 194
        assert mv.metadata_["genesis"] is True
        assert mv.metadata_["passed"] == report.passed

    def test_holdout_results_saved(self, db_session):
        report = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        mv_id = save_frozen_manifold(report, db_session)

        hrs = db_session.query(HoldoutResult).filter_by(manifold_id=mv_id).all()
        assert len(hrs) == len(HOLDOUT_IDS)
        for hr in hrs:
            assert hr.question_id in HOLDOUT_IDS

    def test_none_session(self):
        report = freeze_genesis_manifold(pop=5_000, seed=42, min_per_country=10)
        assert save_frozen_manifold(report, None) is None


class TestGenesisManifoldStore:
    def test_save_manifold_genesis(self, db_session):
        civ = build_genesis_civilization(pop=5_000, seed=42, min_per_country=10)
        mv = save_manifold(db_session, civ, kind="frozen")
        assert mv.country_count == 194

    def test_save_agent_batch_genesis(self, db_session):
        civ = build_genesis_civilization(pop=5_000, seed=42, min_per_country=10)
        mv = save_manifold(db_session, civ, kind="frozen")
        n = save_agent_batch(db_session, mv.id, civ, sample_n=50)
        assert n == 50

    def test_pop_hash_deterministic(self):
        civ1 = genesis(pop=5_000, seed=42, min_per_country=10)
        civ2 = genesis(pop=5_000, seed=42, min_per_country=10)
        assert compute_pop_hash(civ1) == compute_pop_hash(civ2)
