"""Tests for the narration module (mock LLM, no live calls)."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from earth1.narration import _build_data_block, narrate, NARRATION_PROMPT
from earth1.types import RunResult, Question, CohortCell, CampAnatomy, Force, NUM_FORCES
from earth1.engine import build_civilization, run_question
from earth1.questions import question_by_id


def _make_result():
    civ = build_civilization(5_000, seed=42)
    q = question_by_id("ssm")
    return run_question(q, civ)


class TestBuildDataBlock:
    def test_contains_question(self):
        r = _make_result()
        block = _build_data_block(r)
        assert "QUESTION:" in block
        assert r.question.text in block

    def test_contains_yes_pct(self):
        r = _make_result()
        block = _build_data_block(r)
        assert "YES %" in block

    def test_contains_force_anatomy(self):
        r = _make_result()
        block = _build_data_block(r)
        assert "FORCE ANATOMY" in block
        assert "identity" in block.lower()

    def test_contains_camps(self):
        r = _make_result()
        block = _build_data_block(r)
        assert "YES CAMP" in block
        assert "NO CAMP" in block

    def test_country_splits_included(self):
        r = _make_result()
        cells = [
            CohortCell(key="0", label="US", n=1000, yes_pct=0.71, dominant=Force.IDENTITY),
            CohortCell(key="1", label="NG", n=800, yes_pct=0.12, dominant=Force.CULTURE),
        ]
        block = _build_data_block(r, country_splits=cells)
        assert "COUNTRY SPLITS" in block
        assert "US" in block
        assert "NG" in block

    def test_temporal_context_included(self):
        r = _make_result()
        block = _build_data_block(r, temporal_context="post-2024 US election")
        assert "TEMPORAL CONTEXT" in block
        assert "post-2024 US election" in block

    def test_no_temporal_context_omitted(self):
        r = _make_result()
        block = _build_data_block(r, temporal_context="")
        assert "TEMPORAL CONTEXT" not in block


class TestNarrateMocked:
    def test_narrate_anthropic_returns_dict(self):
        r = _make_result()

        mock_anthropic = MagicMock()
        mock_block = MagicMock()
        mock_block.type = "tool_use"
        mock_block.name = "narrate"
        mock_block.input = {
            "narration": "Identity drives SSM support at 55%.",
            "headline": "Identity leads the charge on marriage equality",
            "cited_forces": ["identity", "culture"],
        }
        mock_resp = MagicMock()
        mock_resp.content = [mock_block]
        mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_resp

        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = narrate(r, provider="anthropic")

        assert result["narration"] == "Identity drives SSM support at 55%."
        assert result["headline"] == "Identity leads the charge on marriage equality"
        assert "identity" in result["cited_forces"]

    def test_narrate_openai_returns_dict(self):
        r = _make_result()

        import json
        mock_openai = MagicMock()
        mock_tc = MagicMock()
        mock_tc.function.name = "narrate"
        mock_tc.function.arguments = json.dumps({
            "narration": "Culture and identity battle it out.",
            "headline": "Culture vs identity on SSM",
            "cited_forces": ["culture", "identity"],
        })
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.tool_calls = [mock_tc]
        mock_openai.OpenAI.return_value.chat.completions.create.return_value = mock_resp

        with patch.dict("sys.modules", {"openai": mock_openai}):
            result = narrate(r, provider="openai")

        assert "Culture" in result["narration"]


class TestNarrationPrompt:
    def test_law_2_in_prompt(self):
        assert "LAW 2" in NARRATION_PROMPT
        assert "ONLY cite causes" in NARRATION_PROMPT

    def test_prompt_mentions_force_names(self):
        assert "force names" in NARRATION_PROMPT.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
