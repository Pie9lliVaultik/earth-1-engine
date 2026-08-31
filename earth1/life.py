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

import os

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
INFORMAL_SCALE = 1.0           # calibratable scale on the floors above (<=0.95 after scaling)

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

# HOUSING. The largest line in almost every household budget, and the
# main road to the street — which is why treating cost of living as one
# undifferentiated number hid the single most important mechanism in
# material life. Rent is a fixed claim that arrives whether or not you
# earned anything, and losing it is what actually makes a person
# homeless.
RENT_SHARE = {"HIC": 0.34, "UMIC": 0.30, "LMIC": 0.26, "LIC": 0.22}
OWNER_SHARE = {"HIC": 0.62, "UMIC": 0.60, "LMIC": 0.68, "LIC": 0.74}
ARREARS_TO_EVICTION = 90.0     # days behind before you lose the home

# ── DURABLES ─────────────────────────────────────────────────────────
# Furniture, appliances, a bed that is not a mattress on the floor.
# These earn their place for a reason that has nothing to do with
# scenery: durable goods are the FIRST thing a household stops buying
# when it is frightened, which is why furniture and appliance orders are
# a classic leading recession indicator. They lead precisely because
# they are deferrable — you can eat next month's dinner but you cannot
# defer it, whereas a sofa waits forever.
#
# So durables are in on two channels: a discretionary spend that
# collapses on fear before income has even fallen (the leading
# indicator), and a stock that quietly carries dignity — a home with
# nothing in it is a different place to live than a furnished one.
DURABLE_SHARE = 0.06           # of a comfortable budget
DURABLE_DECAY_YR = 0.10        # things wear out

DESTITUTE_BUFFER = 3.0           # under 3 days of reserve = destitute
# Deprivation form: "cliff" = canonical v4.1 (binary gate); "gradient" =
# depth-of-shortfall candidate (ops/alive/HARDSHIP_GRADIENT_IMPACT.md).
# Default stays canonical: no deployed physics changes without a ruling.
HARDSHIP_MODE = os.environ.get("EARTH1_HARDSHIP_MODE", "cliff")

# DISTRESS LAYOFFS (c-SHOCK named change, ops/alive/cycles/cshock.md).
# A firm in sudden decline sheds workers before it dies. Without this
# the only shock->jobs path is total firm failure, whose hazard tops
# out at 2x baseline even for a maximum shock — which is how a
# covid-scale scenario destroyed -24±671 jobs on a 200k world. The
# detector is a DROP against the firm's own trailing health (EMA), so
# it is exactly zero at any steady state: baseline unemployment
# anchors are untouched by construction. The deadband sits ~5x the
# daily health-noise sigma (0.02) so steady-state noise never fires.
DISTRESS_LAYOFFS = os.environ.get("EARTH1_DISTRESS_LAYOFFS", "off")
LAYOFF_GAIN = float(os.environ.get("EARTH1_LAYOFF_GAIN", "0.0"))
LAYOFF_EMA_TAU = 30.0
LAYOFF_DEADBAND = 0.10

# INCOME CALIBRATION (M-INCOME-SCALE, 2026-08-27). Earth-1's income
# distribution was ~2.5x too low and less than half as unequal as the
# world: median 1.23x subsistence vs a fetched 3.09x, total log-sd
# 0.614 vs a fetched 1.301. Constants are DERIVED from World Bank / PIP
# anchors (data/income_calibration.json, data/anchors_worldbank.json);
# poverty headcounts are not targeted and remain the test. Default is
# canonical v4.1 (off): no deployed physics change without a ruling.
INCOME_CALIBRATION = os.environ.get("EARTH1_INCOME_CALIBRATION", "off")
# Substrate-keyed (founder ruling 2026-08-27): a constant derived on one
# substrate must never silently apply to another. The file is
# income_calibration.<substrate>.json, its "substrate" field must match
# the active tag, and genesis() cross-checks its substrate argument
# against this tag at world birth.
INCOME_SUBSTRATE_TAG = {"off": "incumbent", "": "incumbent"}.get(
    os.environ.get("EARTH1_SUBSTRATE_FLAG", "off"),
    os.environ.get("EARTH1_SUBSTRATE_FLAG", "off"))
