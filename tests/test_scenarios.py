"""Tests for composable scenario branching."""
import sys
sys.path.insert(0, ".")

import numpy as np
import pytest

from earth1.scenarios import (
    Event, ScenarioBranch, BranchStep, ScenarioTree,
    run_tree, quick_branch, list_events, get_event,
    EVENT_CATALOG, _find_divergence,
)
from earth1.temporal import simulate, Shock
from earth1.engine import build_civilization
from earth1.questions import question_by_id
from earth1.types import Force


POP = 10_000
civ = build_civilization(POP, seed=42)


class TestEvent:
    def test_from_forces(self):
        e = Event.from_forces("test", "Test Event", fear=2.0, economics=-1.0)
        assert e.shifts[Force.FEAR.value] == 2.0
        assert e.shifts[Force.ECONOMICS.value] == -1.0

    def test_as_shock(self):
        e = Event.from_forces("test", "Test", fear=1.5)
        shock = e.as_shock(day=30)
        assert isinstance(shock, Shock)
        assert shock.day == 30
        assert shock.shifts[Force.FEAR.value] == 1.5

    def test_scaled(self):
        e = Event.from_forces("test", "Test", fear=2.0, economics=1.0)
        doubled = e.scaled(2.0)
        assert doubled.shifts[Force.FEAR.value] == 4.0
        assert doubled.shifts[Force.ECONOMICS.value] == 2.0
        assert "x2.0" in doubled.id

    def test_combined(self):
        a = Event.from_forces("a", "A", tags=["crisis"], fear=2.0)
        b = Event.from_forces("b", "B", tags=["economics"], economics=1.5)
        c = a.combined(b)
        assert c.shifts[Force.FEAR.value] == 2.0
        assert c.shifts[Force.ECONOMICS.value] == 1.5
        assert "crisis" in c.tags
        assert "economics" in c.tags

    def test_combined_stacks_same_force(self):
        a = Event.from_forces("a", "A", fear=2.0)
        b = Event.from_forces("b", "B", fear=1.0)
        c = a.combined(b)
        assert c.shifts[Force.FEAR.value] == 3.0


class TestEventCatalog:
    def test_catalog_not_empty(self):
        assert len(EVENT_CATALOG) >= 10

    def test_get_event(self):
        e = get_event("financial_crisis")
        assert e is not None
        assert e.id == "financial_crisis"
        assert Force.FEAR.value in e.shifts

    def test_get_event_missing(self):
        assert get_event("nonexistent") is None

    def test_list_events_all(self):
        events = list_events()
        assert len(events) >= 10

    def test_list_events_by_tag(self):
        crisis = list_events(tag="crisis")
        assert len(crisis) >= 3
        for e in crisis:
            assert "crisis" in e.tags

    def test_list_events_by_tag_no_match(self):
        empty = list_events(tag="nonexistent_tag")
        assert len(empty) == 0


class TestScenarioBranch:
    def test_from_event_ids(self):
        branch = ScenarioBranch.from_event_ids(
            "test", "Test Branch",
            [(0, "financial_crisis"), (90, "pandemic_onset")],
        )
        assert len(branch.steps) == 2
        assert branch.steps[0].day == 0
        assert branch.steps[1].event.id == "pandemic_onset"

    def test_from_event_ids_bad_event(self):
        with pytest.raises(ValueError, match="Unknown event"):
            ScenarioBranch.from_event_ids("test", "Test", [(0, "fake_event")])

    def test_to_shocks(self):
        branch = ScenarioBranch.from_event_ids(
            "test", "Test", [(30, "bank_run")],
        )
        shocks = branch.to_shocks()
        assert len(shocks) == 1
        assert shocks[0].day == 30

    def test_then_chains(self):
        branch = ScenarioBranch.from_event_ids("a", "A", [(0, "war_outbreak")])
        extended = branch.then(180, get_event("peace_deal"))
        assert len(extended.steps) == 2
        assert extended.steps[1].day == 180

    def test_fork_creates_multiple(self):
        branch = ScenarioBranch.from_event_ids("root", "Root", [(0, "pandemic_onset")])
        forks = branch.fork(90, [
            get_event("pandemic_recovery"),
            get_event("financial_crisis"),
        ])
        assert len(forks) == 2
        assert all(len(f.steps) == 2 for f in forks)


