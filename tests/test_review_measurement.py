"""Review regressions M06a/b/c/d — one honest measurement layer for
consequence reports (ops/alive/EXTERNAL_REVIEW_VERIFICATION_2026-09-08).

Reproduces the reviewer's probes against the fixed layer:

  M06c  SEM was std(ddof=1)/sqrt(n-1) at both aggregation sites; must
        be std(ddof=1)/sqrt(n). For 1..8 that is 0.86603, not 0.92582.
  M06a  geography delta_people lacked the 8.1e9/base_pop conversion the
        global lines carry — a single hungry agent read as "1 person"
        on the country line and "~405k people" on the global line.
  M06b  a day-30 run's memory line was hard-labelled 'force units at
        day 180'; the day actually measured must be stamped, and a
        substituted horizon flagged (requested_day/measured_day).
  M06d  the consequence path differenced dead SLOTS (rebirth recycles
        a slot within the tick; ~4% capture, 0% in the reviewer's
        90-day probe); a per-arm DeathWatch now reports cumulative
        deaths as deaths_cumulative alongside the stock, which is kept
        under the honest name dead_slots_now.
"""
import numpy as np
import pytest

from earth1.adapters import consequences as cq
from earth1.branch import Scenario, null_branch
from earth1.genesis import GENESIS_COUNTRIES
from earth1.types import FORCE_KEYS

NC = len(GENESIS_COUNTRIES)
NF = len(FORCE_KEYS)
EXP_I = [f.name.lower() for f in FORCE_KEYS].index("experience")
BASE_POP = 20000
N_SEEDS = 8


def _snap(hungry, exp_force=0.0):
    """The reviewer's synthetic snapshot: everything zero except an
    optional weighted hungry count in country 0 and an experience
    force level."""
    d = {k: 0.0 for k in ["unemployed", "destitute", "evicted", "homeless",
                          "dead", "median_buffer", "migrants", "mean_hope",
                          "_protest_risk", "_hot_locality_days",
                          "_onsets_event"]}
    f = np.zeros(NF)
    f[EXP_I] = exp_force
    d.update(hungry=hungry, _forces=f, _forces_by_c={},
             legitimacy=np.zeros(NC),
             hungry_by_country=np.r_[hungry, np.zeros(NC - 1)],
             destitute_by_country=np.zeros(NC),
             people_per_agent_by_country=np.ones(NC))
    return d


def _report(runs):
    return cq.build_from_runs(
        {"question_id": "probe", "class": "probe",
         "scenario": Scenario("probe", "probe", {})},
        runs, [], list(range(N_SEEDS)), BASE_POP, 0.0)


# ── M06c ─────────────────────────────────────────────────────────────

def test_sem_is_std_over_sqrt_n():
    row = cq._line("t", [1., 2., 3., 4., 5., 6., 7., 8.], "u",
                   "UNCALIBRATED")
    # std(1..8, ddof=1)/sqrt(8) = 2.44949/2.82843
    assert row["sem"] == pytest.approx(0.86603, abs=1e-5)
    # and NOT the reviewer's measured defect value std/sqrt(n-1)
    assert row["sem"] != pytest.approx(0.92582, abs=1e-4)


# ── M06a (+ exact-day labelling and geo SEM site of M06c) ────────────

def test_country_and_global_lines_agree_on_one_agent():
    """Reviewer's 1-agent synthetic: one weighted hungry agent in
    country 0 at N=20,000 must read as the SAME number of people on
    the global line and the country line."""
    runs = [{"scn": {"snaps": {7: _snap(1.0), 90: _snap(1.0),
                               180: _snap(1.0)}, "hash": "s"},
             "null": {"snaps": {7: _snap(0.0), 90: _snap(0.0),
                                180: _snap(0.0)}, "hash": "n"}}
            for _ in range(N_SEEDS)]
    rep = _report(runs)

    g = next(r for r in rep["order2"] if r["observable"] == "hungry")
    assert g["delta"] == pytest.approx(1.0)              # weighted agents
    # the exact requested day was measured: stamped, not flagged
    assert g["unit"] == "agents at day 90"
    assert "requested_day" not in g and "measured_day" not in g

    geo = rep["order2_geography"]
    assert geo["basis"] == "hungry_by_country"
    assert geo["unit"] == "people"
    assert geo["measured_day"] == 90
    top = geo["top"][0]
    people_per_agent = 8.1e9 / BASE_POP                  # 405,000
    assert top["delta_people"] == pytest.approx(people_per_agent)
    # reconciliation the block now carries: people = agents * ppa
    assert top["delta_people"] == pytest.approx(
        g["delta"] * top["people_per_agent"], rel=1e-6)
    # geo SEM site uses the same sqrt(n) divisor (identical runs -> 0)
    assert top["sem"] == pytest.approx(0.0, abs=1e-9)


