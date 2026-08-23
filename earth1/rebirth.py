"""REBIRTH — the central reset schema. Phase 0.0b.

When a dead slot is reused for a newborn it must become a genuinely new
Earthling, not a partially reset corpse. Before this module, `_be_born`
reset ~25 fields by hand and silently inherited ~40 more from the
previous occupant — including `health.declining` (a newborn could be
born mid fall-decline, carrying x3.5 fall hazard), the dead person's
wage, home, hunger, criminal record, memories, and their entire social
graph.

THE CONTRACT. Every per-agent field carries exactly one policy:

  RESET           previous occupant's state cleared to a defined zero
  INITIALIZE      drawn from the canonical birth distribution (the
                  formulas are verbatim from the pre-0.0b `_be_born`
                  and the `birth_*` constructors — 0.0b changes WHO is
                  reset, never the birth physics itself)
  INHERIT_PARENT  intentionally inherited from the PARENT (never from
                  the corpse) by model design
  REBUILD         relational state recreated through its subsystem

Two completeness gates enforce it (tests/test_rebirth.py): every
runtime-discovered per-agent field must appear in POLICY, and every
POLICY entry must be implemented in `apply_rebirth`. Adding a per-agent
field without a rebirth policy fails CI — the same pattern that ended
the hand-maintained persistence lists (d3d2a0c class).

Known, deliberately preserved defect: the trait/forces/knowledge
INITIALIZE formulas blend toward the PLANETARY living mean (audit
D4-f, Class-GM occurrence #7 — a child in Niger inherits half a global
average). Changing that blend is birth physics, not reset correctness,
and is left for its own adjudicated fix.

Core invariant:  newborn = birth initialization + declared inheritance,
never previous-occupant leftovers.
"""
from __future__ import annotations

import numpy as np

RESET = "RESET"
INITIALIZE = "INITIALIZE"
INHERIT_PARENT = "INHERIT_PARENT"
REBUILD = "REBUILD"

HERITABILITY = 0.45         # matches _be_born signature default

