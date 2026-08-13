"""Tests for standing-record resolution + Force-Outcome Atlas (§20.2)."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from earth1.db.models import Base, Prediction, Outcome, ForceOutcome
from earth1.engine import build_genesis_civilization
from earth1.corpus import QuestionCorpus
from earth1.markets import LiveMarket
from earth1.arming import arm_market
from earth1.resolving import (
    resolve_armed, verify_hash, atlas_report, Resolution,
)
from earth1.types import NUM_FORCES


@pytest.fixture
def db():
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture(scope="module")
def civ():
    return build_genesis_civilization(20_000, seed=42)


@pytest.fixture
def corpus():
    c = QuestionCorpus()
    rng = np.random.default_rng(0)
    c.build(
        ids=["c0", "c1"],
        texts=["Will the incumbent president win the next election?",
               "Will the government coalition survive the year?"],
        baselines=np.array([0.1, -0.2]),
        weights=rng.normal(0, 1, (2, NUM_FORCES)),
    )
    return c


def _arm(db, civ, corpus, question, mid="m1", price=0.6):
    m = LiveMarket(id=mid, source="manifold", question=question,
                   price=price, close_time="2027-01-01T00:00:00+00:00",
                   url="https://example.test/" + mid, volume=100.0)
    return arm_market(db, civ, m, corpus=corpus)


def test_resolution_scores_into_atlas(db, civ, corpus):
    out = _arm(db, civ, corpus,
               "Will the incumbent president win the next election?")
    assert out.status == "armed"

    results = resolve_armed(
        db, fetch=lambda src, mid: Resolution(resolved=True, actual=1.0))
    assert len(results) == 1
    assert results[0].status == "resolved"
    assert results[0].actual == 1.0

    pred = db.query(Prediction).one()
    assert pred.status == "resolved"
    assert db.query(Outcome).count() == 1
    fo = db.query(ForceOutcome).one()
    assert fo.fragility_at_prediction == pred.fragility
    assert fo.error == pytest.approx(abs(pred.predicted_yes_pct - 1.0))


def test_unresolved_stays_open(db, civ, corpus):
    _arm(db, civ, corpus,
         "Will the incumbent president win the next election?")
    results = resolve_armed(db, fetch=lambda s, m: Resolution(resolved=False))
    assert results[0].status == "open"
    assert db.query(Prediction).one().status == "open"
    assert db.query(ForceOutcome).count() == 0


def test_voided_market_never_scored(db, civ, corpus):
    _arm(db, civ, corpus,
         "Will the incumbent president win the next election?")
    results = resolve_armed(
        db, fetch=lambda s, m: Resolution(resolved=True, voided=True))
    assert results[0].status == "voided"
    assert db.query(Prediction).one().status == "voided"
    assert db.query(ForceOutcome).count() == 0


def test_tampered_reading_flagged_not_scored(db, civ, corpus):
    out = _arm(db, civ, corpus,
               "Will the incumbent president win the next election?")
    pred = db.query(Prediction).one()
    assert verify_hash(pred)
    pred.predicted_yes_pct = 0.99  # tamper after arming
    db.commit()
    assert not verify_hash(pred)

    results = resolve_armed(
        db, fetch=lambda s, m: Resolution(resolved=True, actual=1.0))
    assert results[0].status == "tampered"
    assert db.query(Prediction).one().status == "tampered"
    assert db.query(ForceOutcome).count() == 0


def test_atlas_report_scoreboard(db, civ, corpus):
    _arm(db, civ, corpus,
         "Will the incumbent president win the next election?", mid="m1")
    _arm(db, civ, corpus,
         "Will the government coalition survive the year?", mid="m2",
         price=0.3)
    resolve_armed(db, fetch=lambda s, m:
                  Resolution(resolved=True, actual=1.0 if m == "m1" else 0.0))

    report = atlas_report(db)
    assert report["n_resolved"] == 2
    assert 0.0 <= report["engine_brier"] <= 1.0
    assert report["market_brier"] is not None
    assert isinstance(report["engine_beats_price"], bool)


def test_empty_atlas_report(db):
    assert atlas_report(db) == {"n_resolved": 0}