# ── M06b ─────────────────────────────────────────────────────────────

def test_substituted_day_is_flagged_not_relabelled():
    """Reviewer's day-30 run: with snapshots only at 7 and 30, the
    memory line used to claim 'force units at day 180'."""
    runs = [{"scn": {"snaps": {7: _snap(0.0),
                               30: _snap(0.0, exp_force=0.1)},
                     "hash": "s"},
             "null": {"snaps": {7: _snap(0.0), 30: _snap(0.0)},
                      "hash": "n"}}
            for _ in range(N_SEEDS)]
    rep = _report(runs)

    mem = next(r for r in rep["order3"]
               if r["observable"] == "memory_imprint_experience")
    assert mem["unit"] == "force units at day 30"
    assert "180" not in mem["unit"]
    assert mem["requested_day"] == 180
    assert mem["measured_day"] == 30
    assert mem["delta"] == pytest.approx(0.1)

    # order2 lines requested at day 90 carry the substitution too
    une = next(r for r in rep["order2"] if r["observable"] == "unemployed")
    assert une["measured_day"] == 30 and une["requested_day"] == 90
    assert une["unit"] == "agents at day 30"

    # and the geography block states what it measured
    assert rep["order2_geography"]["measured_day"] == 30


# ── M06d ─────────────────────────────────────────────────────────────

def test_deathwatch_threaded_through_pair_runner(tiny_world):
    """30-day 2k pair run: deaths_cumulative is present at every
    snapshot, monotone non-decreasing, and >= the naive dead-stock
    delta the old path reported (which rebirth pins near zero)."""
    pair, _ = cq._run_pair(null_branch(), tiny_world, 0, 30)
    for arm in ("scn", "null"):
        snaps = pair[arm]["snaps"]
        days = sorted(snaps)
        assert days, "no snapshots recorded"
        cum = [snaps[d]["deaths_cumulative"] for d in days]
        assert all(c == c and c >= 0 for c in cum)
        assert cum == sorted(cum), "deaths_cumulative must be monotone"
        naive = float(snaps[days[-1]]["dead"]) - float(snaps[days[0]]["dead"])
        assert cum[-1] >= naive - 1e-9, (
            f"DeathWatch count {cum[-1]} < naive dead-stock delta {naive}")


def test_dead_stock_renamed_and_flow_reported():
    """The report keeps the stock under dead_slots_now (labelled) and
    reports deaths_cumulative as a flow line."""
    def snap_with_deaths(dead_slots, deaths_cum):
        s = _snap(0.0)
        s["dead"] = dead_slots
        s["deaths_cumulative"] = deaths_cum
        return s

    # 12 real deaths per run, of which the stock shows 0.5 slots
    runs = [{"scn": {"snaps": {7: snap_with_deaths(0.5, 3.0),
                               90: snap_with_deaths(0.5, 12.0)},
                     "hash": "s"},
             "null": {"snaps": {7: snap_with_deaths(0.0, 0.0),
                                90: snap_with_deaths(0.0, 0.0)},
                      "hash": "n"}}
            for _ in range(N_SEEDS)]
    rep = _report(runs)
    names = [r["observable"] for r in rep["order2"]]
    assert "dead" not in names
    stock = next(r for r in rep["order2"]
                 if r["observable"] == "dead_slots_now")
    flow = next(r for r in rep["order2"]
                if r["observable"] == "deaths_cumulative")
    assert stock["kind"] == "stock"
    assert "stock" in (stock["note"] or "")
    assert flow["kind"] == "flow"
    assert stock["delta"] == pytest.approx(0.5)
    assert flow["delta"] == pytest.approx(12.0)
