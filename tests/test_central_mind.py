"""Tests for the Central Mind orchestrator (mocked LLM calls)."""
import sys
sys.path.insert(0, ".")

import json
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from earth1.central_mind import think, MindResult
from earth1.engine import build_civilization


POP = 5_000
civ = build_civilization(POP, seed=42)


def _mock_gateway_response(
    baseline=0.35, fear=0, desire=0, economics=0, collective=-1.2,
    identity=3.4, culture=-2.2, experience=-1.6, temperament=0,
    premise_valid=True, domain="belief_causal",
    country_scope="global", temporal_context="", binary_question="Do people support same-sex marriage?",
):
    return {
        "baseline": baseline, "fear": fear, "desire": desire,
        "economics": economics, "collective": collective,
        "identity": identity, "culture": culture,
        "experience": experience, "temperament": temperament,
        "domain": domain, "premise_valid": premise_valid,
        "premise_reason": "" if premise_valid else "External substrate",
        "lens": "culture", "confidence": "forward_estimate",
        "country_scope": country_scope,
        "temporal_context": temporal_context,
        "binary_question": binary_question,
    }


def _mock_narration_response():
    return {
        "narration": "Identity (0.412) drives yes at 55%. Culture (-0.301) pushes back.",
        "headline": "Identity leads, culture resists on SSM",
        "cited_forces": ["identity", "culture"],
    }


def _setup_mocks():
    mock_anthropic = MagicMock()

    gateway_block = MagicMock()
    gateway_block.type = "tool_use"
    gateway_block.name = "estimate_weights"
    gateway_block.input = _mock_gateway_response()

    narration_block = MagicMock()
    narration_block.type = "tool_use"
    narration_block.name = "narrate"
    narration_block.input = _mock_narration_response()

    call_count = {"n": 0}
    def mock_create(**kwargs):
        call_count["n"] += 1
        resp = MagicMock()
        if call_count["n"] == 1:
            resp.content = [gateway_block]
        else:
            resp.content = [narration_block]
        return resp

    mock_anthropic.Anthropic.return_value.messages.create.side_effect = mock_create
    return mock_anthropic


class TestCentralMind:
    def test_think_returns_mind_result(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("Do people support same-sex marriage?", civ, provider="anthropic")

        assert isinstance(mind, MindResult)
        assert not mind.abstained

    def test_think_has_confidence(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("Do people support same-sex marriage?", civ, provider="anthropic")

        assert mind.confidence.regime in ("calibrated", "transitional", "forward_estimate")
        assert 0 <= mind.confidence.similarity <= 1

    def test_think_has_narration(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("Do people support same-sex marriage?", civ, provider="anthropic")

        assert mind.narration is not None
        assert "identity" in mind.narration["cited_forces"]

    def test_think_skip_narration(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think(
                "Do people support same-sex marriage?", civ,
                provider="anthropic", skip_narration=True,
            )

        assert mind.narration is None

    def test_think_country_scope(self):
        mock_anthropic = MagicMock()
        block = MagicMock()
        block.type = "tool_use"
        block.name = "estimate_weights"
        block.input = _mock_gateway_response(country_scope="DE")

        narr_block = MagicMock()
        narr_block.type = "tool_use"
        narr_block.name = "narrate"
        narr_block.input = _mock_narration_response()

        call_count = {"n": 0}
        def mock_create(**kwargs):
            call_count["n"] += 1
            resp = MagicMock()
            resp.content = [block] if call_count["n"] == 1 else [narr_block]
            return resp

        mock_anthropic.Anthropic.return_value.messages.create.side_effect = mock_create

        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("What do Germans think about SSM?", civ, provider="anthropic")

        assert mind.country_scope == "DE"

    def test_think_temporal_context(self):
        mock_anthropic = MagicMock()
        block = MagicMock()
        block.type = "tool_use"
        block.name = "estimate_weights"
        block.input = _mock_gateway_response(temporal_context="post-2024 US election")

        narr_block = MagicMock()
        narr_block.type = "tool_use"
        narr_block.name = "narrate"
        narr_block.input = _mock_narration_response()

        call_count = {"n": 0}
        def mock_create(**kwargs):
            call_count["n"] += 1
            resp = MagicMock()
            resp.content = [block] if call_count["n"] == 1 else [narr_block]
            return resp

        mock_anthropic.Anthropic.return_value.messages.create.side_effect = mock_create

        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think(
                "After the 2024 election, do Americans trust their government?",
                civ, provider="anthropic",
            )

        assert mind.temporal_context == "post-2024 US election"

    def test_think_premise_invalid(self):
        mock_anthropic = MagicMock()
        block = MagicMock()
        block.type = "tool_use"
        block.name = "estimate_weights"
        block.input = _mock_gateway_response(
            premise_valid=False, domain="external_substrate",
            binary_question="Will it rain tomorrow?",
        )
        resp = MagicMock()
        resp.content = [block]
        mock_anthropic.Anthropic.return_value.messages.create.return_value = resp

        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("Will it rain tomorrow?", civ, provider="anthropic")

        assert mind.abstained
        assert mind.narration is None
        assert mind.confidence.regime == "forward_estimate"

    def test_think_result_has_yes_pct(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("Do people support same-sex marriage?", civ, provider="anthropic")

        assert 0 <= mind.result.yes_pct <= 1

    def test_think_country_splits_populated(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("Do people support same-sex marriage?", civ, provider="anthropic")

        assert mind.country_splits is not None
        assert len(mind.country_splits) == 9

    def test_think_binary_question_preserved(self):
        mock_anthropic = _setup_mocks()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}), \
             patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            mind = think("What do people think about gay marriage?", civ, provider="anthropic")

        assert mind.binary_question == "Do people support same-sex marriage?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
