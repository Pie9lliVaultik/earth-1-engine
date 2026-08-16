"""Civilization-scope gate (rule v1-2026-08-16) — semantic tests."""
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from earth1.markets import is_civilization_scope, SCOPE_RULE_VERSION


def _m(question, **kw):
    d = {"question": question, "id": kw.pop("id", question[:20])}
    d.update(kw)
    return d


def test_personal_resolution_rejected(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ok, reason = is_civilization_scope(
        _m("Will I vote in the Michigan primary this month?"))
    assert not ok and reason == "personal_resolution"


def test_market_meta_rejected(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ok, reason = is_civilization_scope(
        _m("Will anyone help me find an edge forecasting Zambian "
           "elections by question close."))
    assert not ok and reason in ("market_meta", "personal_resolution")


def test_us_token_protected(monkeypatch):
    """'US' the country must not trip the 'us' pronoun rule."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ok, reason = is_civilization_scope(
        _m("Will US impose new tariffs on Spain by end of July 2026?"))
    assert ok, f"US-token protection failed: {reason}"


def test_thin_market_rejected(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ok, reason = is_civilization_scope(
        _m("Will the parliament pass the housing bill?",
           uniqueBettorCount=3))
    assert not ok and reason == "thin_market"


def test_gate_is_not_a_miss_launderer(tmp_path):
    """The Klobuchar row (a genuine engine miss) must PASS the gate and
    stay scored — the gate removes out-of-scope rows, never bad ones."""
    q = ("Will Amy Klobuchar win all state legislative districts in the "
         "2026 DFL Governor primary?")
    fake_resp = mock.Mock()
    fake_resp.content = [mock.Mock(text="AGGREGATE")]
    with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
         mock.patch("anthropic.Anthropic") as A:
        A.return_value.messages.create.return_value = fake_resp
        ok, reason = is_civilization_scope(
            _m(q, uniqueBettorCount=50, volume=5000),
            cache_path=str(tmp_path / "cache.json"))
    assert ok and reason == "scope_aggregate"


def test_natural_fails_scope(tmp_path):
    """Divergence from the draft, deliberate: the behavioral-response
    claim covers human reaction, not geophysics."""
    fake_resp = mock.Mock()
    fake_resp.content = [mock.Mock(text="NATURAL")]
    with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
         mock.patch("anthropic.Anthropic") as A:
        A.return_value.messages.create.return_value = fake_resp
        ok, reason = is_civilization_scope(
            _m("Will the volcano erupt before March?",
               uniqueBettorCount=50, volume=5000),
            cache_path=str(tmp_path / "cache.json"))
    assert not ok and reason == "scope_natural"


def test_tier2_cache_one_call(tmp_path):
    fake_resp = mock.Mock()
    fake_resp.content = [mock.Mock(text="INSTITUTION")]
    cache = str(tmp_path / "cache.json")
    with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
         mock.patch("anthropic.Anthropic") as A:
        A.return_value.messages.create.return_value = fake_resp
        m = _m("Will the court strike down the ban?",
               id="fixed-id", uniqueBettorCount=50, volume=5000)
        is_civilization_scope(m, cache_path=cache)
        is_civilization_scope(m, cache_path=cache)
        assert A.return_value.messages.create.call_count == 1
    cached = json.loads(Path(cache).read_text())
    assert cached["fixed-id"]["class"] == "INSTITUTION"


def test_no_key_degrades_open(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ok, reason = is_civilization_scope(
        _m("Will the government resign over the scandal?",
           uniqueBettorCount=50, volume=5000))
    assert ok and reason == "tier2_skipped"


def test_rule_version_pinned():
    assert SCOPE_RULE_VERSION == "v1-2026-08-16"
