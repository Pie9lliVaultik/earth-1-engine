"""Phase 5.8 pipeline tests — perception machinery, stub only.

The live LLM path needs ANTHROPIC_API_KEY (rotated) and is exercised
by scripts, not tests. These prove the pipeline's discipline: clipping,
confidence floor, channel-off-without-key, stub tagging.
"""
import sys
sys.path.insert(0, ".")

import os
import numpy as np
import pytest

from earth1.types import Force
from earth1.news_perception import (
    NewsItem, PerceivedEvent, perceive_item, perceive_item_stub,
    events_from_news, _parse_perception, _MAX_DELTA,
)


def _item(title="War breaks out", country="UA"):
    return NewsItem(title=title, country=country, date="2022-02-24")


def test_channel_off_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert perceive_item(_item()) is None  # off, never a silent fallback


def test_stub_perceives_and_is_tagged():
    ev = perceive_item_stub(_item("War breaks out"))
    assert ev is not None
    assert ev.rationale == "STUB"
    assert ev.force_deltas[Force.FEAR.value] > 0


def test_stub_declines_irrelevant():
    assert perceive_item_stub(_item("Local bakery wins pie contest")) is None


def test_parse_clips_magnitude_and_decay():
    ev = _parse_perception(_item(), {
        "force_deltas": {"fear": 0.9, "economics": -0.7},
        "confidence": 0.8, "decay_half_life_days": 500,
    })
    assert ev is not None
    assert abs(ev.force_deltas[Force.FEAR.value]) <= _MAX_DELTA
    assert abs(ev.force_deltas[Force.ECONOMICS.value]) <= _MAX_DELTA
    assert ev.decay_half_life <= 90.0


def test_parse_drops_low_confidence():
    assert _parse_perception(_item(), {
        "force_deltas": {"fear": 0.1}, "confidence": 0.1,
    }) is None


def test_parse_drops_empty_deltas():
    assert _parse_perception(_item(), {
        "force_deltas": {}, "confidence": 0.9,
    }) is None


def test_events_from_news_country_scoped():
    items = [_item("War breaks out", "UA"),
             _item("Economy in crisis", "AR"),
             _item("Pie contest", "US")]
    events = events_from_news(items, t=10.0, perceiver=perceive_item_stub)
    assert len(events) == 2  # pie contest declined
    assert all(e.region_pattern.endswith("-*") for e in events)
    assert all(e.source == "perception:stub" for e in events)
    assert all(e.timestamp == 10.0 for e in events)


def test_events_gain_scales():
    items = [_item("War breaks out", "UA")]
    e1 = events_from_news(items, t=0.0, gain=1.0,
                          perceiver=perceive_item_stub)[0]
    e2 = events_from_news(items, t=0.0, gain=0.5,
                          perceiver=perceive_item_stub)[0]
    assert abs(e2.force_deltas["fear"] - 0.5 * e1.force_deltas["fear"]) < 1e-9
