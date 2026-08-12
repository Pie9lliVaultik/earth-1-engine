"""Tests for event generation — the model feeding back into itself."""
import numpy as np
import pytest

from earth1.event_generation import (
    detect_polarization,
    detect_consensus,
    detect_opinion_reversal,
    detect_cascade,
    detect_emergent_events,
    _bimodality,
)
from earth1.event_log import EventLog, WorldEvent
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.questions import QUESTIONS
from earth1.types import RunResult, Force, NUM_FORCES


@pytest.fixture(scope="module")
def civ():
    return genesis(pop=5_000, seed=42, min_per_country=10)


def _make_result(yes_pct=0.5, conviction=0.5, fragility=0.3, qid="test"):
    q = QUESTIONS[0]
    return RunResult(
        question=q, n=1000, yes_pct=yes_pct, frac_yes=yes_pct,
        regime="forward-estimate",
        distribution_by_layer=[], final_distribution=np.zeros(20, dtype=int),
        force_anatomy=np.ones(NUM_FORCES) / NUM_FORCES,
        dominant=Force.IDENTITY, conviction=conviction, fragility=fragility,
        camps={"yes": None, "no": None},
        params={"epsilon": 0.18, "layers": 8},
    )


class TestBimodality:
    def test_uniform_low_bimodality(self):
        stances = np.full(100, 0.5)
        assert _bimodality(stances) < 0.01

    def test_bimodal_higher(self):
        stances = np.concatenate([np.full(50, 0.1), np.full(50, 0.9)])
        uniform = np.full(100, 0.5)
        assert _bimodality(stances) > _bimodality(uniform)

    def test_small_sample(self):
        assert _bimodality(np.array([0.5])) == 0.0


class TestDetectConsensus:
    def test_strong_yes_consensus(self, civ):
        r = _make_result(yes_pct=0.85)
        events = detect_consensus(civ, [{"q1": r}], threshold=0.80)
        assert len(events) >= 1
        assert "consensus" in events[0].source

    def test_strong_no_consensus(self, civ):
        r = _make_result(yes_pct=0.15)
        events = detect_consensus(civ, [{"q1": r}], threshold=0.80)
        assert len(events) >= 1

    def test_no_consensus_when_moderate(self, civ):
        r = _make_result(yes_pct=0.55)
        events = detect_consensus(civ, [{"q1": r}], threshold=0.80)
        assert len(events) == 0

    def test_empty_history(self, civ):
        events = detect_consensus(civ, [])
        assert len(events) == 0


class TestDetectOpinionReversal:
    def test_reversal_detected(self):
        history = [
            {"q1": _make_result(yes_pct=0.40)},
            {"q1": _make_result(yes_pct=0.45)},
            {"q1": _make_result(yes_pct=0.50)},
            {"q1": _make_result(yes_pct=0.45)},
            {"q1": _make_result(yes_pct=0.38)},
        ]
        events = detect_opinion_reversal(history, window=5, min_swing=0.05)
        assert len(events) >= 1
        assert "reversal" in events[0].source

    def test_no_reversal_steady(self):
        history = [
            {"q1": _make_result(yes_pct=0.50)},
            {"q1": _make_result(yes_pct=0.51)},
            {"q1": _make_result(yes_pct=0.52)},
            {"q1": _make_result(yes_pct=0.53)},
            {"q1": _make_result(yes_pct=0.54)},
        ]
        events = detect_opinion_reversal(history, window=5, min_swing=0.05)
        assert len(events) == 0

    def test_insufficient_history(self):
        history = [{"q1": _make_result(yes_pct=0.5)}]
        events = detect_opinion_reversal(history, window=5)
        assert len(events) == 0


class TestDetectCascade:
    def test_cascade_from_multiple_thresholds(self):
        log = EventLog()
        for i in range(4):
            log.append(WorldEvent.create(
                timestamp=float(i),
                force_deltas={"fear": 0.1},
                region_pattern="IT-*",
                source="threshold:test",
            ))
        events = detect_cascade(log, t=4.0, window_ticks=5.0, min_events=3)
        assert len(events) >= 1
        assert "cascade" in events[0].source

    def test_no_cascade_when_few_events(self):
        log = EventLog()
        log.append(WorldEvent.create(
            timestamp=0.0, force_deltas={"fear": 0.1},
            region_pattern="IT-*", source="threshold:test",
        ))
        events = detect_cascade(log, t=1.0, window_ticks=5.0, min_events=3)
        assert len(events) == 0

    def test_no_cascade_from_non_threshold_events(self):
        log = EventLog()
        for i in range(5):
            log.append(WorldEvent.create(
                timestamp=float(i),
                force_deltas={"fear": 0.1},
                source="manual",
            ))
        events = detect_cascade(log, t=5.0, window_ticks=6.0, min_events=3)
        assert len(events) == 0


class TestDetectEmergentEvents:
    def test_combined_detection(self, civ):
        log = EventLog()
        for i in range(4):
            log.append(WorldEvent.create(
                timestamp=float(i),
                force_deltas={"fear": 0.1},
                region_pattern="*",
                source="threshold:test",
            ))
        history = [
            {"q1": _make_result(yes_pct=0.90)},
        ]
        events = detect_emergent_events(civ, log, t=4.0, recent_results=history)
        # Should find at least consensus + cascade
        sources = [e.source for e in events]
        assert any("consensus" in s for s in sources)
        assert any("cascade" in s for s in sources)

    def test_deterministic(self, civ):
        log = EventLog()
        history = [{"q1": _make_result(yes_pct=0.85)}]
        e1 = detect_emergent_events(civ, log, t=1.0, recent_results=history)
        e2 = detect_emergent_events(civ, log, t=1.0, recent_results=history)
        assert len(e1) == len(e2)
        for a, b in zip(e1, e2):
            assert a.source == b.source
            assert a.force_deltas == b.force_deltas
