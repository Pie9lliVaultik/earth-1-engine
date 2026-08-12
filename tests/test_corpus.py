"""Tests for the Phase 3 retrieval corpus (bible §19.1)."""
import numpy as np
import pytest

from earth1.corpus import QuestionCorpus, CorpusHit, DEFAULT_MIN_SIM
from earth1.types import NUM_FORCES


def _make_corpus():
    c = QuestionCorpus()
    texts = [
        "Do people support same-sex marriage?",
        "Should immigration be more restricted?",
        "Is your money safe at your bank right now?",
        "Do people trust the national government?",
        "Do people trust the national parliament?",
    ]
    n = len(texts)
    rng = np.random.default_rng(0)
    weights = rng.normal(0, 1, (n, NUM_FORCES))
    # make the two "trust" questions weight-consistent (a coherent region)
    weights[4] = weights[3] + rng.normal(0, 0.05, NUM_FORCES)
    c.build(
        ids=[f"q{i}" for i in range(n)], texts=texts,
        baselines=np.zeros(n), weights=weights,
    )
    return c


def test_build_and_len():
    c = _make_corpus()
    assert len(c) == 5
    assert c.matrix.shape[1] > 0


def test_exact_duplicate_retrieves_directly():
    c = _make_corpus()
    hit = c.retrieve("Do people support same-sex marriage?")
    assert hit is not None
    assert hit.id == "q0"
    assert hit.similarity >= 0.995


def test_novel_question_routes_to_llm():
    c = _make_corpus()
    hit = c.retrieve("Should the moon be declared a nature reserve?")
    assert hit is None


def test_consensus_required_for_non_exact():
    c = _make_corpus()
    # near-duplicate of a coherent region (the two trust questions agree)
    hit = c.retrieve("Do people trust the national government today?",
                     min_sim=0.5, min_weight_agreement=0.8)
    # if it fires, it must return blended weights near the region's weights
    if hit is not None:
        cos = (hit.weights @ c.weights[3]) / (
            np.linalg.norm(hit.weights) * np.linalg.norm(c.weights[3]))
        assert cos > 0.8


def test_disagreeing_neighbourhood_abstains():
    c = QuestionCorpus()
    texts = [
        "What is your opinion of the United States?",
        "What is your opinion of the Russian Federation?",
        "What is your opinion of the European Union?",
    ]
    rng = np.random.default_rng(1)
    # same stem, contradictory weights — must NOT reuse
    weights = np.stack([rng.normal(0, 1, NUM_FORCES) for _ in range(3)])
    weights[1] = -weights[0]
    c.build(ids=["a", "b", "c"], texts=texts,
            baselines=np.zeros(3), weights=weights)
    hit = c.retrieve("What is your opinion of the Chinese government?",
                     min_sim=0.5, min_weight_agreement=0.8)
    assert hit is None


def test_save_load_roundtrip(tmp_path):
    c = _make_corpus()
    c.save(tmp_path / "corpus_test")
    c2 = QuestionCorpus.load(tmp_path / "corpus_test")
    assert len(c2) == len(c)
    h1 = c.retrieve("Do people support same-sex marriage?")
    h2 = c2.retrieve("Do people support same-sex marriage?")
    assert h1.id == h2.id
    assert abs(h1.similarity - h2.similarity) < 1e-12
    np.testing.assert_allclose(h1.weights, h2.weights)


def test_add_grows_corpus():
    c = _make_corpus()
    c.add(id="new1", text="Do people fear artificial intelligence?",
          baseline=0.1, weights=np.ones(NUM_FORCES), source="llm")
    assert len(c) == 6
    hit = c.retrieve("Do people fear artificial intelligence?")
    assert hit is not None
    assert hit.id == "new1"
    assert hit.source == "llm"


def test_hit_to_question():
    c = _make_corpus()
    hit = c.retrieve("Do people support same-sex marriage?")
    q = hit.to_question(qid="custom")
    assert q.id == "custom"
    assert q.weights.shape == (NUM_FORCES,)