# ── the schema ──────────────────────────────────────────────────────
POLICY = {
    # Civilization — demographics & identity
    ("civ", "country"): INHERIT_PARENT,
    ("civ", "region"): INHERIT_PARENT,
    ("civ", "urban"): INHERIT_PARENT,
    ("civ", "education"): INHERIT_PARENT,
    ("civ", "income"): INHERIT_PARENT,          # was corpse leftover
    ("civ", "age"): INITIALIZE,                  # 0.0 = adult entry at 18
    ("civ", "age_bucket"): INITIALIZE,
    # Civilization — traits (parent-blend formula, verbatim)
    ("civ", "openness"): INITIALIZE,
    ("civ", "empathy"): INITIALIZE,
    ("civ", "risk_appetite"): INITIALIZE,
    ("civ", "doubt"): INITIALIZE,
    ("civ", "desire_intensity"): INITIALIZE,
    ("civ", "conscientiousness"): INITIALIZE,
    ("civ", "agreeableness"): INITIALIZE,
    ("civ", "extraversion"): INITIALIZE,
    ("civ", "neuroticism"): INITIALIZE,
    # Civilization — culture-anchored personal fields: the newborn is of
    # the parent's culture and place, never the corpse's residue
    ("civ", "economic_field"): INHERIT_PARENT,   # was corpse leftover
    ("civ", "person_id"): INITIALIZE,            # next counter value
    ("civ", "parent_id"): INHERIT_PARENT,        # parent's person_id
    ("life", "partner"): INITIALIZE,             # -1: born single
    ("civ", "culture_offset"): INHERIT_PARENT,   # was corpse leftover
    ("civ", "power_distance"): INHERIT_PARENT,   # was corpse leftover
    ("civ", "individualism"): INHERIT_PARENT,    # was corpse leftover
    ("civ", "uncertainty_avoidance"): INHERIT_PARENT,  # was corpse
    ("civ", "long_term_orientation"): INHERIT_PARENT,  # was corpse
    ("civ", "forces"): INITIALIZE,               # parent/mean blend
    ("civ", "alpha"): INITIALIZE,                # 0.35, the young unsure
    # Civilization — flag-gated optionals (None in production)
    ("civ", "religiosity"): INHERIT_PARENT,
    ("civ", "marital"): RESET,
    ("civ", "employed"): RESET,
    ("civ", "ideology"): INHERIT_PARENT,
    ("civ", "social_class"): INHERIT_PARENT,

    # Life — labour
    ("life", "occupation"): INITIALIZE,          # education-affinity draw
    ("life", "firm"): RESET,                     # -1
    ("life", "employed"): RESET,
    ("life", "in_lf"): INITIALIZE,               # True at adult entry
    ("life", "wage"): INHERIT_PARENT,            # was corpse; hire never
                                                 # re-prices, so household
                                                 # wage is the entry level
    ("life", "tenure"): RESET,
    ("life", "spells"): RESET,
    ("life", "deprivation"): RESET,
    ("life", "wealth"): RESET,                   # no savings, no scars
    # Life — household economics: born into the parent's household
    ("life", "cost"): INHERIT_PARENT,            # was corpse leftover
    ("life", "policy_net"): INHERIT_PARENT,      # same country; gov
                                                 # rewrites next tick
    ("life", "durables"): INHERIT_PARENT,        # the household's goods
    ("life", "durable_spend"): RESET,
    ("life", "owns_home"): INHERIT_PARENT,       # lives where parent does
    ("life", "rent"): INHERIT_PARENT,
    ("life", "arrears"): RESET,
    ("life", "evicted"): RESET,
    # Life — body & self
    ("life", "mental_setpoint"): INITIALIZE,     # heritable: parent+noise
                                                 # (was CORPSE setpoint)
    ("life", "relationship_setpoint"): INITIALIZE,  # (was corpse)
    ("life", "mental"): INITIALIZE,              # = own new setpoint
    ("life", "physical"): INITIALIZE,            # young body, beta(7,2)
    ("life", "addiction"): RESET,
    ("life", "relationship"): INITIALIZE,        # setpoint + noise
    ("life", "social_need"): INITIALIZE,         # beta(2,5)
    ("life", "political"): INITIALIZE,           # beta(2,3)
    ("life", "force_baseline"): INITIALIZE,      # = own new forces
    ("life", "trait_baseline"): INITIALIZE,      # = own new traits
    ("life", "last_event"): RESET,
    ("life", "last_event_day"): RESET,           # -1; was corpse leftover
    ("life", "n_events"): RESET,

    # Health — a new body
    ("health", "alive"): INITIALIZE,             # True — the birth itself
    ("health", "condition"): RESET,
    ("health", "diagnosed_day"): RESET,          # -1
    ("health", "in_treatment"): RESET,
    ("health", "cause_of_death"): RESET,
    ("health", "lifetime_illnesses"): RESET,
    ("health", "declining"): RESET,              # was corpse: newborn in
                                                 # post-fall decline
    ("health", "falls"): RESET,                  # was corpse leftover

    # Knowledge
    ("knowledge", "stock"): INITIALIZE,          # parent/mean blend
    ("knowledge", "status"): RESET,              # recomputed by its tick
    ("knowledge", "connected"): INITIALIZE,      # country-tier draw
                                                 # (was corpse leftover)
    ("knowledge", "works_made"): RESET,
    ("knowledge", "discoveries"): RESET,

    # Class
    ("klass", "homeless"): RESET,
    ("klass", "criminal"): RESET,
    ("klass", "days_homeless"): RESET,           # was corpse leftover
    ("klass", "crimes_committed"): RESET,
    ("klass", "migrated"): RESET,                # was corpse leftover

    # Flourishing — needs come from the household, drives start fresh
    ("flourishing", "hunger"): INHERIT_PARENT,   # same table (was corpse:
                                                 # born starving if the
                                                 # occupant starved)
    ("flourishing", "thirst"): INHERIT_PARENT,
    ("flourishing", "breath"): INHERIT_PARENT,   # same air
    ("flourishing", "hope"): INITIALIZE,         # beta(4,3)
    ("flourishing", "curiosity"): INITIALIZE,    # 0.3+0.5*openness+noise
    ("flourishing", "meaning"): INITIALIZE,      # beta(3.5,3)
    ("flourishing", "belonging"): INITIALIZE,    # = own relationship
    ("flourishing", "satisfaction"): INITIALIZE, # beta(3,3)
    ("flourishing", "art_received"): RESET,
    ("flourishing", "lifetime_joy"): RESET,

    # Presence — born where the parent is
    ("presence", "locality"): INHERIT_PARENT,    # was corpse's place
    ("presence", "density"): INHERIT_PARENT,
    ("presence", "gathering"): RESET,            # -1

    # Mobility — a fresh traveller in the parent's circumstances
    ("mobility", "owns_car"): RESET,             # no car at entry
    ("mobility", "flies_per_year"): INITIALIZE,  # tier/urban formula
    ("mobility", "commute_minutes"): RESET,      # no job, no commute
    ("mobility", "travelled"): RESET,            # was corpse's lifetime

    # Relational — rebuilt through subsystems, never copied
    ("fabric", "ties"): REBUILD,                 # all 7 types, row+col
    ("fabric", "household"): REBUILD,            # joins parent's household
    ("feed", "edges"): REBUILD,                  # cleared; no feed at
                                                 # entry (rewiring is
                                                 # graph_dynamics, 0.5)
    ("chronicle", "scope"): REBUILD,             # not present at events
                                                 # before their birth
}

