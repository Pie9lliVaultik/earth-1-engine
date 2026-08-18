"""OBSERVE — follow one earthling, and read their possible futures.

Two things live here, and they are the same thing seen from two sides.

OBSERVATION. Pick a person out of the population and look at their
life: where they live, what they do, who they know, what has happened
to them, what they believe and how strongly. Not a card generated for
display — the actual state the simulation is carrying for that agent,
read directly.

THE EARTHLING MULTIVERSE. Run that one person's life forward many
times from this exact moment. The world is stochastic, so the futures
differ; the SPREAD of those futures is that person's indeterminacy, and
the modal path is the life they are most likely to lead.

    "A 34-year-old in Lagos. Employed, two weeks of savings, one job
     loss behind him. In 200 of 200 futures he keeps working. In 31 he
     is destitute within the year. In 9 he is destitute AND isolated,
     and in those his fear runs a third higher than in the others."

Observation and branching are the same operation because the futures
are only resolved when someone asks. Until then the agent carries all
of them.
"""
from __future__ import annotations

import copy

import numpy as np

from earth1.life import EVENT_CODES, OCC_NAMES
from earth1.types import Force

FORCE_NAMES = [f.name.lower() for f in Force]


def _country(civ, i: int) -> str:
    from earth1.genesis import GENESIS_COUNTRIES
    c = GENESIS_COUNTRIES[int(civ.country[i])]
    return f"{c['name']} ({c['iso2']})"


def observe(civ, life, i: int, fabric=None) -> dict:
    """Everything the world is currently carrying about one person."""
    age_years = float(18 + civ.age[i] * 72)
    out = {
        "id": int(i),
        "country": _country(civ, i),
        "age": round(age_years, 1),
        "education": ["low", "mid", "high"][int(civ.education[i])],
        "urban": bool(civ.urban[i]),
        "work": {
            "occupation": OCC_NAMES[int(life.occupation[i])],
            "employed": bool(life.employed[i]),
            "in_labour_force": bool(life.in_lf[i]),
            "years_in_job": round(float(life.tenure[i]) / 365.0, 2),
            "times_lost_work": int(life.spells[i]),
        },
        "money": {
            "wage_vs_survival_cost": round(float(life.wage[i]), 2),
            "savings_days": round(float(life.wealth[i]), 1),
            "deprivation": round(float(life.deprivation[i]), 3),
        },
        "forces": {n: round(float(civ.forces[i, k]), 3)
                   for k, n in enumerate(FORCE_NAMES)},
        "conviction": round(float(civ.alpha[i]), 3),
    }
    if life.mental is not None:
        out["self"] = {
            "mental_health": round(float(life.mental[i]), 3),
            "physical_health": round(float(life.physical[i]), 3),
            "addiction": round(float(life.addiction[i]), 3),
            "relationship": round(float(life.relationship[i]), 3),
            "unmet_social_need": round(float(life.social_need[i]), 3),
            "political_engagement": round(float(life.political[i]), 3),
            "last_thing_that_happened": EVENT_CODES.get(
                int(life.last_event[i]), "nothing"),
            "marks_left_by_life": int(life.n_events[i]),
        }
    if fabric is not None:
        out["connections"] = {
            k: int(m[i].nnz) for k, m in fabric.by_type.items()}
        out["household_id"] = int(fabric.household[i])
    return out


def futures(civ, life, i: int, *, n_branches: int = 200, days: int = 365,
            step_kw: dict | None = None) -> dict:
    """Run this person's life forward many times. Report the spread.

    Every branch starts from the identical present and differs only in
    the dice. What comes back is not a prediction, it is a DISTRIBUTION
    over the lives this person could lead from here — which is the
    honest object, because the world is stochastic and a single forward
    run would be one sample dressed up as an answer.
    """
    from earth1.chaos import world_step
    kw = step_kw or dict(beta=2.0, residue=0.02,
                         critical_fraction=0.12, relax=0.25)
    start = observe(civ, life, i)

    rows = []
    for b in range(n_branches):
        c2 = copy.deepcopy(civ)
        l2 = copy.deepcopy(life)
        rng = np.random.default_rng(90000 + b)
        ever_destitute = False
        ever_jobless = False
        for _ in range(days):
            world_step(c2, l2, rng, **kw)
            if l2.deprivation[i] > 0.99:
                ever_destitute = True
            if not l2.employed[i] and l2.in_lf[i]:
                ever_jobless = True
        rows.append({
            "employed": bool(l2.employed[i]),
            "destitute_end": bool(l2.deprivation[i] > 0.99),
            "ever_destitute": ever_destitute,
            "ever_jobless": ever_jobless,
            "savings_days": float(l2.wealth[i]),
            "mental": float(l2.mental[i]) if l2.mental is not None else None,
            "isolated": (bool(l2.relationship[i] < 0.25)
                         if l2.relationship is not None else None),
            "fear": float(c2.forces[i, Force.FEAR]),
            "spells": int(l2.spells[i]),
        })

    def frac(key):
        return round(float(np.mean([r[key] for r in rows])), 4)

    fear = np.array([r["fear"] for r in rows])
    sav = np.array([r["savings_days"] for r in rows])
    bad = [r for r in rows if r["ever_destitute"]]
    good = [r for r in rows if not r["ever_destitute"]]
    return {
        "who": start,
        "branches": n_branches, "horizon_days": days,
        "P_employed_at_end": frac("employed"),
        "P_ever_jobless": frac("ever_jobless"),
        "P_ever_destitute": frac("ever_destitute"),
        "P_destitute_at_end": frac("destitute_end"),
        "P_isolated_at_end": frac("isolated"),
        "savings_days": {"p10": round(float(np.percentile(sav, 10)), 1),
                         "median": round(float(np.median(sav)), 1),
                         "p90": round(float(np.percentile(sav, 90)), 1)},
        "fear": {"median": round(float(np.median(fear)), 3),
                 "spread_p10_p90": [round(float(np.percentile(fear, 10)), 3),
                                    round(float(np.percentile(fear, 90)), 3)]},
        "fear_if_destitute": (round(float(np.mean([r["fear"] for r in bad])), 3)
                              if bad else None),
        "fear_if_not": (round(float(np.mean([r["fear"] for r in good])), 3)
                        if good else None),
    }
