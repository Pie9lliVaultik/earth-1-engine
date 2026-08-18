"""FABRIC — the society an earthling actually lives in.

The graph was a random draw with homophily: everyone had roughly the
same kind of neighbour, everywhere on Earth. A shock therefore
propagated the same way in Lagos and in Stockholm, which is the one
thing we know is false.

Here the graph is a CONSEQUENCE of the material layer. You know the
people you live with, the people you work for, the people on your
street, the people like you, and a handful of people who connect you to
a world you would otherwise never touch.

    HOUSEHOLD    partners, children, elders. The strongest tie there
                 is: income is pooled, so a job loss lands on everyone
                 in the house on the same day. Size varies by country
                 fertility, which is why this channel dominates in
                 high-fertility countries and barely exists in
                 low-fertility ones.
    COLLEAGUES   read off life.firm, which already exists. When a firm
                 fails, these people lose their income together AND
                 they are connected to each other — correlated shock
                 and correlated network in the same structure.
    NEIGHBOURS   locality. Carries crime, heat, local events.
    FRIENDS      homophily on trait and life stage.
    WEAK TIES    Granovetter's bridges: sparse, random, long-range.
                 Novel information travels through weak ties, not
                 strong ones, so these are what let a cascade jump
                 between clusters instead of dying inside one.

EVERY TIE TYPE IS KEPT SEPARATELY as well as combined. That is the
point: it makes the CHANNEL a shock travelled through an observable,
not an assumption. "It reached everyone" becomes "it reached them
through households here and through weak ties there", which is the
geography of the chaos rather than just its existence.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import sparse

# tie type -> (influence weight, ties per agent)
TIE_SPEC = {
    "household": (1.00, None),   # size set by country fertility
    "colleagues": (0.60, 6),
    "neighbours": (0.40, 5),
    "friends": (0.70, 5),
    "weak": (0.15, 2),
    # ── the planet ───────────────────────────────────────────────────
    # Without these, Earth-1 is 194 disconnected villages: the phi-proxy
    # measured 0.0028 because severing the world changed nothing, and
    # nothing can be severed that was never joined. These are what make
    # it one world.
    "diaspora": (0.55, 1),   # migration corridors: you keep your people
    "media": (0.30, 3),      # global hubs — celebrities, scientists
}

# Share of the population who are global hub nodes: the people whose
# reach is not bounded by geography. Broadcasters, athletes, musicians,
# scientists, heads of state. Vanishingly few, enormously connected.
HUB_SHARE = 0.0002


@dataclass
class Fabric:
    adj: object                                  # combined weighted CSR
    by_type: dict = field(default_factory=dict)  # name -> CSR
    household: np.ndarray = None                 # household id per agent

    def degree(self, kind: str | None = None) -> np.ndarray:
        a = self.adj if kind is None else self.by_type[kind]
        return np.asarray(a.sum(axis=1)).ravel()


def _mean_household_size(civ) -> np.ndarray:
    """Household size per agent's country, from real fertility.

    Total fertility is the strongest single predictor of household size
    in cross-national data. A country at TFR 1.5 lands near 2.6 people
    per household; one at TFR 5 lands near 5.7. This is what makes a
    job loss in Lagos hit five people and the same loss in Stockholm
    hit two.
    """
    from earth1.genesis import GENESIS_COUNTRIES
    tfr = np.array([float(c.get("tfr", 2.0) or 2.0)
                    for c in GENESIS_COUNTRIES])
    return (1.2 + 0.9 * tfr)[civ.country]


def _pairs_within(groups: np.ndarray, k: int, rng, n: int):
    """k random ties per agent, drawn inside the agent's own group.

    Vectorized: agents are sorted by group and partners are chosen by
    offsetting within the group's contiguous block, which avoids any
    per-group Python loop and stays fast at population scale.
    """
    order = np.argsort(groups, kind="stable")
    g_sorted = groups[order]
    # start index and size of each group's block
    starts = np.searchsorted(g_sorted, g_sorted, side="left")
    ends = np.searchsorted(g_sorted, g_sorted, side="right")
    sizes = ends - starts
    ok = sizes > 1
    rows, cols = [], []
    for _ in range(k):
        off = rng.integers(1, np.maximum(sizes, 2))
        pos = starts + (np.arange(len(g_sorted)) - starts + off) % \
            np.maximum(sizes, 1)
        rows.append(order[ok])
        cols.append(order[pos[ok]])
    if not rows:
        return np.empty(0, int), np.empty(0, int)
    return np.concatenate(rows), np.concatenate(cols)


def build_fabric(civ, life, seed: int = 0) -> Fabric:
    """Assemble the social fabric from who these people actually are."""
    rng = np.random.default_rng(seed ^ 0xFAB)
    n = civ.n
    mats = {}

    # ── households ───────────────────────────────────────────────────
    # agents are grouped into houses inside their own country, with the
    # size drawn from that country's fertility
    hh_size = _mean_household_size(civ)
    ids = np.zeros(n, dtype=np.int64)
    cur = 0
    # Cut each country's population into houses using THAT country's
    # size distribution. Done per country because a house never spans a
    # border, and because the whole point of this channel is that the
    # number varies: at TFR 5 a job loss lands on five or six people, at
    # TFR 1.5 it lands on two.
    for ci in np.unique(civ.country):
        who = np.flatnonzero(civ.country == ci)
        if who.size == 0:
            continue
        rng.shuffle(who)
        mean = float(hh_size[who[0]])
        # draw generously, then keep exactly as many houses as fit
        sizes = np.maximum(1, rng.poisson(mean, int(who.size / max(mean, 1)) + 8))
        cuts = np.cumsum(sizes)
        cuts = cuts[cuts < who.size]
        for block in np.split(who, cuts):
            if block.size:
                ids[block] = cur
                cur += 1
    hh_id = ids
    r, c = _pairs_within(hh_id, 3, rng, n)
    mats["household"] = (r, c)

    # ── colleagues: straight off the firm assignment ─────────────────
    firm = np.where(life.employed, life.firm, -1 - np.arange(n))
    r, c = _pairs_within(firm, TIE_SPEC["colleagues"][1], rng, n)
    mats["colleagues"] = (r, c)

    # ── neighbours: locality = country x region x urban ──────────────
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2 + civ.urban.astype(np.int64))
    r, c = _pairs_within(loc, TIE_SPEC["neighbours"][1], rng, n)
    mats["neighbours"] = (r, c)

    # ── friends: people like you, at your life stage ─────────────────
    like = (civ.country.astype(np.int64) * 100
            + civ.education.astype(np.int64) * 10
            + civ.age_bucket.astype(np.int64))
    r, c = _pairs_within(like, TIE_SPEC["friends"][1], rng, n)
    mats["friends"] = (r, c)

    # ── weak ties: the bridges, mostly national, a few global ────────
    k = TIE_SPEC["weak"][1]
    rr = np.tile(np.arange(n), k)
    cc = rng.integers(0, n, n * k)
    same = civ.country[rr] == civ.country[cc]
    # keep national bridges, plus 2% genuinely international ones
    intl = rng.random(rr.size) < 0.02
    keep = same | intl
    mats["weak"] = (rr[keep], cc[keep])

    # ── diaspora: you moved, and you kept your people ────────────────
    # Corridors follow cultural and regional proximity, which is how
    # real migration runs. A shock in the destination country reaches
    # the origin country through the people who left.
    k = TIE_SPEC["diaspora"][1]
    rr = np.tile(np.arange(n), k)
    # partner drawn from a country in the same broad region where
    # possible, so corridors are structured rather than uniform noise
    cc = rng.integers(0, n, n * k)
    cross = civ.country[rr] != civ.country[cc]
    same_region = civ.region[rr] == civ.region[cc]
    # migrants are a minority: only a slice of the population has ties
    # abroad at all
    is_migrant = rng.random(n) < 0.14
    keep = cross & same_region & is_migrant[rr]
    mats["diaspora"] = (rr[keep], cc[keep])

    # ── media: the few who reach everyone ────────────────────────────
    n_hub = max(1, int(n * HUB_SHARE))
    hubs = rng.choice(n, n_hub, replace=False)
    k = TIE_SPEC["media"][1]
    audience = rng.integers(0, n, n_hub * k * 40)
    speakers = np.repeat(hubs, k * 40)
    mats["media"] = (speakers, audience)

    by_type, total = {}, None
    for name, (r, c) in mats.items():
        w = TIE_SPEC[name][0]
        m = sparse.csr_matrix(
            (np.full(r.size, w, dtype=np.float64), (r, c)), shape=(n, n))
        m = m.maximum(m.T)                       # ties are mutual
        m.setdiag(0.0)
        m.eliminate_zeros()
        by_type[name] = m
        total = m if total is None else total + m

    return Fabric(adj=total.tocsr(), by_type=by_type, household=hh_id)