# fields excluded from discovery: per-firm arrays, scalars, aliases
_NOT_PER_AGENT = {("life", "firm_health"), ("life", "firm_country")}


def discover_per_agent_fields(w):
    """Every (object, field) whose array is per-agent, found at runtime.

    Discovery, not declaration, is what makes the completeness gate
    real: a new per-agent field shows up here automatically and fails
    CI until POLICY says what rebirth does with it.
    """
    n = w.civ.n
    found = set()
    for obj_name in ("civ", "life", "health", "knowledge", "klass",
                     "flourishing", "presence", "mobility"):
        obj = getattr(w, obj_name if obj_name != "klass" else "klass")
        for f in getattr(obj, "__dataclass_fields__", {}):
            v = getattr(obj, f, None)
            if isinstance(v, np.ndarray) and v.shape[:1] == (n,):
                if (obj_name, f) not in _NOT_PER_AGENT:
                    found.add((obj_name, f))
    return found


def policy_gaps(w):
    declared = set(POLICY)
    actual = discover_per_agent_fields(w)
    structural = {k for k in declared
                  if k[0] in ("fabric", "feed", "chronicle")}
    # a declared field is stale only if its object no longer even has
    # the attribute — a None value is a lazily-created field (the five
    # flag-gated civ optionals; life.policy_net before the first
    # institutions tick), not a schema error
    stale = set()
    for obj_name, f in declared - structural - actual:
        obj = getattr(w, obj_name, None)
        if obj is None or not hasattr(obj, f):
            stale.add((obj_name, f))
    return {"undeclared": sorted(actual - declared),
            "stale": sorted(stale)}


def assert_policy_complete(w):
    gaps = policy_gaps(w)
    if gaps["undeclared"]:
        raise ValueError(
            f"per-agent fields with no rebirth policy: "
            f"{gaps['undeclared']} — declare each in rebirth.POLICY; a "
            f"reborn slot must never carry an undeclared leftover")
    if gaps["stale"]:
        raise ValueError(f"rebirth POLICY names missing fields: "
                         f"{gaps['stale']}")


# ── relational rebuild ──────────────────────────────────────────────

def _zero_rows_cols(mat, slots):
    """Zero row and column entries for `slots` on a CSR matrix in place.

    Ties are mutual (fabric symmetrizes), so a row-only clear would
    leave inbound edges still delivering influence through adj @ x.
    """
    m = mat.tocsr()
    for i in slots:
        m.data[m.indptr[i]:m.indptr[i + 1]] = 0.0
    mask = np.isin(m.indices, slots)
    if mask.any():
        m.data[mask] = 0.0
    m.eliminate_zeros()
    return m


def rebuild_ties(w, slots, parents):
    """Sever every tie of the previous occupant; attach the newborn to
    the parent's household through the fabric's own typed structure.

    Zero inherited friends, colleagues, neighbours, weak ties, diaspora,
    media relationships — and zero reverse references: the columns go
    with the rows. The only ties a newborn starts with are household
    ties to the parent's living household, at the household tie weight.
    """
    from scipy import sparse
    fab = w.fabric
    slots = np.asarray(slots)
    parents = np.asarray(parents)

    for name in list(fab.by_type):
        fab.by_type[name] = _zero_rows_cols(fab.by_type[name], slots)
    adj = _zero_rows_cols(fab.adj, slots)

    # household membership follows the parent
    fab.household[slots] = fab.household[parents]

    rows, cols = [], []
    for s, p in zip(slots, parents):
        members = np.flatnonzero((fab.household == fab.household[p])
                                 & w.health.alive)
        members = members[members != s]
        if members.size == 0:
            members = np.array([p])
        rows.extend([s] * members.size + list(members))
        cols.extend(list(members) + [s] * members.size)
    if rows:
        n = w.civ.n
        w_house = 1.00                        # TIE_SPEC household weight
        delta = sparse.csr_matrix(
            (np.full(len(rows), w_house, dtype=adj.dtype), (rows, cols)),
            shape=(n, n))
        fab.by_type["household"] = (fab.by_type["household"]
                                    + delta).tocsr()
        adj = (adj + delta).tocsr()

    fab.adj = adj
    w.civ.adj = adj          # keep the alive.py:64 alias current

    if w.feed is not None:
        w.feed = _zero_rows_cols(w.feed, slots)

    for m in w.chronicle.events:
        if m.scope is not None:
            m.scope[slots] = False


