"""Tests for the LLM gateway — weight estimation from free text.

Uses mock LLM responses to test the parsing/integration pipeline.
Set ANTHROPIC_API_KEY to also run live integration tests.
"""
import sys
sys.path.insert(0, ".")

import os
import json
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from earth1.llm_gateway import (
    estimate, _parse_tool_input, _slug, GatewayResult, SYSTEM_PROMPT, WEIGHT_TOOL,
)
from earth1.types import Force, NUM_FORCES


def _mock_tool_input(**overrides):
    base = {
        "baseline": 0.3,
        "fear": -2.0,
        "desire": 1.5,
        "economics": 0.8,
        "collective": 0.0,
        "identity": 2.4,
        "culture": -1.2,
        "experience": 0.0,
        "temperament": 0.6,
        "domain": "belief_causal",
        "premise_valid": True,
        "premise_reason": "",
        "lens": "policy",
        "confidence": "forward_estimate",
    }
    base.update(overrides)
    return base


def test_parse_tool_input_basic():
    data = _mock_tool_input()
    r = _parse_tool_input(data, "Is democracy the best system?")
    assert r.question.id == "is_democracy_the_best_system"
    assert r.question.text == "Is democracy the best system?"
    assert r.question.domain == "belief_causal"
    assert r.question.baseline == 0.3
    assert r.question.weights.shape == (NUM_FORCES,)
    assert r.question.weights[Force.FEAR] == -2.0
    assert r.question.weights[Force.IDENTITY] == 2.4
    assert r.premise_valid is True
    assert r.confidence == "forward_estimate"


def test_parse_tool_input_external_substrate():
    data = _mock_tool_input(
        domain="external_substrate",
        premise_valid=False,
        premise_reason="Weather depends on atmospheric physics, not beliefs.",
        fear=1.0, identity=2.0,
    )
    r = _parse_tool_input(data, "Will it snow in Tokyo tomorrow?")
    assert r.premise_valid is False
    assert "physics" in r.premise_reason
    assert np.all(r.question.weights == 0)


def test_parse_preserves_all_forces():
    data = _mock_tool_input(
        fear=1.1, desire=2.2, economics=3.3, collective=-1.1,
        identity=-2.2, culture=-3.3, experience=0.5, temperament=-0.5,
    )
    r = _parse_tool_input(data, "test q")
    w = r.question.weights
    assert w[0] == 1.1
    assert w[1] == 2.2
    assert w[2] == 3.3
    assert w[3] == -1.1
    assert w[4] == -2.2
    assert w[5] == -3.3
    assert w[6] == 0.5
    assert w[7] == -0.5


def test_slug():
    assert _slug("Will it rain in London tomorrow?") == "will_it_rain_in_london_tomorrow"
    assert _slug("Is AI dangerous??") == "is_ai_dangerous"
    assert _slug("  spaces  ") == "spaces"
    assert _slug("") == "freetext"
    long = "a" * 100
    assert len(_slug(long)) == 60


def test_system_prompt_contains_forces():
    for f in Force:
        assert f.name.lower() in SYSTEM_PROMPT


def test_weight_tool_schema_has_all_forces():
    props = WEIGHT_TOOL["input_schema"]["properties"]
    for f in Force:
        assert f.name.lower() in props


def _make_mock_anthropic_response(data):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "estimate_weights"
    block.input = data
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_estimate_anthropic_mock():
    data = _mock_tool_input()
    mock_resp = _make_mock_anthropic_response(data)

    mock_anthropic = MagicMock()
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = mock_resp

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        from earth1.llm_gateway import estimate_anthropic
        r = estimate_anthropic("Do people trust banks?")

        assert r.question.text == "Do people trust banks?"
        assert r.question.weights[Force.FEAR] == -2.0
        mock_client.messages.create.assert_called_once()


def test_estimate_openai_mock():
    data = _mock_tool_input()

    mock_tc = MagicMock()
    mock_tc.function.name = "estimate_weights"
    mock_tc.function.arguments = json.dumps(data)

    mock_choice = MagicMock()
    mock_choice.message.tool_calls = [mock_tc]
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    mock_client.chat.completions.create.return_value = mock_resp

    with patch.dict("sys.modules", {"openai": mock_openai}):
        from earth1.llm_gateway import estimate_openai
        r = estimate_openai("Do people trust banks?")

        assert r.question.text == "Do people trust banks?"
        assert r.premise_valid is True


def test_estimate_no_key_raises():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(RuntimeError, match="No LLM API key"):
            estimate("anything")


def test_estimate_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        estimate("anything", provider="deepseek")


def test_engine_run_freetext_mock():
    """Full pipeline: mock the LLM, run through the real engine."""
    os.environ["EARTH1_POP"] = "5000"
    data = _mock_tool_input(baseline=0.5, fear=-2.5, identity=2.0)
    mock_resp = _make_mock_anthropic_response(data)

    mock_anthropic = MagicMock()
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = mock_resp

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            from earth1.engine import run_freetext, build_civilization
            civ = build_civilization(5000, seed=42)
            out = run_freetext("Do people trust banks?", civ)

            assert "gateway" in out
            assert "result" in out
            r = out["result"]
            assert r.n == 5000
            assert 0 <= r.yes_pct <= 1
            assert r.abstained is None

            gw = out["gateway"]
            assert gw.premise_valid is True
            assert gw.question.weights[Force.FEAR] == -2.5


def test_engine_run_freetext_abstains_mock():
    """External substrate questions should abstain."""
    data = _mock_tool_input(
        domain="external_substrate",
        premise_valid=False,
        premise_reason="This is a weather question.",
    )
    mock_resp = _make_mock_anthropic_response(data)

    mock_anthropic = MagicMock()
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = mock_resp

    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            from earth1.engine import run_freetext, build_civilization
            civ = build_civilization(5000, seed=42)
            out = run_freetext("Will it rain tomorrow?", civ)

            r = out["result"]
            assert r.abstained is not None
            assert "weather" in r.abstained.lower()


# --- Live integration tests (only run with real API key) ---

@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live LLM test",
)
def test_live_estimate_belief_causal():
    r = estimate("Do people support universal basic income?", provider="anthropic")
    assert r.premise_valid is True
    assert r.question.domain == "belief_causal"
    assert r.question.weights.shape == (NUM_FORCES,)
    nonzero = np.count_nonzero(r.question.weights)
    assert nonzero >= 2, "Expected at least 2 non-zero force weights"


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live LLM test",
)
def test_live_estimate_external_substrate():
    r = estimate("What is the boiling point of water?", provider="anthropic")
    assert r.premise_valid is False
    assert r.question.domain == "external_substrate"
    assert len(r.premise_reason) > 0


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live LLM test",
)
def test_live_full_pipeline():
    from earth1.engine import run_freetext, build_civilization
    civ = build_civilization(5000, seed=42)
    out = run_freetext("Should the voting age be lowered to 16?", civ, provider="anthropic")
    r = out["result"]
    assert r.n == 5000
    assert 0 < r.yes_pct < 1
    gw = out["gateway"]
    assert gw.premise_valid is True
    w = gw.question.weights
    assert np.any(w != 0), "LLM should assign non-zero weights"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
