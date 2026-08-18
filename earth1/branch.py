"""BRANCH — take the world as it stands, do something to it, live it forward.

This is the product, in one function.

    S_t + X  ->  S_t+1 -> ... -> S_t+n

You take the civilisation at this moment, apply a scenario, and let it
LIVE through the consequences — jobs, firms, governments, hunger,
protest, migration, death — rather than asking anyone what they imagine
they would think about a hypothetical. Then you ask them.

That ordering is the whole distinction. Earth-1 does not ask synthetic
humans what they think about a possible future. It simulates the future
AROUND them, lets them change inside it, and then asks.

Every branch runs against a CONTROL: the same world, same seed, same
dice, no scenario. Without it a number like "jobs lost" is
uninterpretable, because a living world is always losing and creating
jobs anyway.

And every scenario is run SEVERAL TIMES with different dice. The world
is chaotic — FSLE +0.13/day, measured — so one run is a sample. The
spread across runs is not noise to be averaged away, it is the honest
width of the forecast.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np

from earth1.alive import live_one_day
from earth1.consequences import compare, snapshot, with_uncertainty
from earth1.types import Force


@dataclass
class Scenario:
    """Something that happens to the world."""
    id: str
    label: str
    # which force channels it presses, and how hard
    forces: dict
    # who it reaches: iso2 codes, or None for everywhere
    countries: list | None = None
    # what it does to the economy where it lands
    firm_damage: float = 0.0
    trade_shock: float = 0.0      # raises the cost of living
    escalates_to_war: bool = False
    persists_days: float = 30.0


def apply(w, sc: Scenario, rng) -> None:
    """The scenario lands on the world. Materially, not just as mood."""
    from earth1.genesis import GENESIS_COUNTRIES
    from earth1.memory import Memory

    iso = {c["iso2"]: i for i, c in enumerate(GENESIS_COUNTRIES)}
    if sc.countries:
        hit_c = np.array([iso[c] for c in sc.countries if c in iso])
        scope = np.isin(w.civ.country, hit_c)
    else:
        hit_c = np.arange(len(GENESIS_COUNTRIES))
        scope = np.ones(w.civ.n, dtype=bool)

    # it enters the world's memory as a thing that happened, and fades
    sig = np.zeros(len(Force))
    for k, v in sc.forces.items():
        f = getattr(Force, k.upper(), None)
        if f is not None:
            sig[f] = v
    w.chronicle.remember(Memory(
        id=sc.id, label=sc.label, day=float(w.day), force_signature=sig,
        scope=scope.copy(), origin="scenario",
        half_life=max(sc.persists_days, 1.0)))

    # the economy takes it first — this is how a headline reaches a life
    if sc.firm_damage:
        firms_hit = np.isin(w.life.firm_country, hit_c)
        w.life.firm_health[firms_hit] = np.clip(
            w.life.firm_health[firms_hit] - sc.firm_damage, 0.0, 1.0)
    if sc.trade_shock:
        # the cost of staying alive rises for everyone it reaches
        w.life.cost[scope] *= (1.0 + sc.trade_shock)
    if sc.escalates_to_war and hit_c.size >= 2:
        a, b = int(hit_c[0]), int(hit_c[1])
        w.gov.at_war_with[a], w.gov.at_war_with[b] = b, a
        w.gov.war_days[[a, b]] = 0.0


def run(world, scenarios: list, days: int = 180, repeats: int = 3,
        seed: int = 0, progress=None) -> dict:
    """Branch the world. Control first, then every scenario, several times.

    Returns consequences per scenario, each with the spread across
    repeats, so the output is a range rather than a false point.
    """
    base_snap = None
    out = {}

    # ── the control: the same world, untouched ───────────────────────
    ctrl_reports = []
    for r in range(repeats):
        w = copy.deepcopy(world)
        rng = np.random.default_rng(seed * 977 + r)
        for _ in range(days):
            live_one_day(w, rng)
        ctrl_reports.append(snapshot(w))
        if progress:
            progress(f"control {r + 1}/{repeats}")
    # average the controls into one counterfactual
    base_snap = ctrl_reports[0]
    for k, v in base_snap.items():
        if isinstance(v, np.ndarray):
            base_snap[k] = np.mean([c[k] for c in ctrl_reports], axis=0)
        elif isinstance(v, (int, float)) and v is not None:
            base_snap[k] = float(np.mean([c[k] for c in ctrl_reports]))

    for sc in scenarios:
        reports = []
        for r in range(repeats):
            w = copy.deepcopy(world)
            rng = np.random.default_rng(seed * 977 + r)   # SAME dice as control
            apply(w, sc, rng)
            for _ in range(days):
                live_one_day(w, rng)
            reports.append(compare(base_snap, snapshot(w), w, days))
            if progress:
                progress(f"{sc.id} {r + 1}/{repeats}")
        out[sc.id] = {"label": sc.label,
                      "runs": reports,
                      "consequences": reports[0],
                      "uncertainty": with_uncertainty(reports)}
    return {"horizon_days": days, "repeats": repeats, "branches": out}
