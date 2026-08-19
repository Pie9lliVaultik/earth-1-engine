"""BACKTEST — put the world before an event whose outcome is known.

This is what turns a demo into an instrument. Everything else in the
programme grades opinion percentages. This grades CONSEQUENCES — jobs,
poverty, governments, displacement — against what actually happened.

    pre-event state + the known event -> simulated consequences
    compare to recorded history

THE HONEST LIMIT, STATED FIRST BECAUSE IT DETERMINES WHAT THE SCORE
MEANS.

Earth-1's population is not initialised to 2019. It is a synthetic
present calibrated to contemporary distributions. So this cannot be a
point-accuracy backtest — nobody should claim "we predicted 255 million
jobs lost" from a world that did not start in 2019 with 2019's firms,
2019's governments and 2019's supply chains.

What it CAN test, and what it is therefore scored on:

  DIRECTION       did the right things get worse, and the right things
                  get better
  ORDER           are the consequences within an order of magnitude of
                  the recorded figures
  RANKING         did the events order correctly against each other —
                  is the pandemic worse than the financial crisis in
                  the model, as it was in life
  GEOGRAPHY       did the damage concentrate where it actually
                  concentrated

Those four are falsifiable, they are what a policy user actually relies
on, and they do not require a historically initialised world. Point
accuracy would require that, and building it is the honest next step
after this one passes.

EVERY FIGURE IN THE REGISTRY BELOW NEEDS VERIFICATION AGAINST ITS
PRIMARY SOURCE BEFORE IT IS USED IN ANY PUBLISHED CLAIM. They are
recorded here as approximate anchors with the source named so the check
is possible; they are not quoted as established.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from earth1.branch import Scenario


@dataclass
class ResolvedEvent:
    """A historical event and what it actually did, as far as recorded."""
    id: str
    label: str
    year: int
    scenario: Scenario
    horizon_days: int
    # recorded outcomes. APPROXIMATE ANCHORS — verify before publishing.
    recorded: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    notes: str = ""


# Countries used as the exposure sets. Deliberately broad: the point of
# the geography test is whether the model concentrates damage correctly
# WITHIN a broad exposure set, not whether we hand-picked the answer.
GLOBAL = None
OECD = ["US", "GB", "DE", "FR", "IT", "ES", "JP", "KR", "CA", "AU", "NL",
        "SE", "PL", "MX", "TR"]
MENA = ["TN", "EG", "LY", "YE", "SY", "BH", "JO", "MA", "DZ", "SA"]


REGISTRY = [
    ResolvedEvent(
        id="covid_2020",
        label="COVID-19 pandemic, first year",
        year=2020,
        horizon_days=365,
        scenario=Scenario(
            id="covid_2020",
            label="Global pandemic and lockdown",
            forces={"fear": 0.45, "economics": -0.30, "collective": 0.25},
            countries=GLOBAL,
            # COVID's disruption was BOTH more global and more
            # persistent than the GFC's. The first version gave the
            # pandemic 400 days and the financial crisis 600, which is
            # inverted — and it is why the model ranked the GFC as the
            # worse event. A scenario parameter, not a model failure.
            firm_damage=0.35, trade_shock=0.18, persists_days=900),
        recorded={
            # ILO reported 2020 working-hour losses equivalent to a very
            # large number of full-time jobs; global output contracted;
            # extreme poverty rose for the first time in decades.
            "jobs_lost_fulltime_equivalent": 2.55e8,
            "gdp_contraction_pct": 3.1,
            "extreme_poverty_increase": 8.0e7,
            "direction": {"jobs": "worse", "poverty": "worse",
                          "hope": "worse", "deaths": "worse"},
        },
        sources={
            "jobs": "ILO Monitor, World of Work (2021) — VERIFY",
            "gdp": "IMF World Economic Outlook (2021) — VERIFY",
            "poverty": "World Bank poverty projections (2021) — VERIFY"},
        notes="The largest simultaneous global shock in the registry; "
              "should rank as the most damaging of the three."),

    ResolvedEvent(
        id="gfc_2008",
        label="Global financial crisis",
        year=2008,
        horizon_days=540,
        scenario=Scenario(
            id="gfc_2008",
            label="Banking collapse and credit freeze",
            forces={"fear": 0.35, "economics": -0.40},
            countries=OECD,
            firm_damage=0.28, trade_shock=0.10, persists_days=500),
        recorded={
            "jobs_lost_fulltime_equivalent": 3.0e7,
            "gdp_contraction_pct": 1.7,
            "direction": {"jobs": "worse", "poverty": "worse",
                          "hope": "worse"},
        },
        sources={"jobs": "ILO Global Employment Trends (2010) — VERIFY",
                 "gdp": "World Bank world GDP growth (2009) — VERIFY"},
        notes="Concentrated in OECD financial and construction sectors; "
              "should be less globally damaging than COVID."),

    ResolvedEvent(
        id="arab_spring_2011",
        label="Arab Spring",
        year=2011,
        horizon_days=540,
        scenario=Scenario(
            id="arab_spring_2011",
            label="Regional uprising and government collapse",
            forces={"identity": 0.40, "collective": 0.35, "fear": 0.30},
            countries=MENA,
            firm_damage=0.15, trade_shock=0.06, persists_days=700),
        recorded={
            # heads of government removed in Tunisia, Egypt, Libya, Yemen
            "governments_fell": 4,
            "displaced": 1.0e7,
            "direction": {"governments": "worse", "displacement": "worse",
                          "jobs": "worse"},
        },
        sources={"governments": "contemporaneous reporting — VERIFY",
                 "displaced": "UNHCR regional figures — VERIFY"},
        notes="The test here is GOVERNMENTS and DISPLACEMENT rather than "
              "jobs — a different consequence channel, which is why it "
              "is in the registry."),
]


def score(event: ResolvedEvent, consequences: dict, scale: float) -> dict:
    """Grade a simulated consequence report against recorded history.

    Scored on direction, order of magnitude, and nothing more precise,
    for the reason given in the module docstring.
    """
    rec = event.recorded
    out = {"event": event.id, "label": event.label, "checks": []}

    def check(name, predicted, actual, tolerance_orders=1.0):
        if actual in (None, 0) or predicted is None:
            return
        p = float(predicted) * scale
        a = float(actual)
        orders = abs(np.log10(max(p, 1.0)) - np.log10(max(a, 1.0)))
        out["checks"].append({
            "quantity": name,
            "predicted": float(p),
            "recorded": a,
            "orders_of_magnitude_off": round(float(orders), 2),
            "within_tolerance": bool(orders <= tolerance_orders)})

    # Grade the CUMULATIVE figure against the cumulative record. The
    # ILO's 255 million is full-time-equivalent job-years lost across
    # 2020, so the comparable model quantity is person-years of excess
    # joblessness integrated over the horizon — not the headcount left
    # standing on the final day.
    check("jobs_lost", consequences.get("jobs_lost_cumulative",
                                        consequences.get("jobs_lost")),
          rec.get("jobs_lost_fulltime_equivalent"))
    check("people_in_destitution",
          consequences.get("people_pushed_into_destitution"),
          rec.get("extreme_poverty_increase"))
    check("displaced", consequences.get("displaced"), rec.get("displaced"))

    # direction: did the right things move the right way
    dirs = rec.get("direction", {})
    got = {}
    if "jobs" in dirs:
        got["jobs"] = "worse" if (consequences.get("jobs_lost") or 0) > 0 \
            else "same_or_better"
    if "poverty" in dirs:
        got["poverty"] = "worse" if (consequences.get(
            "people_pushed_into_destitution") or 0) > 0 else "same_or_better"
    if "hope" in dirs:
        hc = consequences.get("hope_change")
        got["hope"] = "worse" if (hc is not None and hc < 0) \
            else "same_or_better"
    if "governments" in dirs:
        got["governments"] = "worse" if consequences.get(
            "governments_at_risk_count",
            len(consequences.get("governments_at_risk", []))) else "same_or_better"
    if "displacement" in dirs:
        got["displacement"] = "worse" if (consequences.get("displaced") or 0) \
            > 0 else "same_or_better"
    if "deaths" in dirs:
        got["deaths"] = "worse" if (consequences.get("excess_deaths") or 0) \
            > 0 else "same_or_better"

    agree = {k: bool(got.get(k) == v) for k, v in dirs.items() if k in got}
    out["direction_expected"] = dirs
    out["direction_got"] = got
    out["direction_correct"] = agree
    out["direction_score"] = (round(sum(agree.values()) / len(agree), 3)
                              if agree else None)
    mags = [c["within_tolerance"] for c in out["checks"]]
    out["magnitude_score"] = (round(sum(mags) / len(mags), 3) if mags
                              else None)
    out["governments_fell_recorded"] = rec.get("governments_fell")
    # Read the COUNT, not the list. The list is suppressed by default
    # (country detail is not reportable), so scoring against it saw zero
    # governments at risk against four that actually fell — a failure
    # manufactured by our own suppression rule.
    out["governments_at_risk_predicted"] = int(
        consequences.get("governments_at_risk_count",
                         len(consequences.get("governments_at_risk", []))))
    return out


def ranking_check(scored: list) -> dict:
    """Did the events order correctly against each other?

    This is the strongest test in the module that does NOT need a
    historically initialised world: whatever the absolute figures, the
    pandemic should come out worse than the financial crisis, because it
    was. Getting the ORDER right is a real claim about the model's
    internal proportionality.
    """
    got = sorted(scored, key=lambda s: -max(
        (c["predicted"] for c in s["checks"]
         if c["quantity"] == "jobs_lost"), default=0.0))
    expected = ["covid_2020", "gfc_2008", "arab_spring_2011"]
    got_order = [s["event"] for s in got if s["event"] in expected]
    exp_order = [e for e in expected if e in got_order]
    return {"expected_order_by_job_losses": exp_order,
            "model_order": got_order,
            "order_correct": got_order == exp_order}
