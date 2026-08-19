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
    ctrl_paths = []          # the control's DAILY unemployment path
    for r in range(repeats):
        w = copy.deepcopy(world)
        rng = np.random.default_rng(seed * 977 + r)
        from earth1.genesis import census_weights
        cw = census_weights(w.civ)
        path = []
        for _ in range(days):
            live_one_day(w, rng)
            lf_alive = w.life.in_lf & w.health.alive
            path.append(float(cw[(~w.life.employed) & lf_alive].sum()))
        ctrl_paths.append(path)
        ctrl_reports.append(snapshot(w))
        if progress:
            progress(f"control {r + 1}/{repeats}")
    # The averaged control is kept ONLY as a reporting reference. It is
    # deliberately no longer used for differencing — see the paired
    # comparison below, which is where the variance reduction lives.
    base_snap = {}
    for k, v in ctrl_reports[0].items():
        if isinstance(v, np.ndarray):
            base_snap[k] = np.mean([c[k] for c in ctrl_reports], axis=0)
        elif isinstance(v, (int, float)) and v is not None:
            base_snap[k] = float(np.mean([c[k] for c in ctrl_reports]))
        else:
            base_snap[k] = v

    for sc in scenarios:
        reports = []
        peak_jobless = [0.0] * repeats
        max_jobless = [0.0] * repeats
        for r in range(repeats):
            w = copy.deepcopy(world)
            rng = np.random.default_rng(seed * 977 + r)   # SAME dice as control
            apply(w, sc, rng)
            # track the whole path, not just where it ends
            # Track the path with a CHEAP weighted count, not a full
            # snapshot — snapshot() costs ~184ms and calling it daily
            # would add ten minutes of pure overhead per ensemble.
            # Weights depend only on the country allocation, which never
            # changes during a run — so compute them ONCE. Rebuilding a
            # 200K array every simulated day turned a 50-minute job into
            # a five-hour one for no information gain.
            from earth1.genesis import census_weights
            cw = census_weights(w.civ)
            base_j = ctrl_reports[r]["unemployed"]
            # DAY AGAINST DAY. The first version compared the branch on
            # day t against the control's value on the FINAL day — a
            # single endpoint. Since the control's unemployment drifts
            # upward across the horizon, branch-day-5 minus
            # control-day-365 is negative for most of the run and clips
            # to zero. That is how a global pandemic came back with
            # exactly zero job losses: I was differencing across TIME
            # instead of across CONDITION.
            ctrl_path = ctrl_paths[r]
            for t in range(days):
                live_one_day(w, rng)
                lf_alive = w.life.in_lf & w.health.alive
                snap_j = float(cw[(~w.life.employed) & lf_alive].sum())
                excess = max(0.0, snap_j - ctrl_path[t])
                peak_jobless[r] += excess / 365.0     # person-years lost
                max_jobless[r] = max(max_jobless[r], excess)
            # PAIRED DIFFERENCE — against the control that ran on THESE
            # dice, not against the average of all controls.
            #
            # The dice were already aligned; the subtraction threw the
            # alignment away. Common random numbers only cancel noise
            # when the MATCHED pair is differenced: run r and control r
            # share every draw, so their shared background churn is
            # identical and vanishes, leaving the scenario's effect.
            # Differencing against an averaged control leaves run r's own
            # churn in the estimate and re-introduces the variance the
            # matching was there to remove.
            #
            # Measured cost of getting this wrong: the country-level
            # signal read 0.0103 unpaired against 0.0359 properly paired.
            # A factor of three, thrown away by comparing to a mean.
            rep = compare(ctrl_reports[r], snapshot(w), w, days)
            # CUMULATIVE, not the endpoint. The recorded figures these
            # get graded against — the ILO's 255 million for 2020 — are
            # integrals over the year, not a headcount on the last day.
            # Reading the final state made a fast-recovering shock score
            # as though it had never happened, which is a category error
            # rather than a modelling one.
            rep["jobs_lost_cumulative"] = int(round(peak_jobless[r]))
            rep["jobs_lost_peak"] = int(round(max_jobless[r]))
            reports.append(rep)
            if progress:
                progress(f"{sc.id} {r + 1}/{repeats}")
        out[sc.id] = {"label": sc.label,
                      "runs": reports,
                      "consequences": reports[0],
                      "uncertainty": with_uncertainty(reports)}
    return {"horizon_days": days, "repeats": repeats, "branches": out}