if INCOME_CALIBRATION == "v1":
    import json as _json
    _p = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", f"income_calibration.{INCOME_SUBSTRATE_TAG}.json")
    if not os.path.exists(_p):
        raise RuntimeError(
            f"income calibration for substrate {INCOME_SUBSTRATE_TAG!r} "
            f"does not exist ({_p}); derive it before enabling "
            f"EARTH1_INCOME_CALIBRATION on this substrate")
    _cal = _json.load(open(_p))
    if _cal.get("substrate") != INCOME_SUBSTRATE_TAG:
        raise RuntimeError(
            f"substrate tag mismatch: file says {_cal.get('substrate')!r}, "
            f"active is {INCOME_SUBSTRATE_TAG!r}")
    WAGE_LEVEL = float(_cal["WAGE_LEVEL"])
    WAGE_LOG_SD = float(_cal["WAGE_LOG_SD"])
else:
    WAGE_LEVEL, WAGE_LOG_SD = 1.0, 0.35

# How strongly accumulated trait change moves the force baseline. This
# is the gain on the return leg trait -> force, and it is what makes
# experience permanent rather than a transient the world relaxes away.
TRAIT_MEMORY = 1.0

# COLLECTIVE-GEO-1 (founder-authorized, flag-gated experimental
# candidate): centered-deviation COLLECTIVE target. Baseline encodes
# normal state; modifiers encode DEPARTURES from the registered
# reference centers (measured once from birth_world(200000, 424242)
# at day 0 — FIXED constants, never recomputed from the running
# population). Slopes unchanged; see ops/alive/COLLECTIVE_GEO_1.md.
GEO1_REF_DS = 0.0
GEO1_REF_POL = 0.3998
GEO1_REF_SN = 0.2855
GEO1_REF_BEL = 0.6416
# Parameter registry (Bible III.6): the four COLLECTIVE modifier slopes
# (0.40 shared-hardship, 0.25 political, 0.20 social_need, 0.20
# belonging) are AUTHORED / EXPERIMENTAL — requires parameter
# provenance; the reference centers are reference-population-derived;
# the genesis baseline is empirical. Canonical == validated candidate
# 76a574c (COLLECTIVE-GEO-1 PASS); canonical does not mean validated.

# ── prevalence anchors, from real epidemiology ───────────────────────
# These are population base rates, not tuned values. Onset hazards below
# are modulated by deprivation and isolation, both of which the model
# computes — so the DISTRIBUTION is emergent even though the level is
# anchored to reality.
MENTAL_ILLNESS_PREV = 0.13        # GBD: ~13% any mental disorder
SUBSTANCE_DEP_PREV = 0.023        # WHO: ~2.3% substance use disorder
CRIME_VICTIM_YR = 0.045           # UN ICVS: ~4.5%/yr contact+property
PARTNERED_SHARE = 0.55

