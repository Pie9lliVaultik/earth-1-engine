"""Tests for genesis integration into the engine — Build 14."""
import numpy as np
import pytest

from earth1.engine import (
    build_genesis_civilization, run_question, run_segment,
    civ_breakdown, _is_genesis, build_civilization,
)
from earth1.genesis import GENESIS_COUNTRIES
from earth1.questions import QUESTIONS
from earth1.types import Force


@pytest.fixture(scope="module")
def gciv():
    return build_genesis_civilization(pop=10_000, seed=42, min_per_country=10)


@pytest.fixture(scope="module")
def lciv():
    return build_civilization(pop=10_000, seed=42)


class TestGenesisDetection:
    def test_genesis_detected(self, gciv):
        assert _is_genesis(gciv)

    def test_legacy_not_detected(self, lciv):
        assert not _is_genesis(lciv)


class TestBuildGenesisCache:
    def test_caching(self):
        c1 = build_genesis_civilization(pop=5000, seed=77, min_per_country=10)
        c2 = build_genesis_civilization(pop=5000, seed=77, min_per_country=10)
        assert c1 is c2

    def test_different_params_different_civ(self):
        c1 = build_genesis_civilization(pop=5000, seed=77, min_per_country=10)
        c2 = build_genesis_civilization(pop=5000, seed=78, min_per_country=10)
        assert c1 is not c2


class TestRunQuestionGenesis:
    def test_basic_run(self, gciv):
        q = QUESTIONS[0]
        result = run_question(q, gciv)
        assert 0 <= result.yes_pct <= 1
        assert result.dominant in list(Force)
        assert result.n == gciv.n

    def test_multiple_questions(self, gciv):
        for q in QUESTIONS[:5]:
            result = run_question(q, gciv)
            assert 0 <= result.yes_pct <= 1


class TestRunSegmentGenesis:
    def test_segment_by_country(self, gciv):
        cells = run_segment(QUESTIONS[0], gciv, "country")
        assert len(cells) > 50
        codes = {c.label for c in cells}
        assert "US" in codes
        assert "IN" in codes

    def test_segment_by_age(self, gciv):
        cells = run_segment(QUESTIONS[0], gciv, "age_bucket")
        assert len(cells) >= 3
        labels = {c.label for c in cells}
        assert "18-29" in labels

    def test_segment_by_education(self, gciv):
        cells = run_segment(QUESTIONS[0], gciv, "education")
        labels = {c.label for c in cells}
        assert labels.issubset({"low", "mid", "high"})

    def test_segment_by_income(self, gciv):
        cells = run_segment(QUESTIONS[0], gciv, "income")
        labels = {c.label for c in cells}
        assert labels.issubset({"low", "mid", "high"})


class TestCivBreakdownGenesis:
    def test_breakdown_194_countries(self, gciv):
        bd = civ_breakdown(gciv)
        assert len(bd) == 194
        codes = {b["code"] for b in bd}
        assert "IN" in codes
        assert "US" in codes

    def test_breakdown_sums_to_n(self, gciv):
        bd = civ_breakdown(gciv)
        total = sum(b["n"] for b in bd)
        assert total == gciv.n

    def test_breakdown_sorted_descending(self, gciv):
        bd = civ_breakdown(gciv)
        ns = [b["n"] for b in bd]
        assert ns == sorted(ns, reverse=True)

    def test_legacy_breakdown_still_works(self, lciv):
        bd = civ_breakdown(lciv)
        assert len(bd) == len(set(b["code"] for b in bd))
        total = sum(b["n"] for b in bd)
        assert total == lciv.n
