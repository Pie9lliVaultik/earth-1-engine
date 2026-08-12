"""Tests for manifold versioning and agent persistence."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from earth1.db.models import Base, ManifoldVersion, AgentSnapshot, HoldoutResult
from earth1.db.store import (
    compute_pop_hash, save_manifold, save_agent_batch,
    get_manifold, list_manifolds, save_holdout_result,
)
from earth1.engine import build_civilization


POP = 1_000
civ = build_civilization(POP, seed=42)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


class TestPopHash:
    def test_deterministic(self):
        h1 = compute_pop_hash(civ)
        h2 = compute_pop_hash(civ)
        assert h1 == h2

    def test_different_seed_different_hash(self):
        civ2 = build_civilization(POP, seed=99)
        assert compute_pop_hash(civ) != compute_pop_hash(civ2)

    def test_hash_is_64_hex_chars(self):
        h = compute_pop_hash(civ)
        assert len(h) == 64
        int(h, 16)  # valid hex


class TestSaveManifold:
    def test_save_and_retrieve(self, db_session):
        mv = save_manifold(db_session, civ, kind="frozen")
        assert mv is not None
        assert mv.kind == "frozen"
        assert mv.population == POP
        assert mv.seed == 42

        loaded = get_manifold(db_session, mv.id)
        assert loaded is not None
        assert loaded.pop_hash == compute_pop_hash(civ)

    def test_list_manifolds(self, db_session):
        save_manifold(db_session, civ, kind="frozen")
        save_manifold(db_session, civ, kind="living")

        all_m = list_manifolds(db_session)
        assert len(all_m) == 2

        frozen = list_manifolds(db_session, kind="frozen")
        assert len(frozen) == 1
        assert frozen[0].kind == "frozen"

    def test_none_session_safe(self):
        assert save_manifold(None, civ) is None
        assert get_manifold(None, "x") is None
        assert list_manifolds(None) == []


class TestAgentBatch:
    def test_save_batch(self, db_session):
        mv = save_manifold(db_session, civ, kind="frozen")
        n = save_agent_batch(db_session, mv.id, civ, sample_n=100)
        assert n == 100

        snaps = db_session.query(AgentSnapshot).filter_by(manifold_id=mv.id).all()
        assert len(snaps) == 100

    def test_snapshot_has_traits(self, db_session):
        mv = save_manifold(db_session, civ, kind="frozen")
        save_agent_batch(db_session, mv.id, civ, sample_n=10)
        snap = db_session.query(AgentSnapshot).first()
        assert "openness" in snap.traits
        assert "neuroticism" in snap.traits
        assert len(snap.forces) == 8
        assert 0 <= snap.alpha <= 1

    def test_snapshot_demographics(self, db_session):
        mv = save_manifold(db_session, civ, kind="frozen")
        save_agent_batch(db_session, mv.id, civ, sample_n=10)
        snap = db_session.query(AgentSnapshot).first()
        assert "age" in snap.demographics
        assert "education" in snap.demographics

    def test_none_session(self):
        assert save_agent_batch(None, "x", civ) == 0


class TestHoldoutResult:
    def test_save_and_query(self, db_session):
        mv = save_manifold(db_session, civ, kind="frozen")
        hr = save_holdout_result(db_session, mv.id, "inflation", 0.65, "economics", 0.82)
        assert hr is not None
        assert hr.question_id == "inflation"
        assert hr.yes_pct == 0.65

    def test_multiple_results(self, db_session):
        mv = save_manifold(db_session, civ, kind="frozen")
        save_holdout_result(db_session, mv.id, "inflation", 0.65, "economics", 0.82)
        save_holdout_result(db_session, mv.id, "nuclear_risk", 0.72, "fear", 0.75)

        results = db_session.query(HoldoutResult).filter_by(manifold_id=mv.id).all()
        assert len(results) == 2

    def test_none_session(self):
        assert save_holdout_result(None, "x", "q", 0.5, "fear", 0.5) is None