EVENT_CODES = {0: "nothing", 1: "job_loss", 2: "found_work",
               3: "crime_victim", 4: "bereavement", 5: "new_child",
               6: "addiction_onset", 7: "recovery", 8: "breakup"}


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
    # ── the body and the self (Layer 1) ──────────────────────────────
    mental: np.ndarray = None        # 0..1, modulates every susceptibility
    physical: np.ndarray = None      # 0..1
    addiction: np.ndarray = None     # 0..1, LOCKS the desire channel
    relationship: np.ndarray = None  # 0=isolated .. 1=deeply connected
    social_need: np.ndarray = None   # unmet connection, feeds COLLECTIVE
    political: np.ndarray = None     # engagement, modulates COLLECTIVE
    # Where this person's mental health and connectedness SIT when
    # nothing is happening to them. Modelling these as purely
    # circumstantial let everyone heal to the ceiling and put lifetime
    # prevalence at 0.9% against GBD's 13%. Mental illness is ~40%
    # heritable and social temperament is stable across the lifespan;
    # circumstance moves a person AROUND their setpoint, it does not
    # define it.
    mental_setpoint: np.ndarray = None
    relationship_setpoint: np.ndarray = None
    # what just happened to this person, as a code and a day. Kept as
    # arrays rather than per-agent lists so 8.3B stays affordable.
    policy_net: np.ndarray = None    # welfare generosity, set by government
    durables: np.ndarray = None      # stock of household goods, 0..1
    durable_spend: np.ndarray = None # today's discretionary purchase
    owns_home: np.ndarray = None     # no rent, but no flexibility either
    rent: np.ndarray = None          # daily housing cost
    arrears: np.ndarray = None       # days of unpaid housing
    evicted: np.ndarray = None
    last_event: np.ndarray = None    # int code, see EVENT_CODES
    last_event_day: np.ndarray = None
    n_events: np.ndarray = None      # lifetime count of marks left
    # API-COMPLETE-1: romantic partnership as a first-class edge. Slot
    # index of the partner, -1 when single. Paired at genesis inside a
    # household (adults of compatible age), dissolved by death (the
    # survivor is widowed), newborns enter single. No dynamics read it.
    partner: np.ndarray = None

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
    from earth1.genesis import GENESIS_COUNTRIES
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
    lognormal = np.exp(rng.normal(0.0, WAGE_LOG_SD, n))  # within-occupation
    wage = OCC_WAGE[occupation] * lognormal / cost_share * WAGE_LEVEL
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

    # SETPOINTS ARE PARAMETERS, SET FROM DATA. The resting LEVEL of
    # mental illness and isolation is an input to this model, calibrated
    # so an untouched population sits at GBD's ~13% and the loneliness
    # surveys' ~12%. That is parameterisation, not fitting.
    #
    # What is NOT set here, and therefore stays out of sample, is every
    # GRADIENT: how these vary with deprivation, with age, with country
    # income tier, and with what has happened to a person. Those fall
    # out of the dynamics and are what scripts/epi_gradient_test.py
    # checks against the published pattern.
    _keys = ["HIC", "UMIC", "LMIC", "LIC"]
    _owns = rng.random(n) < np.array([OWNER_SHARE[k] for k in _keys])[tier]
    # rent is a share of the LOCAL median wage, not of your own — which
    # is exactly why a low earner in an expensive city is crushed
    _med = np.array([np.median(wage[civ.country == c]) if (civ.country == c).any()
                     else 1.0 for c in range(len(GENESIS_COUNTRIES))])
    _rent = np.array([RENT_SHARE[k] for k in _keys])[tier] * _med[civ.country]
    _rent = np.where(_owns, _rent * 0.35, _rent)   # owners still pay upkeep
    _rent = np.where(civ.urban, _rent * 1.35, _rent * 0.8)

    _msp = np.clip(rng.beta(8.0, 2.2, n), 0.0, 1.0)
    _rsp = np.where(rng.random(n) < PARTNERED_SHARE,
                    rng.uniform(0.60, 1.00, n), rng.uniform(0.15, 0.75, n))

    return Life(occupation=occupation, firm=firm, employed=employed,
                in_lf=in_lf, wage=wage, wealth=wealth, cost=cost, tenure=tenure,
                deprivation=np.zeros(n), spells=np.zeros(n, dtype=np.int32),
                firm_health=firm_health, firm_country=firm_country,
                force_baseline=civ.forces.copy(),
                trait_baseline=np.stack([civ.openness, civ.doubt,
                                         civ.desire_intensity], axis=1),
                durables=np.clip(rng.beta(3.0, 2.2, n)
                                 * (0.4 + 0.6 * np.clip(
                                     wage / max(float(np.median(wage)), 1e-9),
                                     0, 2)), 0, 1),
                durable_spend=np.zeros(n),
                owns_home=_owns, rent=_rent, arrears=np.zeros(n),
                evicted=np.zeros(n, dtype=bool),
                mental_setpoint=_msp, relationship_setpoint=_rsp,
                mental=np.clip(_msp + rng.normal(0, 0.05, n), 0.0, 1.0),
                physical=np.clip(rng.beta(7.0, 2.0, n)
                                 * (1.0 - 0.35 * civ.age), 0.0, 1.0),
                addiction=np.where(rng.random(n) < SUBSTANCE_DEP_PREV,
                                   rng.uniform(0.3, 0.9, n), 0.0),
                relationship=np.clip(_rsp + rng.normal(0, 0.05, n), 0, 1),
                social_need=np.clip(rng.beta(2.0, 5.0, n), 0.0, 1.0),
                political=np.clip(rng.beta(2.0, 3.0, n), 0.0, 1.0),
                last_event=np.zeros(n, dtype=np.int8),
                last_event_day=np.full(n, -1.0),
                n_events=np.zeros(n, dtype=np.int32),
                partner=np.full(n, -1, dtype=np.int64))


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

    # ── 2b. distress layoffs (flag-gated; see DISTRESS_LAYOFFS above) ─
    # Fires on the DROP of firm health below its own 30-day trail, past
    # a deadband above the noise floor. RNG is drawn only when the flag
    # is on, so flag-off runs stay bit-identical to canonical physics.
    dcut = np.zeros(n, dtype=bool)
    if DISTRESS_LAYOFFS == "on":
        ema = getattr(life, "firm_health_ema", None)
        if ema is None:
            ema = life.firm_health.copy()
        gap_f = np.clip(ema - life.firm_health - LAYOFF_DEADBAND, 0.0, 1.0)
        life.firm_health_ema = ema + (life.firm_health - ema) \
            * (dt_days / LAYOFF_EMA_TAU)
        if float(gap_f.max()) > 0.0:
            u_cut = rng.random(n)
            agent_gap = np.where(life.firm >= 0,
                                 gap_f[np.maximum(life.firm, 0)], 0.0)
            dcut = ((u_cut < LAYOFF_GAIN * dt_days * agent_gap)
                    & life.employed & ~laid_off & ~sep)

    lost = laid_off | sep | dcut
    life.employed[lost] = False
    life.firm[lost] = -1
    life.tenure[lost] = 0.0
    life.spells[lost] += 1
    lost_idx = np.flatnonzero(lost)          # for fabric re-homing (0.0d)

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
    found_idx = np.flatnonzero(found)        # for fabric re-homing (0.0d)
    if found.any():
        life.employed[found] = True
        idx = found_idx
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
    informal = np.clip(informal * INFORMAL_SCALE, 0.0, 0.95)
    # An agent out of formal work falls back on whichever is better: the
    # welfare state, or the informal economy. Modelling only the former
    # made the poorest countries destitute by construction.
    # If a government exists and has decided on a welfare policy, THAT
    # is the safety net. The constant in this file is only the default
    # for a world with no institutions — see earth1/institutions.py.
    policy = getattr(life, "policy_net", None)
    if policy is not None:
        net = np.asarray(policy)
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
    # Rent is CARVED OUT of the cost of living, not added to it. The
    # first version stacked housing on top of a `cost` that already
    # represented the whole budget, double-counting it and putting half
    # the world into arrears. Housing is the largest SHARE of the
    # budget, not an extra bill beside it.
    housing = life.rent if life.rent is not None else 0.0
    if life.rent is not None:
        paid = income >= life.cost
        # renters fall behind; owners cannot be evicted for arrears
        behind = (~paid) & (~life.owns_home)
        life.arrears = np.where(behind, life.arrears + dt_days,
                                np.maximum(life.arrears - 2.0 * dt_days, 0.0))
        newly_evicted = (life.arrears > ARREARS_TO_EVICTION) & ~life.evicted
        life.evicted |= newly_evicted
        # losing the home ends the rent and ends the arrears
        life.arrears[newly_evicted] = 0.0
    surplus = np.maximum(income - life.cost, 0.0)
    shortfall = np.minimum(income - life.cost, 0.0)
    # ── DURABLES: the first thing to go, and it goes BEFORE income does ──
    # This is why furniture and appliance orders lead a recession. A
    # household that is frightened stops buying the deferrable thing
    # while its paycheque is still arriving, so the signal shows up in
    # the data before the job losses do.
    if life.durables is not None:
        from earth1.types import Force
        frightened = np.clip(civ.forces[:, Force.FEAR], 0, 1)
        can_afford = np.clip(surplus / np.maximum(life.cost, 1e-9), 0, 1)
        # confidence, not income, gates the purchase
        life.durable_spend = (DURABLE_SHARE * can_afford
                              * np.clip(1.0 - 1.6 * (frightened - 0.5), 0, 1)
                              * (1.0 - np.clip(life.deprivation, 0, 1)))
        life.durables = np.clip(
            life.durables
            + (life.durable_spend * 0.02
               - DURABLE_DECAY_YR / 365.0) * dt_days, 0.0, 1.0)
        surplus = np.maximum(surplus - life.durable_spend * life.cost, 0.0)

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
    if HARDSHIP_MODE == "gradient":
        # HARDSHIP GRADIENT (2026-08-27). The cliff form below made
        # deprivation binary: 30.5% of the world sat at ~1.0 and 0.5%
        # anywhere between 0.5 and 0.99, because `covers` is a hard
        # step (99% of cost scored identically to zero income) and a
        # 3-day buffer empties at once. Reality is graded — ~9% in
        # extreme poverty, ~44% below $6.85/day — and every downstream
        # hardship channel (mortality gain, cascade entry) was reading
        # that missing middle as universal catastrophe.
        # Depth of shortfall, cushioned by reserves:
        gap = np.clip((life.cost - income) / np.maximum(life.cost, 1e-9),
                      0.0, 1.0)
        cushion = np.clip(life.wealth / DESTITUTE_BUFFER, 0.0, 1.0)
        life.deprivation = np.where(covers, 0.0, gap * (1.0 - cushion))
    else:
        life.deprivation = np.where(
            covers, 0.0,
            np.clip(1.0 - life.wealth / DESTITUTE_BUFFER, 0.0, 1.0))

    # ── 6. firm health drifts, and recovers slowly ────────────────────
    life.firm_health = np.clip(
        life.firm_health + z_health
        + 0.004 * (0.8 - life.firm_health), 0.0, 1.0)
    if failed.size:
        life.firm_health[failed] = u_reseed[failed]

    # ── THE BODY AND THE SELF ─────────────────────────────────────────
    # Everything below is stochastic, discrete and irreversible-ish, and
    # every rate is modulated by a state the model already computes. That
    # is what makes the DISTRIBUTION emergent even though the population
    # LEVEL is anchored to real epidemiology.
    if life.mental is not None:
        u_crime = rng.random(n)
        u_ber = rng.random(n)
        u_child = rng.random(n)
        u_addict = rng.random(n)
        u_recover = rng.random(n)
        u_split = rng.random(n)

        pressure = (np.clip(life.deprivation, 0, 1) * 0.4
                    + life.social_need * 0.3 + life.addiction * 0.3)

        # crime: victimisation rises with deprivation, and it is LOCAL —
        # it lands on a person, not on a country
        crime_p = (CRIME_VICTIM_YR / 365.0) * dt_days * \
            (1.0 + 2.0 * life.deprivation)
        victim = u_crime < crime_p

        # bereavement: the older you are, the more of your people die
        ber_p = (0.012 / 365.0) * dt_days * (1.0 + 6.0 * civ.age ** 2)
        bereaved = u_ber < ber_p

        # a child arrives: partnered, of age, and not destitute
        fertile = ((civ.age > 0.05) & (civ.age < 0.45)
                   & (life.relationship > 0.6) & (life.deprivation < 0.5))
        new_child = fertile & (u_child < (0.055 / 365.0) * dt_days)

        # addiction: onset hazard rises as mental health falls
        onset = ((u_addict < (0.004 / 365.0) * dt_days
                  * (1.0 + 8.0 * (1.0 - life.mental)))
                 & (life.addiction < 0.3))
        recover = (u_recover < (0.09 / 365.0) * dt_days * life.mental) \
            & (life.addiction > 0)

        # relationships end under sustained pressure
        split = ((u_split < (0.02 / 365.0) * dt_days * (1.0 + 4.0 * pressure))
                 & (life.relationship > 0.5))

        # apply
        life.addiction = np.clip(life.addiction + 0.25 * onset
                                 - 0.35 * recover, 0.0, 1.0)
        life.relationship = np.clip(
            life.relationship
            + (life.relationship_setpoint - 0.18 * pressure
               - life.relationship) * 0.02 * dt_days
            - 0.55 * split + 0.05 * new_child, 0.0, 1.0)
        life.social_need = np.clip(
            life.social_need + (0.25 - life.relationship) * 0.02 * dt_days
            + 0.20 * bereaved, 0.0, 1.0)
        life.mental = np.clip(
            life.mental
            + (life.mental_setpoint - pressure * 0.5 - life.mental)
            * 0.02 * dt_days
            - 0.12 * victim - 0.16 * bereaved - 0.10 * split
            - 0.06 * lost, 0.0, 1.0)
        life.physical = np.clip(
            life.physical - 0.0004 * dt_days - 0.05 * victim
            - 0.02 * life.addiction * dt_days
            + 0.02 * life.mental * dt_days, 0.0, 1.0)

        # leave the mark: what happened to this person, and when
        for code, m in ((2, found), (1, lost), (8, split), (7, recover),
                        (6, onset), (5, new_child), (4, bereaved),
                        (3, victim)):
            if m.any():
                life.last_event[m] = code
                life.n_events[m] += 1

    stats = {"lost_idx": lost_idx, "found_idx": found_idx,
             "laid_off": int(laid_off.sum()), "separated": int(sep.sum()),
             "found_work": int(found.sum()), "firms_failed": int(failed.size),
             "unemployment": float((~life.employed & life.in_lf).sum()
                                   / max(life.in_lf.sum(), 1)),
             "destitute": float((life.deprivation > 0.99).mean()),
             "deprived": float((life.deprivation > 0.5).mean()),
             "median_buffer_days": float(np.median(life.wealth))}
    if life.rent is not None:
        stats.update({"in_arrears": float((life.arrears > 14).mean()),
                      "evicted_total": int(life.evicted.sum()),
                      "rent_burden": float(np.median(
                          life.rent / np.maximum(life.wage, 1e-6)))})
    if life.mental is not None:
        stats.update({
            "mental_ill": float((life.mental < 0.45).mean()),
            "addicted": float((life.addiction > 0.3).mean()),
            "isolated": float((life.relationship < 0.25).mean()),
            "crime_victims": int(victim.sum()),
            "bereaved": int(bereaved.sum()),
            "new_children": int(new_child.sum()),
            "addiction_onsets": int(onset.sum())})

    if couple_forces:
        stats.update(couple_life_to_forces(civ, life))
    return stats


