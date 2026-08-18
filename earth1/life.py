"""LIFE — the material substrate. Earthlings with biographies.

Every measurement this week said the same thing: the population earns
nothing. MrsP matched it on less information, mean-agent equivalence
reproduced it from one row per country, the camp diagnostic found 39 of
40 questions decorative, and the threshold detector found that nowhere
on Earth-1 do 30% of agents jointly occupy an extreme state.

They all have one cause. An agent is a STATIC DRAW. It has attributes
and no biography. Two agents born identical stay identical forever,
because nothing that happens to one of them happens only to them. A
population like that has no tail, and with no tail there is nothing for
a threshold to detect, nothing for a cascade to propagate, and nothing
a country-level regression cannot reproduce.

This module gives them lives.

  WORK        an occupation, a wage, a firm, a tenure
  MONEY       wealth measured in days of survival held in reserve
  NEEDS       food, shelter, the daily cost of staying alive
  PRECARITY   job loss, and the compounding that follows it

THE MECHANISM THAT MATTERS — CORRELATED SHOCKS.

If misfortune were independent across agents, it would average out and
the population would stay Gaussian: exactly the world we have now. Real
hardship does not arrive independently. A firm fails and four hundred
people lose their income in the same week; they share a town, they
drink in the same bars, their children attend the same school. That is
why real societies have fat tails and Earth-1 does not.

So shocks here arrive THROUGH STRUCTURE. Firms carry health, firms fail,
and failure lays off everyone inside at once. The graph then carries
the consequence outward. Compounding does the rest: an agent who loses
a job drains reserves, and a drained agent cannot absorb the next shock,
so trajectories that began together separate and do not reconverge.

Nothing here is tuned to produce a result. The parameters are ordinary
labour-economics magnitudes, named and defended at the point of use, and
the test that grades this module is registered before it runs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.types import Civilization, Force

# ── occupations ───────────────────────────────────────────────────────
# (label, wage multiple of national median, separation hazard multiple,
#  education affinity). Wage multiples are ordinary occupational
# dispersion; the hazard column encodes that manual and service work is
# separated from far more often than professional work, which is the
# single most important asymmetry for who ends up in the tail.
OCCUPATIONS = [
    ("subsistence_agriculture", 0.45, 1.30, 0),
    ("manual_labour",           0.70, 1.60, 0),
    ("service",                 0.85, 1.45, 0),
    ("trades",                  1.05, 1.00, 1),
    ("clerical",                1.00, 0.90, 1),
    ("sales",                   0.95, 1.20, 1),
    ("care_and_teaching",       1.10, 0.55, 1),
    ("technical",               1.45, 0.70, 2),
    ("professional",            1.90, 0.45, 2),
    ("management",              2.40, 0.50, 2),
]
OCC_NAMES = [o[0] for o in OCCUPATIONS]
OCC_WAGE = np.array([o[1] for o in OCCUPATIONS])
OCC_HAZARD = np.array([o[2] for o in OCCUPATIONS])
OCC_EDU = np.array([o[3] for o in OCCUPATIONS])

# ── rates, per year, converted to the tick's dt ───────────────────────
# 12%/yr baseline job separation: mid-range for OECD job destruction
# plus voluntary quits.
#
# FINDING is a per-SPELL hazard, not a per-job one, and the first
# version of this module set it to 0.55/yr as if it were the same kind
# of quantity. Steady-state unemployment is sep/(sep+find), so 0.12 and
# 0.55 imply 18% unemployment and roughly two-year job searches — and
# the simulation duly converged there. It was obeying the parameter, not
# malfunctioning. Real median spells are months: 3.0/yr means a mean
# search near four months and a steady state near 4%.
SEPARATION_RATE_YR = 0.12
FINDING_RATE_YR = 3.0
FIRM_FAILURE_RATE_YR = 0.08      # ~8%/yr business exit, all sizes
AGENTS_PER_FIRM = 24             # mean; sizes are heavy-tailed below

# Unemployment income as a fraction of the previous wage, by country
# income tier. This is the welfare state, and it is the strongest
# single lever on whether hardship becomes destitution.
SAFETY_NET = {"HIC": 0.55, "UMIC": 0.30, "LMIC": 0.15, "LIC": 0.05}

# Where the welfare state is absent, the informal economy is not. A
# subsistence farmer who loses a wage job does not drop to zero income;
# they farm, they trade, they are paid in cash off the books. Leaving
# this out was an error in the first version of this module and it drove
# destitution to 30% — the poorest countries were modelled as having
# neither benefits nor informal work, which describes nowhere on Earth.
# The two are near-complements: informal share is HIGHEST where the
# safety net is weakest.
INFORMAL = {"HIC": 0.18, "UMIC": 0.35, "LMIC": 0.55, "LIC": 0.70}

# A household spends most of its income staying alive; the poorer the
# country the higher that share (Engel's law).
COST_SHARE = {"HIC": 0.72, "UMIC": 0.80, "LMIC": 0.88, "LIC": 0.94}

# Wealth is measured in DAYS OF SURVIVAL — how long this agent could pay
# for food and shelter with income cut to zero. Scale-free across
# countries, no fake currency conversion, and it is the quantity that
# actually determines who breaks when a shock lands.
# Households save a modest share of what they have left after survival
# costs and consume the rest. Without this, everyone employed
# accumulates reserves forever.
SAVE_RATE = 0.12

DESTITUTE_BUFFER = 3.0           # under 3 days of reserve = destitute

# How strongly accumulated trait change moves the force baseline. This
# is the gain on the return leg trait -> force, and it is what makes
# experience permanent rather than a transient the world relaxes away.
TRAIT_MEMORY = 1.0


@dataclass
class Life:
    """Per-agent material state. Struct-of-arrays, like Civilization."""
    occupation: np.ndarray       # int, index into OCCUPATIONS
    firm: np.ndarray             # int, -1 when not employed
    employed: np.ndarray         # bool
    in_lf: np.ndarray            # bool, in the labour force at all
    wage: np.ndarray             # float, daily, in units of daily cost
    wealth: np.ndarray           # float, DAYS of survival in reserve
    cost: np.ndarray             # float, daily cost of living (= 1.0 base)
    tenure: np.ndarray           # float, days in the current job
    deprivation: np.ndarray      # float 0..1, unmet need
    spells: np.ndarray           # int, lifetime count of job losses
    firm_health: np.ndarray      # float per FIRM, not per agent
    firm_country: np.ndarray     # int per firm
    # The force state the agent was BORN with. Material condition maps
    # to a force LEVEL relative to this baseline; it is never integrated
    # into the force. Getting that wrong is what pinned 99% of agents to
    # a clip bound in the first run of this module.
    force_baseline: np.ndarray = None    # (N, 8)
    # Traits as they were at birth. What an agent has LIVED THROUGH is
    # the drift away from these, and that drift is fed back into the
    # force baseline so experience leaves a permanent mark. Without this
    # the ring is open — world_step writes force into trait, and nothing
    # ever reads trait back into force, so memory goes to a dead end and
    # two worlds always reconverge onto the same attractor.
    trait_baseline: np.ndarray = None    # (N, 3): openness, doubt, desire

    @property
    def n_firms(self) -> int:
        return int(self.firm_health.size)


def _tier(civ: Civilization) -> np.ndarray:
    """Country income tier per agent, as an index into the rate tables."""
    from earth1.genesis import GENESIS_COUNTRIES
    order = ["HIC", "UMIC", "LMIC", "LIC"]
    per_country = np.array([order.index(c.get("income", "LMIC"))
                            if c.get("income") in order else 2
                            for c in GENESIS_COUNTRIES])
    return per_country[civ.country]


def birth_life(civ: Civilization, seed: int = 0) -> Life:
    """Give a freshly created population its material starting point."""
    rng = np.random.default_rng(seed ^ 0x11FE)
    n = civ.n

    # occupation: education sets the affinity, but never determines it —
    # people work outside their credential in every real labour market,
    # and that slack is a genuine source of within-cohort variance.
    aff = np.exp(-1.2 * np.abs(OCC_EDU[None, :] - civ.education[:, None]))
    p = aff / aff.sum(axis=1, keepdims=True)
    occupation = np.array([rng.choice(len(OCCUPATIONS), p=row) for row in p]) \
        if n <= 20_000 else _fast_categorical(p, rng)

    tier = _tier(civ)
    cost_share = np.array([COST_SHARE[k] for k in
                           ["HIC", "UMIC", "LMIC", "LIC"]])[tier]

    # Wage in units of the agent's own daily cost of living. An agent on
    # the national median in a country spending 80% of income on
    # survival has a wage of 1/0.8 = 1.25 daily costs.
    lognormal = np.exp(rng.normal(0.0, 0.35, n))      # within-occupation
    wage = OCC_WAGE[occupation] * lognormal / cost_share
    cost = np.ones(n)

    # LABOUR FORCE first, employment second. Conflating the two was an
    # error in the first version: retirees, students and full-time
    # carers were counted as unemployed, which both inflated the
    # unemployment rate and put people into a job search they are not
    # in. Someone outside the labour force is not looking for work and
    # is not failing to find it.
    in_lf = (civ.age <= 0.78) & (rng.random(n) > 0.28)
    employed = in_lf & (rng.random(n) > 0.09)

    # firms, with heavy-tailed sizes assigned WITHIN country so a firm
    # failure is a local event rather than a global one
    n_firms = max(1, n // AGENTS_PER_FIRM)
    firm_country = civ.country[rng.integers(0, n, n_firms)]
    firm = np.full(n, -1, dtype=np.int64)
    for ci in np.unique(civ.country):
        agents = np.flatnonzero((civ.country == ci) & employed)
        firms_here = np.flatnonzero(firm_country == ci)
        if agents.size == 0 or firms_here.size == 0:
            continue
        # Zipf-ish draw: most people work for the few large employers
        w = 1.0 / (1.0 + np.arange(firms_here.size))
        firm[agents] = rng.choice(firms_here, size=agents.size, p=w / w.sum())
    firm_health = rng.uniform(0.45, 1.0, n_firms)

    # starting reserves: heavy-tailed and correlated with wage, because
    # the people with the least income also have the least buffer — that
    # correlation is what turns one bad month into destitution
    wealth = np.clip(rng.gamma(1.6, 12.0, n) * (0.4 + 0.6 * wage / wage.mean()),
                     0.0, 4000.0)
    tenure = rng.exponential(700.0, n) * employed

    return Life(occupation=occupation, firm=firm, employed=employed,
                in_lf=in_lf, wage=wage, wealth=wealth, cost=cost, tenure=tenure,
                deprivation=np.zeros(n), spells=np.zeros(n, dtype=np.int32),
                firm_health=firm_health, firm_country=firm_country,
                force_baseline=civ.forces.copy(),
                trait_baseline=np.stack([civ.openness, civ.doubt,
                                         civ.desire_intensity], axis=1))


def _fast_categorical(p: np.ndarray, rng) -> np.ndarray:
    """Vectorized per-row categorical draw (rng.choice is per-row slow)."""
    c = np.cumsum(p, axis=1)
    u = rng.random((p.shape[0], 1))
    return (u > c).sum(axis=1).clip(0, p.shape[1] - 1)


def life_tick(civ: Civilization, life: Life, rng, dt_days: float = 1.0,
              couple_forces: bool = True) -> dict:
    """One day of material life. Returns what happened, for the log.

    Order matters: firms fail before individuals are separated, so a
    failure and its layoffs land in the same tick and the resulting
    hardship is CORRELATED across everyone in that firm. That is the
    whole mechanism — see the module docstring.
    """
    n = civ.n
    dt_yr = dt_days / 365.0
    tier = _tier(civ)

    # DRAW ALIGNMENT. Every random quantity is drawn at FULL SIZE up
    # front, so an agent's draws never depend on how many other agents
    # happened to act this tick. Without this, perturbing one agent
    # shifts the random stream for everyone after it and the butterfly
    # test measures desynchronisation instead of causation.
    u_sep = rng.random(n)
    u_find = rng.random(n)
    u_firmpick = rng.random(n)
    u_fail = rng.random(life.n_firms)
    z_health = rng.normal(0.0, 0.02, life.n_firms)
    u_reseed = rng.uniform(0.4, 0.9, life.n_firms)

    # ── 1. firms fail, and take everyone inside with them ─────────────
    # Failure hazard falls with firm health, so weak firms go first and
    # a downturn (health pushed down globally) produces a WAVE rather
    # than a trickle.
    fail_p = FIRM_FAILURE_RATE_YR * dt_yr * (2.0 - life.firm_health)
    failed = np.flatnonzero(u_fail < fail_p)
    laid_off = np.zeros(n, dtype=bool)
    if failed.size:
        laid_off = np.isin(life.firm, failed) & life.employed

    # ── 2. individual separation, hazard by occupation and tenure ─────
    # New hires are let go first; this is why a recent job-loser is more
    # likely to lose the next one too, and how spells compound.
    sep_base = SEPARATION_RATE_YR * dt_yr * OCC_HAZARD[life.occupation]
    tenure_mult = 1.0 + 1.5 * np.exp(-life.tenure / 365.0)
    sep = (u_sep < sep_base * tenure_mult) & life.employed & ~laid_off

    lost = laid_off | sep
    life.employed[lost] = False
    life.firm[lost] = -1
    life.tenure[lost] = 0.0
    life.spells[lost] += 1

    # ── 3. the unemployed look for work ───────────────────────────────
    # Finding gets harder the longer the spell and the more spells you
    # have already had — scarring, which is well documented and is the
    # mechanism that makes the bottom tail STICKY instead of transient.
    idle = ~life.employed & life.in_lf
    # Scarring with a FLOOR. Unbounded scarring meant that after a few
    # spells an agent's finding rate went to ~zero and unemployment
    # ratcheted upward forever instead of equilibrating. Real long-term
    # unemployed people do find work; they find it more slowly.
    scar = np.maximum(1.0 / (1.0 + 0.25 * life.spells), 0.35)
    find_p = FINDING_RATE_YR * dt_yr * scar
    found = idle & (u_find < find_p)
    if found.any():
        life.employed[found] = True
        idx = np.flatnonzero(found)
        for ci in np.unique(civ.country[idx]):
            who = idx[civ.country[idx] == ci]
            firms_here = np.flatnonzero((life.firm_country == ci)
                                        & (life.firm_health > 0.25))
            if firms_here.size:
                pick = (u_firmpick[who] * firms_here.size).astype(np.int64)
                life.firm[who] = firms_here[np.minimum(pick,
                                                      firms_here.size - 1)]

    life.tenure[life.employed] += dt_days

    # ── 4. income, needs, and the buffer ──────────────────────────────
    keys = ["HIC", "UMIC", "LMIC", "LIC"]
    net = np.array([SAFETY_NET[k] for k in keys])[tier]
    informal = np.array([INFORMAL[k] for k in keys])[tier]
    # An agent out of formal work falls back on whichever is better: the
    # welfare state, or the informal economy. Modelling only the former
    # made the poorest countries destitute by construction.
    fallback = np.maximum(net, informal)
    # Outside the labour force is not the same as jobless: pensions,
    # family support and household pooling carry these agents.
    fallback = np.where(life.in_lf, fallback, np.maximum(fallback, 0.75))
    income = np.where(life.employed, life.wage, life.wage * fallback)
    # wealth is denominated in DAYS of survival, so the flow is
    # (income - cost) / cost days added per day
    # People spend most of what they earn. Banking the entire surplus
    # every day made median reserves grow without bound (93 days after
    # one year) while a separate group starved — a bimodality that was
    # an artefact of nobody ever consuming above subsistence.
    surplus = np.maximum(income - life.cost, 0.0)
    shortfall = np.minimum(income - life.cost, 0.0)
    saved = SAVE_RATE * surplus + shortfall
    life.wealth += saved * dt_days / np.maximum(life.cost, 1e-9)
    life.wealth = np.clip(life.wealth, -400.0, 1e6)

    # ── 5. deprivation ────────────────────────────────────────────────
    # 1.0 when the buffer is gone entirely, tapering to 0 at the point
    # where an agent could survive DESTITUTE_BUFFER days unpaid.
    # Deprivation requires BOTH that current income fails to cover
    # survival AND that there is no reserve left. An agent working a
    # low wage with no savings is precarious, not destitute; the first
    # version labelled everyone living paycheck to paycheck as
    # destitute, which is what drove the rate near 40%.
    covers = income >= life.cost
    life.deprivation = np.where(
        covers, 0.0, np.clip(1.0 - life.wealth / DESTITUTE_BUFFER, 0.0, 1.0))

    # ── 6. firm health drifts, and recovers slowly ────────────────────
    life.firm_health = np.clip(
        life.firm_health + z_health
        + 0.004 * (0.8 - life.firm_health), 0.0, 1.0)
    if failed.size:
        life.firm_health[failed] = u_reseed[failed]

    stats = {"laid_off": int(laid_off.sum()), "separated": int(sep.sum()),
             "found_work": int(found.sum()), "firms_failed": int(failed.size),
             "unemployment": float((~life.employed & life.in_lf).sum()
                                   / max(life.in_lf.sum(), 1)),
             "destitute": float((life.deprivation > 0.99).mean()),
             "deprived": float((life.deprivation > 0.5).mean()),
             "median_buffer_days": float(np.median(life.wealth))}

    if couple_forces:
        stats.update(couple_life_to_forces(civ, life))
    return stats


def life_force_target(civ: Civilization, life: Life) -> np.ndarray:
    """The force state this agent's CIRCUMSTANCES imply, right now.

    Returned rather than applied, because the social layer needs it as a
    RESTORING TARGET rather than an overwrite. An agent is pushed around
    by the people they know and pulled back by the life they actually
    live; the tension between those two is where the interesting
    dynamics are. A world with only the push saturates to the poles and
    freezes. A world with only the pull is a spreadsheet.
    """
    dep = life.deprivation
    base = life.force_baseline
    if base is None:
        return civ.forces.copy()

    # EXPERIENCE MOVES THE BASELINE. An agent who has lived through
    # something does not return to who they were; their circumstances
    # now pull them toward a different place than they were born to.
    # This is the return leg of the ring: trait -> force baseline.
    if life.trait_baseline is not None:
        cur = np.stack([civ.openness, civ.doubt, civ.desire_intensity],
                       axis=1)
        drift = cur - life.trait_baseline
        base = base.copy()
        base[:, Force.CULTURE] = np.clip(
            base[:, Force.CULTURE] + TRAIT_MEMORY * drift[:, 0], 0.0, 1.0)
        base[:, Force.FEAR] = np.clip(
            base[:, Force.FEAR] + TRAIT_MEMORY * drift[:, 1], 0.0, 1.0)
        base[:, Force.DESIRE] = np.clip(
            base[:, Force.DESIRE] + TRAIT_MEMORY * drift[:, 2], 0.0, 1.0)
    buffer_ok = np.clip(life.wealth / 90.0, 0.0, 1.0)
    precarity = (~life.employed).astype(float) * 0.6 + \
        np.clip(life.spells / 4.0, 0.0, 1.0) * 0.4
    adj = civ.adj
    deg = np.asarray(adj.sum(axis=1)).ravel()
    shared = np.asarray(adj @ dep).ravel() / np.maximum(deg, 1.0)

    t = base.copy()
    t[:, Force.ECONOMICS] = np.clip(
        base[:, Force.ECONOMICS] - 0.45 * dep + 0.20 * buffer_ok, 0.0, 1.0)
    t[:, Force.FEAR] = np.clip(
        base[:, Force.FEAR] + 0.35 * precarity + 0.25 * dep, 0.0, 1.0)
    t[:, Force.DESIRE] = np.clip(
        base[:, Force.DESIRE] - 0.30 * dep, 0.0, 1.0)
    t[:, Force.COLLECTIVE] = np.clip(
        base[:, Force.COLLECTIVE] + 0.40 * dep * shared, 0.0, 1.0)
    return t


def couple_life_to_forces(civ: Civilization, life: Life) -> dict:
    """Material condition becomes force state.

    These couplings are structural claims about people, each one
    defensible on its own, and none of them fitted to a target:

      ECONOMICS  falls with deprivation and rises with a real buffer.
                 This is the channel that was previously identical for
                 every citizen of a country.
      FEAR       rises with precarity — being out of work, and having
                 been out of work before. Insecurity, not poverty, is
                 what fear tracks.
      DESIRE     falls under deprivation. Aspiration is what people
                 give up first when survival is in question.
      COLLECTIVE rises with SHARED hardship. An agent who is suffering
                 alone withdraws; an agent suffering alongside their
                 whole town turns toward the group. This is the term
                 that makes deprivation socially contagious instead of
                 individually absorbed, and it is why correlated shocks
                 matter more than their average size.

    LEVEL MAP, NOT ACCUMULATION. Force is set to the agent's birth
    baseline plus a term in CURRENT material condition. It is never
    incremented in place. The first version of this module incremented,
    and after ninety ticks 99% of agents sat exactly on a clip bound —
    a wall, not a tail. An agent whose fortunes recover must come back
    down the force axis, and only a level map does that.
    """
    dep, f = life.deprivation, civ.forces
    base = life.force_baseline
    if base is None:                       # legacy state, nothing to do
        return {}
    buffer_ok = np.clip(life.wealth / 90.0, 0.0, 1.0)
    precarity = (~life.employed).astype(float) * 0.6 + \
        np.clip(life.spells / 4.0, 0.0, 1.0) * 0.4

    # SHARED HARDSHIP, READ OFF THE GRAPH — not off the country.
    #
    # The first version averaged deprivation over the whole country.
    # That is an averaging channel, and the butterfly test proved what
    # averaging does: one agent losing their job perturbed 68 others at
    # its peak and then the worlds RECONVERGED, Lyapunov -0.0265/day.
    # A country mean over ~258 agents moves by 1/258 when one person
    # falls, which is a contraction, not a transmission.
    #
    # Reading it off the social graph instead means hardship reaches the
    # people who actually know you — colleagues, neighbours, friends —
    # at full strength rather than diluted by everyone who does not.
    # That is the difference between a statistic and a society.
    adj = civ.adj
    deg = np.asarray(adj.sum(axis=1)).ravel()
    shared = np.asarray(adj @ dep).ravel() / np.maximum(deg, 1.0)
    # agents with no ties fall back on the country, which is the only
    # honest thing to say about someone with nobody around them
    lonely = deg < 1
    if lonely.any():
        for ci in np.unique(civ.country[lonely]):
            m = lonely & (civ.country == ci)
            shared[m] = dep[civ.country == ci].mean()

    before = f[:, Force.ECONOMICS].std()
    f[:, Force.ECONOMICS] = np.clip(
        base[:, Force.ECONOMICS] - 0.45 * dep + 0.20 * buffer_ok, 0.0, 1.0)
    f[:, Force.FEAR] = np.clip(
        base[:, Force.FEAR] + 0.35 * precarity + 0.25 * dep, 0.0, 1.0)
    f[:, Force.DESIRE] = np.clip(
        base[:, Force.DESIRE] - 0.30 * dep, 0.0, 1.0)
    f[:, Force.COLLECTIVE] = np.clip(
        base[:, Force.COLLECTIVE] + 0.40 * dep * shared, 0.0, 1.0)

    return {"economics_std_before": float(before),
            "economics_std_after": float(f[:, Force.ECONOMICS].std())}
