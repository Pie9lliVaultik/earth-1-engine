"""Tests for the confidence scoring module."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.confidence import score_confidence, _cosine, _keyword_overlap, _content_tokens
from earth1.types import Question
from earth1.benchmark import BENCHMARK_QUESTIONS
from earth1.questions import _w


class TestHelpers:
    def test_cosine_identical(self):
        a = np.array([1.0, 2.0, 3.0])
        assert abs(_cosine(a, a) - 1.0) < 1e-6

    def test_cosine_orthogonal(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert abs(_cosine(a, b)) < 1e-6

    def test_cosine_opposite(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert abs(_cosine(a, b) + 1.0) < 1e-6

    def test_cosine_zero_vector(self):
        a = np.zeros(3)
        b = np.array([1.0, 2.0, 3.0])
        assert _cosine(a, b) == 0.0

    def test_keyword_overlap_identical(self):
        assert _keyword_overlap("same-sex marriage", "same-sex marriage") == 1.0

    def test_keyword_overlap_none(self):
        assert _keyword_overlap("cats and dogs", "economics finance budget") == 0.0

    def test_content_tokens_strips_stop_words(self):
        tokens = _content_tokens("Do people support same-sex marriage?")
        assert "do" not in tokens
        assert "people" not in tokens
        assert "support" in tokens


class TestScoreConfidence:
    def test_benchmark_question_scores_high(self):
        bq = BENCHMARK_QUESTIONS[0]
        q = bq.to_question()
        score = score_confidence(q)
        assert score.similarity >= 0.85
        assert score.regime == "calibrated"
        assert score.nearest_id == bq.id

    def test_similar_question_scores_transitional_or_higher(self):
        q = Question(
            id="test_ssm_variant",
            text="Should gay couples be allowed to marry?",
            domain="belief_causal",
            baseline=0.3,
            weights=_w(identity=3.0, culture=-2.0, collective=-1.0, experience=-1.5),
            lens="culture",
        )
        score = score_confidence(q)
        assert score.similarity >= 0.5

    def test_unrelated_question_scores_low(self):
        q = Question(
            id="test_aliens",
            text="Do aliens exist on Mars?",
            domain="belief_causal",
            baseline=0.0,
            weights=_w(fear=4.0),
            lens="space",
        )
        score = score_confidence(q)
        assert score.regime == "forward_estimate"

    def test_all_benchmark_self_score_calibrated(self):
        for bq in BENCHMARK_QUESTIONS:
            q = bq.to_question()
            score = score_confidence(q)
            assert score.similarity >= 0.85, f"{bq.id} self-score only {score.similarity}"

    def test_regime_boundaries(self):
        q_high = BENCHMARK_QUESTIONS[0].to_question()
        score = score_confidence(q_high)
        assert score.regime in ("calibrated", "transitional", "forward_estimate")

    def test_returns_nearest_text(self):
        q = Question(
            id="test", text="Test", domain="belief_causal",
            baseline=0.0, weights=np.zeros(8),
        )
        score = score_confidence(q)
        assert len(score.nearest_text) > 0
        assert len(score.nearest_id) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
