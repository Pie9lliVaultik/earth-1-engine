"""KNOWLEDGE — what they learn, what they make, and who they become.

Four things that are one thing, because they feed each other.

LEARNING. Knowledge is not handed out at birth and frozen. An agent
learns from schooling, from what they can reach (a phone, a library, a
signal), and above all from PEOPLE WHO KNOW MORE THAN THEY DO. That
last channel is what makes knowledge a network property: put a curious
person next to an expert and both change.

STATUS. Not money. Status is what a society gives you for what you have
and what you are: income, the standing of your occupation, what you
know, and how many people listen to you. It is unequally distributed by
construction and it compounds, because status buys access which buys
more status.

DISCOVERY. The most knowledgeable agents are scientists whether or not
anyone calls them that. They generate discoveries at a rate that rises
with what they know and with how connected they are to others who know
things — collaboration is the single largest multiplier in the real
production function of science. A discovery raises the GLOBAL knowledge
stock permanently, which raises the ceiling for everyone born after it.
That is the ratchet no individual can turn alone.

CREATION. They make things: music, images, stories, arguments, games.
A cultural work is ORDER PULLED OUT OF NOISE — the maker takes a
high-entropy internal state and emits a low-entropy artefact that other
people can hold. It is measured that way here, literally, as entropy
reduction, and works spread along the same social fabric as everything
else. Beauty is not decoration in this model. It is negentropy, made by
somebody, travelling through a network.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# fraction of a country's people who can actually reach the world's
# information: phone, connection, electricity, literacy
CONNECTIVITY = {"HIC": 0.94, "UMIC": 0.78, "LMIC": 0.52, "LIC": 0.28}
TIERS = ["HIC", "UMIC", "LMIC", "LIC"]

# "Scientist" is a RANK, not a score. An absolute cutoff made 61% of
# the population scientists as soon as average knowledge drifted up —
# the label has to mean "at the frontier of what this civilisation
# knows", which is inherently relative to everyone else.
SCIENTIST_PERCENTILE = 99.5
DISCOVERY_RATE_YR = 0.06
CREATION_RATE_YR = 0.35        # people make things far more often than
                               # they discover things
WORK_DECAY_HALF_LIFE = 900.0   # days before a work is half forgotten


@dataclass
class Knowledge:
    stock: np.ndarray          # 0..1 what this person knows
    status: np.ndarray         # 0..1 what society grants them
    connected: np.ndarray      # bool, can reach the information world
    works_made: np.ndarray     # lifetime cultural works produced
    discoveries: np.ndarray    # lifetime discoveries
    global_stock: float = 0.0  # the commons: what humanity knows
    living_works: float = 0.0  # cultural works still remembered


def _tier(civ) -> np.ndarray:
    from earth1.genesis import GENESIS_COUNTRIES
    per = np.array([TIERS.index(c.get("income", "LMIC"))
                    if c.get("income") in TIERS else 2
                    for c in GENESIS_COUNTRIES])
    return per[civ.country]


def birth_knowledge(civ, life, seed: int = 0) -> Knowledge:
    rng = np.random.default_rng(seed ^ 0xC0DE)
    n = civ.n
    tier = _tier(civ)
    conn_p = np.array([CONNECTIVITY[t] for t in TIERS])[tier]
    # education sets the floor, curiosity and country set the spread
    stock = np.clip(0.18 + 0.22 * civ.education
                    + 0.20 * civ.openness
                    + 0.15 * (1.0 - tier / 3.0)
                    + rng.normal(0, 0.09, n), 0.0, 1.0)
    return Knowledge(
        stock=stock,
        status=np.zeros(n),
        connected=rng.random(n) < conn_p,
        works_made=np.zeros(n, dtype=np.int32),
        discoveries=np.zeros(n, dtype=np.int32),
        global_stock=float(stock.mean()))


def knowledge_tick(civ, life, kn: Knowledge, rng, dt_days: float = 1.0,
                   alive: np.ndarray | None = None) -> dict:
    """One day of learning, earning standing, discovering and making."""
    n = civ.n
    dt_yr = dt_days / 365.0
    live = alive if alive is not None else np.ones(n, dtype=bool)
    deg = np.maximum(np.asarray(civ.adj.sum(axis=1)).ravel(), 1.0)

    # ── learning from the people you know ────────────────────────────
    # you move toward what your neighbours know, but only UPWARD and
    # only as fast as your own openness allows. Nobody unlearns by
    # meeting someone ignorant.
    nb = np.asarray(civ.adj @ kn.stock).ravel() / deg
    gap = np.maximum(nb - kn.stock, 0.0)
    # access to the commons matters only if you are connected to it
    reach = np.where(kn.connected, 1.0, 0.25)
    # Learning is SLOW. The first version moved 2% of the gap per day,
    # which saturated the whole population inside a year and made
    # everyone an expert. A person absorbs what those around them know
    # over decades, not months.
    learn = (0.0015 * civ.openness * gap
             + 0.0004 * reach * np.maximum(kn.global_stock - kn.stock, 0.0)) \
        * dt_days
    # hardship crowds out learning: you cannot study while you starve
    learn *= (1.0 - 0.7 * np.clip(life.deprivation, 0, 1))
    kn.stock = np.clip(kn.stock + learn * live, 0.0, 1.0)

    # ── status: money, standing, knowing, being listened to ──────────
    from earth1.life import OCC_WAGE
    occ_standing = OCC_WAGE[life.occupation] / OCC_WAGE.max()
    listened_to = np.clip(deg / max(float(np.percentile(deg, 99)), 1.0),
                          0.0, 1.0)
    wealth_rank = np.clip(life.wealth / 365.0, 0.0, 1.0)
    kn.status = np.clip(0.30 * wealth_rank + 0.25 * occ_standing
                        + 0.25 * kn.stock + 0.20 * listened_to, 0.0, 1.0)

    # ── discovery: the ratchet ───────────────────────────────────────
    cutoff = float(np.percentile(kn.stock[live], SCIENTIST_PERCENTILE)) \
        if live.any() else 1.0
    scientists = live & (kn.stock >= cutoff)
    peers = np.asarray(civ.adj @ scientists.astype(np.float64)).ravel()
    rate = DISCOVERY_RATE_YR * (1.0 + 0.5 * peers) * dt_yr
    made_discovery = scientists & (rng.random(n) < rate)
    kn.discoveries += made_discovery
    if made_discovery.any():
        # the commons rises, permanently, for everyone including the
        # unborn. No individual can do this alone and nobody can undo it.
        # the commons moves slowly. Every discovery ever made has taken
        # humanity from stone tools to here; no single one of them moves
        # the whole stock by a measurable fraction.
        kn.global_stock = float(min(
            1.0, kn.global_stock + 2.5e-6 * made_discovery.sum()))

    # ── creation: order pulled out of noise ──────────────────────────
    # a work is made when someone has something to say and the room to
    # say it. Deprivation suppresses it; connection and knowledge feed it.
    drive = (0.4 * civ.openness + 0.3 * kn.stock
             + 0.3 * (1.0 - np.clip(life.deprivation, 0, 1)))
    made_work = live & (rng.random(n) < CREATION_RATE_YR * drive * dt_yr)
    kn.works_made += made_work

    # works accumulate and are forgotten at a half-life
    decay = 0.5 ** (dt_days / WORK_DECAY_HALF_LIFE)
    kn.living_works = kn.living_works * decay + float(made_work.sum())

    # NEGENTROPY: a work is measurable order. The maker's internal state
    # is high-entropy; the artefact is not. Report the reduction.
    negentropy = 0.0
    if made_work.any():
        before = float(np.std(civ.forces[made_work]))
        negentropy = float(max(0.0, before - float(
            np.std(civ.forces[made_work].mean(axis=0)))))

    return {"mean_knowledge": float(kn.stock[live].mean()),
            "global_knowledge": round(kn.global_stock, 5),
            "scientists": int(scientists.sum()),
            "discoveries_today": int(made_discovery.sum()),
            "works_today": int(made_work.sum()),
            "living_works": round(kn.living_works, 1),
            "negentropy": round(negentropy, 5),
            "status_gini": round(_gini(kn.status[live]), 4),
            "connected_share": float(kn.connected[live].mean())}


def _gini(x: np.ndarray) -> float:
    if x.size == 0:
        return 0.0
    s = np.sort(x)
    i = np.arange(1, s.size + 1)
    d = s.sum()
    return float((2 * (i * s).sum()) / (s.size * d) - (s.size + 1) / s.size) \
        if d > 0 else 0.0
