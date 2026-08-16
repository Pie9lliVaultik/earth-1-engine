"""The world's daily news read — channel discipline tests."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from earth1.daily_news import read_todays_news, READ_COUNTRIES, PER_DAY
from earth1.news_perception import perceive_item_stub


FAKE_ARTS = [
    {"title": "Economic crisis deepens as markets tumble worldwide",
     "date": "20260816"},
    {"title": "Local pie contest draws record crowd in village fair",
     "date": "20260816"},
]


def _fake_fetcher(name):
    return list(FAKE_ARTS)


def test_rotation_is_deterministic_in_day():
    cohort_a = [READ_COUNTRIES[(5 * PER_DAY + i) % len(READ_COUNTRIES)]
                for i in range(PER_DAY)]
    cohort_b = [READ_COUNTRIES[(5 * PER_DAY + i) % len(READ_COUNTRIES)]
                for i in range(PER_DAY)]
    assert cohort_a == cohort_b


def test_rotation_covers_all_countries():
    seen = set()
    n_days = len(READ_COUNTRIES) // PER_DAY
    for day in range(n_days):
        for i in range(PER_DAY):
            seen.add(READ_COUNTRIES[(day * PER_DAY + i) % len(READ_COUNTRIES)][0])
    assert seen == {cc for cc, _ in READ_COUNTRIES}


def test_events_scoped_to_country():
    events = read_todays_news(day=0, t=10.0, perceiver=perceive_item_stub,
                              fetcher=_fake_fetcher, progress=False)
    assert events, "stub perceives the crisis headline"
    for ev in events:
        cc = ev.region_pattern.split("-")[0]
        assert len(cc) == 2
        assert ev.region_pattern == f"{cc}-*"


def test_event_timestamps_are_world_time():
    events = read_todays_news(day=0, t=42.0, perceiver=perceive_item_stub,
                              fetcher=_fake_fetcher, progress=False)
    assert all(ev.timestamp == 42.0 for ev in events)


def test_abstentions_ledgered_never_dropped(tmp_path):
    ledger = tmp_path / "abstentions.jsonl"
    read_todays_news(day=0, t=0.0, perceiver=perceive_item_stub,
                     fetcher=_fake_fetcher, ledger_path=ledger,
                     progress=False)
    rows = [json.loads(l) for l in ledger.read_text().splitlines()]
    outcomes = {r["outcome"] for r in rows}
    # the pie-contest headline has no stub keyword -> abstained
    assert "abstained" in outcomes
    assert "perceived" in outcomes
    # every fetched headline is accounted for
    assert len(rows) == PER_DAY * len(FAKE_ARTS)


def test_scope_overrides_publisher_country():
    """A ZA outlet carrying a NATO/Latvia wire story must scope the
    event to the concerned population, not to South Africa — the bug
    the world's first live read surfaced (2026-08-16)."""
    from earth1.news_perception import PerceivedEvent, NewsItem
    from earth1.types import Force

    def scoped_perceiver(item):
        return PerceivedEvent(
            item, {Force.FEAR.value: 0.1}, 0.7, 14.0,
            rationale="wire story", scope="LV",
        ).clipped()

    events = read_todays_news(day=0, t=0.0, perceiver=scoped_perceiver,
                              fetcher=_fake_fetcher, progress=False)
    assert all(ev.region_pattern == "LV-*" for ev in events)


def test_global_scope_reaches_everyone():
    from earth1.news_perception import PerceivedEvent
    from earth1.types import Force

    def global_perceiver(item):
        return PerceivedEvent(
            item, {Force.FEAR.value: 0.1}, 0.8, 30.0, scope="GLOBAL",
        ).clipped()

    events = read_todays_news(day=0, t=0.0, perceiver=global_perceiver,
                              fetcher=_fake_fetcher, progress=False)
    assert all(ev.region_pattern == "*" for ev in events)


def test_parse_none_scope_abstains():
    from earth1.news_perception import _parse_perception, NewsItem
    item = NewsItem(title="x", country="ZA", date="2026-08-16")
    out = _parse_perception(item, {
        "force_deltas": {"fear": 0.1}, "confidence": 0.9,
        "concerns": "NONE",
    })
    assert out is None


def test_parse_malformed_scope_falls_back_to_publisher():
    from earth1.news_perception import _parse_perception, NewsItem
    item = NewsItem(title="x", country="BR", date="2026-08-16")
    out = _parse_perception(item, {
        "force_deltas": {"fear": 0.1}, "confidence": 0.9,
        "concerns": "not-a-code",
    })
    assert out is not None and out.scope == "BR"


def test_empty_fetch_ledgered(tmp_path):
    ledger = tmp_path / "abstentions.jsonl"
    events = read_todays_news(day=0, t=0.0, perceiver=perceive_item_stub,
                              fetcher=lambda name: [], ledger_path=ledger,
                              progress=False)
    assert events == []
    rows = [json.loads(l) for l in ledger.read_text().splitlines()]
    assert all(r["outcome"] == "fetch_empty" for r in rows)
    assert len(rows) == PER_DAY