def life_force_target(civ: Civilization, life: Life,
                      flourishing=None, adj=None) -> np.ndarray:
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
    # POSTHUMOUS rule: current shared hardship is computed over LIVING
    # alters when the caller passes the living view (alive.py does).
    adj = civ.adj if adj is None else adj
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
        base[:, Force.COLLECTIVE]
        + 0.40 * (dep * shared - GEO1_REF_DS), 0.0, 1.0)

    # THE BODY BECOMES OPINION.
    #   mental health modulates how much fear a person carries at all
    #   addiction LOCKS the desire channel — an addicted agent stops
    #     responding to collective pressure, which is the clinical
    #     picture and also a real dynamical consequence
    #   isolation turns a person toward identity and away from others
    if life.mental is not None:
        t[:, Force.FEAR] = np.clip(
            t[:, Force.FEAR] + 0.30 * (1.0 - life.mental), 0.0, 1.0)
        t[:, Force.DESIRE] = np.clip(
            t[:, Force.DESIRE] + 0.45 * life.addiction, 0.0, 1.0)
        t[:, Force.COLLECTIVE] = np.clip(
            t[:, Force.COLLECTIVE] * (1.0 - 0.6 * life.addiction)
            + 0.25 * (life.political - GEO1_REF_POL)
            - 0.20 * (life.social_need - GEO1_REF_SN), 0.0, 1.0)
        t[:, Force.IDENTITY] = np.clip(
            t[:, Force.IDENTITY] + 0.25 * life.social_need
            - 0.15 * life.relationship, 0.0, 1.0)
        t[:, Force.EXPERIENCE] = np.clip(
            t[:, Force.EXPERIENCE] + 0.10 * np.clip(life.n_events / 8.0,
                                                    0, 1), 0.0, 1.0)
    # FLOURISHING LEVEL MAP (canonical; candidate 76a574c, ported
    # verbatim from field_lab.flourishing_level_map): hope, need,
    # curiosity, belonging and meaning are bounded LEVEL contributions
    # to the lived target, never daily increments. Belonging enters as
    # a departure from its reference center (COLLECTIVE-GEO-1).
    fl = flourishing
    if fl is not None and fl.hope is not None:
        need = np.clip(0.6 * fl.hunger + 0.4 * fl.thirst, 0, 1)
        t[:, Force.FEAR] = np.clip(
            t[:, Force.FEAR] + 0.30 * need - 0.20 * fl.hope, 0, 1)
        t[:, Force.DESIRE] = np.clip(
            t[:, Force.DESIRE] + 0.20 * fl.hope
            + 0.15 * fl.curiosity - 0.25 * need, 0, 1)
        t[:, Force.COLLECTIVE] = np.clip(
            t[:, Force.COLLECTIVE]
            + 0.20 * (fl.belonging - GEO1_REF_BEL), 0, 1)
        t[:, Force.CULTURE] = np.clip(
            t[:, Force.CULTURE] + 0.20 * fl.meaning, 0, 1)
        t[:, Force.EXPERIENCE] = np.clip(
            t[:, Force.EXPERIENCE] + 0.10 * fl.curiosity, 0, 1)
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
