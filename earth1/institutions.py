"""INSTITUTIONS — governments, war, migration, and how a life changes class.

GOVERNMENTS. One per country, and they DECIDE. Each holds a policy
state — tax, welfare generosity, policing, war footing — and each
watches its own population. When deprivation climbs, a government
either spends or represses, and which one it reaches for depends on how
much legitimacy it has left. Policy then changes the parameters its
people live under: welfare generosity IS the safety net that life.py
was treating as a constant of nature. It stops being a constant and
becomes a decision, which closes the loop between what a population
suffers and what is done about it.

WAR. States go to war when fear is high, legitimacy is failing, and a
neighbour looks weak — the historically ordinary combination. War
conscripts the young, kills, displaces people across borders, wrecks
firms, and dominates every channel of attention at once. It is the
single most violent thing one government can do to another population's
lives, and it enters this model as exactly that.

MIGRATION. People leave. They leave when staying is worse than going,
they go where they already know somebody, and the leaving is
self-reinforcing because each migrant becomes somebody else's reason to
follow. Diaspora ties are the corridor.

CLASS. Three trajectories the model previously had no way to express:
  HOMELESS   savings gone, nobody to fall back on, no institution to
             catch you. It is the CONJUNCTION that does it — poverty
             alone rarely puts a person on the street; poverty plus
             isolation plus no safety net does.
  CRIMINAL   deprivation plus opportunity plus nothing left to lose,
             damped by policing and by having status worth protecting.
  WEALTHY    compounding. Returns accrue to those who already have a
             buffer, which is why the top pulls away rather than
             drifting.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.types import Force

TIERS = ["HIC", "UMIC", "LMIC", "LIC"]
# Steady-state wars = onset/(onset+end) x 194. The first values gave
# 44 countries at war at once against a real-world figure near 10.
WAR_ONSET_YR = 0.0035        # per country-year, before modifiers
WAR_END_YR = 1.10             # median war well under a year
CONSCRIPT_SHARE = 0.06
MIGRATION_RATE_YR = 0.008     # ~0.8%/yr, close to real gross flows

# ── NUCLEAR WEAPONS ──────────────────────────────────────────────────
# In only as a war-escalation term, which is the one thing they
# demonstrably change. Two effects, opposite in sign, and both are
# contested in the literature — which is why they are parameters here
# rather than assumptions buried in code:
#
#   DETERRENCE   no two nuclear-armed states have fought a full
#                interstate war. Whether that is causation or a
#                seventy-year coincidence is genuinely disputed, so the
#                strength of the effect is a knob, not a fact.
#   CEILING      when a nuclear state fights a non-nuclear one, the
#                escalation ceiling is higher, and use would be
#                catastrophic rather than merely severe.
NUCLEAR_STATES = ("US", "RU", "CN", "FR", "GB", "IN", "PK", "IL", "KP")
DETERRENCE_FACTOR = 0.08      # war onset multiplier when BOTH are armed
NUCLEAR_ESCALATION = 2.2      # damage multiplier when one side is armed
NUCLEAR_USE_PER_WAR_YR = 0.004  # deliberately small; catastrophic if hit


@dataclass
class Governments:
    tax: np.ndarray            # per country 0..1
    welfare: np.ndarray        # generosity — becomes life.py's safety net
    policing: np.ndarray       # 0..1
    legitimacy: np.ndarray     # 0..1, the budget a government spends
    at_war_with: np.ndarray    # country index, -1 if at peace
    war_days: np.ndarray
    # What this country's people are USED TO. A government is judged
    # against the normal it inherited, not against an absolute constant.
    # Judging against a fixed 0.5 meant every state in a fearful world
    # bled legitimacy forever, cut welfare, deepened the fear, and lost
    # more legitimacy — a spiral with no floor and no basis in fact.
    unrest_norm: np.ndarray = None
    dep_norm: np.ndarray = None


@dataclass
class Class:
    homeless: np.ndarray
    criminal: np.ndarray
    days_homeless: np.ndarray
    crimes_committed: np.ndarray
    migrated: np.ndarray


def birth_institutions(civ, seed: int = 0):
    from earth1.genesis import GENESIS_COUNTRIES
    rng = np.random.default_rng(seed ^ 0x607)
    nc = len(GENESIS_COUNTRIES)
    tier = np.array([TIERS.index(c.get("income", "LMIC"))
                     if c.get("income") in TIERS else 2
                     for c in GENESIS_COUNTRIES])
    gov = Governments(
        tax=np.clip(0.42 - 0.08 * tier + rng.normal(0, 0.05, nc), 0.05, 0.65),
        welfare=np.clip(0.55 - 0.16 * tier + rng.normal(0, 0.06, nc),
                        0.02, 0.85),
        policing=np.clip(0.45 + 0.04 * tier + rng.normal(0, 0.08, nc),
                         0.05, 0.95),
        legitimacy=np.clip(0.65 - 0.05 * tier + rng.normal(0, 0.10, nc),
                           0.05, 0.98),
        at_war_with=np.full(nc, -1, dtype=np.int64),
        war_days=np.zeros(nc),
        unrest_norm=np.full(nc, 0.5), dep_norm=np.full(nc, 0.3))
    n = civ.n
    cls = Class(homeless=np.zeros(n, dtype=bool),
                criminal=np.zeros(n, dtype=bool),
                days_homeless=np.zeros(n, dtype=np.int32),
                crimes_committed=np.zeros(n, dtype=np.int32),
                migrated=np.zeros(n, dtype=bool))
    return gov, cls


_NUKE_CACHE = {}


def _nuclear_mask(nc: int) -> np.ndarray:
    """Which countries hold nuclear weapons."""
    if nc in _NUKE_CACHE:
        return _NUKE_CACHE[nc]
    from earth1.genesis import GENESIS_COUNTRIES
    m = np.array([c["iso2"] in NUCLEAR_STATES
                  for c in GENESIS_COUNTRIES[:nc]])
    _NUKE_CACHE[nc] = m
    return m


def govern(civ, life, gov: Governments, rng, dt_days: float = 1.0) -> dict:
    """Governments look at their people and decide what to do about it."""
    from earth1.genesis import GENESIS_COUNTRIES
    nc = len(GENESIS_COUNTRIES)
    dt_yr = dt_days / 365.0

    # what each government can see about its own population
    dep = np.bincount(civ.country, weights=np.clip(life.deprivation, 0, 1),
                      minlength=nc)
    pop = np.maximum(np.bincount(civ.country, minlength=nc), 1)
    dep = dep / pop
    unrest = np.bincount(civ.country,
                         weights=civ.forces[:, Force.FEAR], minlength=nc) / pop

    # THE DECISION. A government with legitimacy to spend answers
    # hardship with welfare. A government without it answers with
    # police. Same input, opposite policy, and which one it picks is
    # the single most consequential thing about a state.
    # A government spends when it has the standing AND the fiscal base
    # to do it. The threshold was 0.45 while legitimacy equilibrates
    # near 0.31, which left every state on Earth permanently in repress
    # mode — an artefact of the constant, not a finding about states.
    spend = (gov.legitimacy > 0.28) & (gov.tax > 0.22)
    gov.welfare = np.clip(
        gov.welfare + np.where(spend, 0.06, -0.02) * dep * dt_days, 0.02, 0.95)
    gov.policing = np.clip(
        gov.policing + np.where(spend, -0.01, 0.07) * unrest * dt_days,
        0.05, 0.99)
    gov.tax = np.clip(gov.tax + 0.02 * (gov.welfare - gov.tax) * dt_days,
                      0.05, 0.75)

    # the normal drifts slowly toward whatever is actually happening —
    # people habituate, and so does the standard a government is held to
    if gov.unrest_norm is None:
        gov.unrest_norm = unrest.copy()
        gov.dep_norm = dep.copy()
    a = 0.002 * dt_days
    gov.unrest_norm += a * (unrest - gov.unrest_norm)
    gov.dep_norm += a * (dep - gov.dep_norm)

    # legitimacy is earned and spent AGAINST THAT NORM: things getting
    # worse costs a government, things getting better restores it, and a
    # steady state costs nothing either way.
    gov.legitimacy = np.clip(
        gov.legitimacy + (0.10 * (gov.dep_norm - dep)
                          - 0.06 * (unrest - gov.unrest_norm))
        * 0.02 * dt_days, 0.02, 0.99)

    # ── war ──────────────────────────────────────────────────────────
    peace = gov.at_war_with < 0
    # afraid, illegitimate governments start wars. It is not a mystery.
    risk = WAR_ONSET_YR * (1.0 + 3.0 * unrest) * (1.0 + 2.0
                                                  * (1.0 - gov.legitimacy))
    starts = peace & (rng.random(nc) < risk * dt_yr)
    for ci in np.flatnonzero(starts):
        if gov.at_war_with[ci] >= 0:
            continue
        # pick a weaker neighbour: low legitimacy, at peace
        cand = np.flatnonzero(peace & (np.arange(nc) != ci)
                              & (gov.at_war_with < 0))
        if cand.size == 0:
            continue
        w = 1.0 / (0.1 + gov.legitimacy[cand])
        # DETERRENCE. No two nuclear-armed states have fought a full
        # interstate war. Whether that is causation or a seventy-year
        # coincidence is genuinely disputed, so this is a weight rather
        # than a prohibition — a nuclear state can still be attacked
        # here, just far less often.
        nuke = _nuclear_mask(nc)
        if nuke[ci]:
            w = w * np.where(nuke[cand], DETERRENCE_FACTOR, 1.0)
        target = int(rng.choice(cand, p=w / w.sum()))
        gov.at_war_with[ci] = target
        gov.at_war_with[target] = ci
        gov.war_days[[ci, target]] = 0.0

    at_war = gov.at_war_with >= 0
    gov.war_days[at_war] += dt_days
    ends = at_war & (rng.random(nc) < WAR_END_YR * dt_yr)
    for ci in np.flatnonzero(ends):
        other = gov.at_war_with[ci]
        gov.at_war_with[ci] = -1
        if other >= 0:
            gov.at_war_with[other] = -1

    return {"mean_welfare": float(gov.welfare.mean()),
            "mean_policing": float(gov.policing.mean()),
            "mean_legitimacy": float(gov.legitimacy.mean()),
            "countries_at_war": int(at_war.sum()),
            "wars_started": int(starts.sum())}


def apply_policy_and_war(civ, life, gov: Governments, health, rng,
                         dt_days: float = 1.0) -> dict:
    """Policy and war stop being abstractions and land on people."""
    nc = gov.welfare.size
    war_here = gov.at_war_with[civ.country] >= 0
    dt_yr = dt_days / 365.0

    # welfare generosity replaces the constant safety net: an agent out
    # of work in a generous country is simply less destitute than the
    # same agent in a mean one, and that is a POLICY, not a constant.
    life.policy_net = gov.welfare[civ.country]

    killed = np.zeros(civ.n, dtype=bool)
    conscripted = 0
    if war_here.any():
        # war wrecks the firms
        firm_at_war = gov.at_war_with[life.firm_country] >= 0
        life.firm_health[firm_at_war] = np.clip(
            life.firm_health[firm_at_war] - 0.02 * dt_days, 0.0, 1.0)
        # ESCALATION CEILING. When one side holds nuclear weapons the
        # war is fought harder, and there is a small chance per year of
        # actual use — which is catastrophic rather than merely severe.
        nuke = _nuclear_mask(nc)
        asymmetric = war_here & (
            nuke[civ.country] ^ nuke[gov.at_war_with[civ.country].clip(0)])
        if asymmetric.any():
            firm_esc = asymmetric & (life.firm_country >= 0)
            life.firm_health[firm_esc] = np.clip(
                life.firm_health[firm_esc]
                - 0.02 * (NUCLEAR_ESCALATION - 1.0) * dt_days, 0.0, 1.0)
        # war conscripts the young
        young = war_here & (civ.age < 0.35) & life.in_lf
        conscripted = int(young.sum())
        # and war kills them
        p_die = 0.02 * dt_yr
        killed = young & (rng.random(civ.n) < p_die)
        if health is not None and killed.any():
            health.alive[killed] = False
            health.cause_of_death[killed] = 5     # war
        # everyone in a country at war is more afraid and more collective
        civ.forces[war_here, Force.FEAR] = np.clip(
            civ.forces[war_here, Force.FEAR] + 0.03 * dt_days, 0, 1)
        civ.forces[war_here, Force.COLLECTIVE] = np.clip(
            civ.forces[war_here, Force.COLLECTIVE] + 0.02 * dt_days, 0, 1)

    return {"people_at_war": int(war_here.sum()),
            "conscripted": conscripted,
            "war_deaths": int(killed.sum())}


def class_tick(civ, life, kn, gov: Governments, cls: Class, rng,
               dt_days: float = 1.0, alive=None) -> dict:
    """Homelessness, crime, and the compounding of wealth."""
    n = civ.n
    live = alive if alive is not None else np.ones(n, dtype=bool)
    dep = np.clip(life.deprivation, 0, 1)
    deg = np.asarray(civ.adj.sum(axis=1)).ravel()
    net = gov.welfare[civ.country]

    # ── homelessness: it is the CONJUNCTION that does it ─────────────
    # broke, alone, and nobody catching you. Poverty alone almost never
    # puts a person on the street.
    alone = life.relationship < 0.25 if life.relationship is not None else \
        (deg < 3)
    exposed = (life.wealth < -20.0) & alone & (net < 0.4)
    # Entry and exit set the equilibrium, and the first pair ratcheted
    # to 5.7% against a real-world figure near 0.2%. Most people who
    # lose housing regain it within months; the tail is what is hard.
    becomes = live & exposed & ~cls.homeless \
        & (rng.random(n) < 0.0015 * dt_days)
    # you get out when money OR people come back
    exits = cls.homeless & ((life.wealth > 5.0) | ~alone) \
        & (rng.random(n) < 0.035 * dt_days)
    cls.homeless = (cls.homeless | becomes) & ~exits
    cls.days_homeless += cls.homeless
    if becomes.any():
        life.mental[becomes] = np.clip(life.mental[becomes] - 0.20, 0, 1)

    # ── crime: pressure, opportunity, and nothing left to lose ───────
    status = kn.status if kn is not None else np.full(n, 0.5)
    push = 0.6 * dep + 0.3 * (1.0 - life.mental) + 0.3 * life.addiction
    pull = 0.8 * gov.policing[civ.country] + 0.6 * status
    p = np.clip(0.05 * (push - 0.4 * pull), 0.0, 1.0) * dt_days / 30.0
    commits = live & (rng.random(n) < p)
    cls.crimes_committed += commits
    cls.criminal |= cls.crimes_committed >= 3

    # ── wealth compounds ─────────────────────────────────────────────
    # returns accrue to those who already have a buffer. This is why the
    # top pulls away instead of drifting, and it needs no conspiracy.
    has = life.wealth > 30.0
    life.wealth[has] *= (1.0 + 0.00012 * dt_days)

    # ── migration: leave when staying is worse ───────────────────────
    from earth1.genesis import GENESIS_COUNTRIES
    nc = len(GENESIS_COUNTRIES)
    pop = np.maximum(np.bincount(civ.country, minlength=nc), 1)
    country_dep = np.bincount(civ.country, weights=dep, minlength=nc) / pop
    better = country_dep[civ.country] - country_dep.min()
    want = live & (dep > 0.5) & (civ.age < 0.5)
    goes = want & (rng.random(n) < MIGRATION_RATE_YR * (1.0 + 3.0 * better)
                   * dt_days / 365.0)
    moved = 0
    if goes.any():
        dest_pool = np.argsort(country_dep)[:25]     # the calmer quarter
        idx = np.flatnonzero(goes)
        civ.country[idx] = rng.choice(dest_pool, idx.size)
        cls.migrated[idx] = True
        # arriving costs you your ties and your job
        life.employed[idx] = False
        life.firm[idx] = -1
        moved = int(idx.size)

    return {"homeless": float(cls.homeless[live].mean()),
            "became_homeless": int(becomes.sum()),
            "crimes_today": int(commits.sum()),
            "criminal_share": float(cls.criminal[live].mean()),
            "migrated_today": moved,
            "wealth_gini": _gini(np.clip(life.wealth[live], 0, None))}


def _gini(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    s = np.sort(x)
    i = np.arange(1, s.size + 1)
    d = s.sum()
    return float(round((2 * (i * s).sum()) / (s.size * d)
                       - (s.size + 1) / s.size, 4)) if d > 0 else 0.0