class TestRunTree:
    def test_returns_scenario_tree(self):
        q = question_by_id("svb")
        branches = [
            ScenarioBranch.from_event_ids("crisis", "Crisis", [(0, "financial_crisis")]),
            ScenarioBranch.from_event_ids("boom", "Boom", [(0, "market_boom")]),
        ]
        tree = run_tree(q, civ, branches, duration_days=180, step_days=30)
        assert isinstance(tree, ScenarioTree)
        assert "baseline" in tree.timelines
        assert "crisis" in tree.timelines
        assert "boom" in tree.timelines

    def test_tree_has_analysis(self):
        q = question_by_id("svb")
        branches = [
            ScenarioBranch.from_event_ids("crisis", "Crisis", [(0, "financial_crisis")]),
        ]
        tree = run_tree(q, civ, branches, duration_days=90, step_days=30)
        assert tree.analysis.max_divergence >= 0
        assert len(tree.analysis.branch_rankings) == 2

    def test_tree_without_baseline(self):
        q = question_by_id("svb")
        branches = [
            ScenarioBranch.from_event_ids("a", "A", [(0, "war_outbreak")]),
            ScenarioBranch.from_event_ids("b", "B", [(0, "peace_deal")]),
        ]
        tree = run_tree(q, civ, branches, duration_days=90, step_days=30,
                        include_baseline=False)
        assert "baseline" not in tree.timelines
        assert "a" in tree.timelines
        assert "b" in tree.timelines

    def test_crisis_vs_boom_diverge(self):
        q = question_by_id("svb")
        branches = [
            ScenarioBranch.from_event_ids("crisis", "Crisis", [(0, "financial_crisis")]),
            ScenarioBranch.from_event_ids("boom", "Boom", [(0, "market_boom")]),
        ]
        tree = run_tree(q, civ, branches, duration_days=180, step_days=30)
        assert tree.analysis.max_divergence > 0.01

    def test_chained_events(self):
        q = question_by_id("ssm")
        branch = ScenarioBranch.from_event_ids(
            "chain", "Pandemic then election",
            [(0, "pandemic_onset"), (180, "election_polarizing")],
        )
        tree = run_tree(q, civ, [branch], duration_days=360, step_days=30)
        assert "chain" in tree.timelines
        tl = tree.timelines["chain"]
        assert any("Polarizing" in s for tp in tl.time_points for s in tp.active_shocks)


class TestQuickBranch:
    def test_quick_branch_works(self):
        q = question_by_id("svb")
        tree = quick_branch(q, civ, {
            "crisis": [(0, "financial_crisis")],
            "calm": [(0, "market_boom")],
        }, duration_days=90, step_days=30)
        assert "crisis" in tree.timelines
        assert "calm" in tree.timelines
        assert "baseline" in tree.timelines


class TestDivergenceAnalysis:
    def test_convergence_detection(self):
        q = question_by_id("ssm")
        branches = [
            ScenarioBranch.from_event_ids("shock", "Media shock", [(0, "media_shock")]),
        ]
        tree = run_tree(q, civ, branches, duration_days=360, step_days=30)
        assert isinstance(tree.analysis.converges, bool)

    def test_rankings_sorted_by_yes_pct(self):
        q = question_by_id("svb")
        branches = [
            ScenarioBranch.from_event_ids("crisis", "Crisis", [(0, "financial_crisis")]),
            ScenarioBranch.from_event_ids("boom", "Boom", [(0, "market_boom")]),
        ]
        tree = run_tree(q, civ, branches, duration_days=180, step_days=30)
        rankings = tree.analysis.branch_rankings
        yes_pcts = [r["final_yes_pct"] for r in rankings]
        assert yes_pcts == sorted(yes_pcts, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
