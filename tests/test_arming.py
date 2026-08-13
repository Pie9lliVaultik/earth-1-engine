"""Tests for the standing-record arming pipeline (bible §20.2)."""
import sys
sys.path.insert(0, ".")

import os
import numpy as np
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from earth1.db.models import Base, Run, Prediction
from earth1.engine import build_genesis_civilization
from earth1.corpus import QuestionCorpus
from earth1.markets import LiveMarket, is_belief_causal, horizon_days
from earth1.arming import arm_market, perceive
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
        ids=["c0"],
        texts=["Will the incumbent president win the next election?"],
        baselines=np.array([0.1]),
        weights=rng.normal(0, 1, (1, NUM_FORCES)),
    )
    return c


def _mk(question, price=0.6):
    return LiveMarket(id="m1", source="manifold", question=question,
                      price=price, close_time="2027-01-01T00:00:00+00:00",
                      url="https://example.test/m1", volume=1000.0)


def test_belief_causal_filter():
    assert is_belief_causal("Will the president win the election?")
    assert not is_belief_causal("Will Bitcoin close above $100k?")
    assert not is_belief_causal("Will the Lakers win the NBA finals?")


def test_horizon_days_from_close_time():
    m = _mk("Will the election be contested?")
    assert 1 <= horizon_days(m) <= 3650


def test_perceive_corpus_hit(corpus):
    q = perceive("Will the incumbent president win the next election?", corpus)
    assert q is not None
    assert q.weights.shape[0] >= NUM_FORCES


def test_perceive_abstains_without_sources(corpus, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    q = perceive("A completely novel unheard-of proposition?", corpus)
    assert q is None


def test_arm_market_precommits(db, civ, corpus):
    m = _mk("Will the incumbent president win the next election?")
    out = arm_market(db, civ, m, corpus=corpus)
    assert out.status == "armed"
    assert out.prediction_hash and len(out.prediction_hash) == 64

    pred = db.query(Prediction).one()
    assert pred.armed is True
    assert pred.armed_at is not None
    assert pred.fragility == out.fragility
    run = db.query(Run).filter_by(run_type="armed_reading").one()
    assert run.gateway_raw["price_at_arming"] == 0.6
    assert run.gateway_raw["reading_branch"] not in ("", "status_quo")
    assert len(run.gateway_raw["branches"]) >= 2


def test_abstention_is_ledgered_never_scored(db, civ, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    m = _mk("Will an entirely novel policy proposition pass the parliament?")
    out = arm_market(db, civ, m, corpus=None)
    assert out.status == "abstained"
    # ledgered: a Run row exists; never scored: no Prediction row
    assert db.query(Run).filter_by(run_type="armed_abstention").count() == 1
    assert db.query(Prediction).count() == 0


def test_rearming_is_blocked(db, civ, corpus):
    m = _mk("Will the incumbent president win the next election?")
    out = arm_market(db, civ, m, corpus=corpus)
    from earth1.db.store import arm_prediction
    with pytest.raises(ValueError, match="already armed"):
        arm_prediction(db, out.prediction_id)