# ── the applier ─────────────────────────────────────────────────────

def apply_rebirth(w, slots, parents, rng, heritability=HERITABILITY):
    """Execute the schema for `slots`, parented by `parents`.

    INITIALIZE formulas are verbatim from the pre-0.0b `_be_born` and
    the `birth_*` constructors; only the coverage is new.
    """
    civ, life, h = w.civ, w.life, w.health
    living = np.flatnonzero(h.alive)
    slots = np.asarray(slots)
    parents = np.asarray(parents)

    # relational state first, while the previous occupant's ties are
    # still identifiable
    rebuild_ties(w, slots, parents)

    # civ — INHERIT_PARENT
    for f in ("country", "region", "urban", "education", "income",
              "economic_field", "culture_offset", "power_distance",
              "individualism", "uncertainty_avoidance",
              "long_term_orientation"):
        getattr(civ, f)[slots] = getattr(civ, f)[parents]
    for f in ("religiosity", "ideology", "social_class"):
        a = getattr(civ, f, None)
        if a is not None:
            a[slots] = a[parents]
    for f in ("marital", "employed"):
        a = getattr(civ, f, None)
        if a is not None:
            a[slots] = 0

    # civ — INITIALIZE (verbatim blend; D4-f preserved and logged)
    for t in ("openness", "empathy", "risk_appetite", "doubt",
              "desire_intensity", "conscientiousness", "agreeableness",
              "extraversion", "neuroticism"):
        a = getattr(civ, t)
        a[slots] = np.clip(heritability * a[parents]
                           + (1 - heritability) * float(a[living].mean())
                           + rng.normal(0, 0.08, slots.size), 0.0, 1.0)
    civ.age[slots] = 0.0
    civ.age_bucket[slots] = 0
    if getattr(civ, "person_id", None) is not None:
        civ.parent_id[slots] = civ.person_id[parents]
        civ.person_id[slots] = civ.person_counter + np.arange(
            slots.size, dtype=np.int64)
        civ.person_counter = int(civ.person_counter + slots.size)
    if getattr(life, "partner", None) is not None:
        # a deceased person's partner is widowed; the newborn is single
        life.partner[slots] = -1
    civ.forces[slots] = (civ.forces[parents] * 0.5
                         + civ.forces[living].mean(axis=0) * 0.5)
    civ.alpha[slots] = 0.35

    # life — labour
    from earth1.life import OCC_EDU
    aff = np.exp(-1.2 * np.abs(OCC_EDU[None, :]
                               - civ.education[slots][:, None]))
    p = aff / aff.sum(axis=1, keepdims=True)
    cum = np.cumsum(p, axis=1)
    draw = rng.random(slots.size)[:, None]
    life.occupation[slots] = (draw > cum).sum(axis=1)
    life.firm[slots] = -1
    life.employed[slots] = False
    life.in_lf[slots] = True
    life.wage[slots] = life.wage[parents]
    life.tenure[slots] = 0.0
    life.spells[slots] = 0
    life.deprivation[slots] = 0.0
    life.wealth[slots] = 0.0

    # life — household economics
    for f in ("cost", "policy_net", "durables", "owns_home", "rent"):
        a = getattr(life, f, None)
        if a is not None:
            a[slots] = a[parents]
    if life.durable_spend is not None:
        life.durable_spend[slots] = 0.0
    if life.arrears is not None:
        life.arrears[slots] = 0.0
        life.evicted[slots] = False

    # life — body & self (setpoints heritable from the PARENT)
    if life.mental is not None:
        life.mental_setpoint[slots] = np.clip(
            life.mental_setpoint[parents]
            + rng.normal(0, 0.05, slots.size), 0.0, 1.0)
        life.relationship_setpoint[slots] = np.clip(
            life.relationship_setpoint[parents]
            + rng.normal(0, 0.05, slots.size), 0.0, 1.0)
        life.mental[slots] = life.mental_setpoint[slots]
        life.relationship[slots] = np.clip(
            life.relationship_setpoint[slots]
            + rng.normal(0, 0.05, slots.size), 0.0, 1.0)
        life.addiction[slots] = 0.0
        life.n_events[slots] = 0
        life.last_event[slots] = 0
        life.last_event_day[slots] = -1.0
    life.physical[slots] = np.clip(rng.beta(7.0, 2.0, slots.size), 0, 1)
    life.social_need[slots] = np.clip(rng.beta(2.0, 5.0, slots.size), 0, 1)
    life.political[slots] = np.clip(rng.beta(2.0, 3.0, slots.size), 0, 1)
    if life.force_baseline is not None:
        life.force_baseline[slots] = civ.forces[slots]
    if life.trait_baseline is not None:
        life.trait_baseline[slots] = np.stack(
            [civ.openness[slots], civ.doubt[slots],
             civ.desire_intensity[slots]], axis=1)

    # health — a new body
    h.alive[slots] = True
    h.condition[slots] = 0
    from earth1.types import CauseOfDeath
    h.cause_of_death[slots] = int(CauseOfDeath.ALIVE)
    h.in_treatment[slots] = False
    h.diagnosed_day[slots] = -1.0
    h.lifetime_illnesses[slots] = 0
    if h.declining is not None:
        h.declining[slots] = 0.0
    if h.falls is not None:
        h.falls[slots] = 0

    # knowledge
    kn = w.knowledge
    kn.stock[slots] = np.clip(
        0.35 * kn.stock[parents] + 0.65 * float(kn.stock[living].mean())
        + rng.normal(0, 0.06, slots.size), 0.0, 1.0)
    kn.status[slots] = 0.0
    from earth1.knowledge import CONNECTIVITY, TIERS, _tier
    conn_p = np.array([CONNECTIVITY[t] for t in TIERS])[
        _tier(civ)[slots]]
    kn.connected[slots] = rng.random(slots.size) < conn_p
    kn.works_made[slots] = 0
    kn.discoveries[slots] = 0

    # class
    kl = w.klass
    kl.homeless[slots] = False
    kl.criminal[slots] = False
    kl.days_homeless[slots] = 0
    kl.crimes_committed[slots] = 0
    kl.migrated[slots] = False

    # flourishing
    fl = w.flourishing
    if fl is not None:
        for f in ("hunger", "thirst", "breath"):
            getattr(fl, f)[slots] = getattr(fl, f)[parents]
        fl.hope[slots] = np.clip(rng.beta(4.0, 3.0, slots.size), 0, 1)
        fl.curiosity[slots] = np.clip(
            0.3 + 0.5 * civ.openness[slots]
            + rng.normal(0, 0.10, slots.size), 0, 1)
        fl.meaning[slots] = np.clip(rng.beta(3.5, 3.0, slots.size), 0, 1)
        fl.belonging[slots] = np.clip(life.relationship[slots], 0, 1)
        fl.satisfaction[slots] = np.clip(
            rng.beta(3.0, 3.0, slots.size), 0, 1)
        fl.art_received[slots] = 0.0
        fl.lifetime_joy[slots] = 0.0

    # presence — born where the parent is
    pr = w.presence
    if pr is not None:
        pr.locality[slots] = pr.locality[parents]
        pr.density[slots] = pr.density[parents]
        pr.gathering[slots] = -1

    # mobility — a fresh traveller
    mo = w.mobility
    if mo is not None:
        from earth1.knowledge import _tier as _ktier
        from earth1.mobility import FLIGHTS_PER_CAPITA_YR
        t = _ktier(civ)[slots]
        mo.owns_car[slots] = False
        # verbatim birth_mobility flight formula, evaluated for the slots
        money = np.clip(life.wage[slots]
                        / max(float(np.median(life.wage)), 1e-6), 0, 4)
        fly = np.array([FLIGHTS_PER_CAPITA_YR[k] for k in TIERS])[t]
        mo.flies_per_year[slots] = (fly * money
                                    * (1.0 + 0.6 * civ.urban[slots]))
        mo.commute_minutes[slots] = 0.0
        mo.travelled[slots] = 0
