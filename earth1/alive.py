"""ALIVE — one world, and one day of it.

Everything that exists in Earth-1 is held here, and `live_one_day` runs
all of it in the order that makes the couplings true:

   1  MATTER        jobs, firms, money, needs                life.py
   2  BODIES        disease, cancer, hospitals, dying        health.py
   3  INSTITUTIONS  governments decide; war lands on people  institutions.py
   4  CLASS         homelessness, crime, wealth, migration   institutions.py
   5  KNOWLEDGE     learning, status, discovery, creation    knowledge.py
   6  MEMORY        what happened is still happening         memory.py
   7  INFLUENCE     the conviction kernel                    influence.py
   8  CIRCUMSTANCE  the restoring pull toward your own life  life.py
   9  CASCADE       local thresholds fire                    thresholds.py
  10  FEEDBACK      absorbed force leaves a permanent mark   chaos.py

The order is not arbitrary. Governments must see yesterday's suffering
before they set today's welfare; welfare must be set before anyone's
deprivation is computed; deprivation must be computed before it can
push someone into crime or onto the street; and all of it must happen
before opinion, because opinion is downstream of life.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from earth1.chaos import CRITICAL_FRACTION, RELAX, RESIDUE_RATE
from earth1.influence import propagate, update_conviction
from earth1.types import Force


@dataclass
class World:
    civ: object
    life: object
    fabric: object
    health: object
    knowledge: object
    gov: object
    klass: object
    chronicle: object
    day: int = 0


def birth_world(pop: int, seed: int = 42) -> World:
    from earth1.fabric import build_fabric
    from earth1.genesis import genesis
    from earth1.health import birth_health
    from earth1.institutions import birth_institutions
    from earth1.knowledge import birth_knowledge
    from earth1.life import birth_life
    from earth1.memory import Chronicle

    civ = genesis(pop, seed)
    life = birth_life(civ, seed=seed)
    fab = build_fabric(civ, life, seed=seed)
    civ.adj = fab.adj
    gov, klass = birth_institutions(civ, seed=seed)
    return World(civ=civ, life=life, fabric=fab,
                 health=birth_health(pop),
                 knowledge=birth_knowledge(civ, life, seed=seed),
                 gov=gov, klass=klass, chronicle=Chronicle())


def live_one_day(w: World, rng, *, beta: float = 2.0,
                 residue: float = RESIDUE_RATE,
                 critical_fraction: float = CRITICAL_FRACTION,
                 relax: float = RELAX, layers: int = 2,
                 dt_days: float = 1.0) -> dict:
    from earth1.health import health_tick
    from earth1.institutions import apply_policy_and_war, class_tick, govern
    from earth1.knowledge import knowledge_tick
    from earth1.life import life_force_target, life_tick

    civ, life = w.civ, w.life
    alive = w.health.alive
    st = {}

    # 3 first: governments decide on YESTERDAY's state, and their policy
    # is what today's deprivation will be computed against
    st.update(govern(civ, life, w.gov, rng, dt_days))
    st.update(apply_policy_and_war(civ, life, w.gov, w.health, rng, dt_days))

    # 1 matter
    st.update(life_tick(civ, life, rng, dt_days=dt_days, couple_forces=False))
    # 2 bodies
    st.update(health_tick(civ, life, w.health, rng, float(w.day), dt_days))
    # 4 class
    st.update(class_tick(civ, life, w.knowledge, w.gov, w.klass, rng,
                         dt_days, alive=w.health.alive))
    # 5 knowledge
    st.update(knowledge_tick(civ, life, w.knowledge, rng, dt_days,
                             alive=w.health.alive))

    target = life_force_target(civ, life)
    # a homeless person's circumstances are not their wage: being on the
    # street is its own condition and it dominates
    if w.klass.homeless.any():
        hm = w.klass.homeless
        target[hm, Force.FEAR] = np.clip(target[hm, Force.FEAR] + 0.25, 0, 1)
        target[hm, Force.COLLECTIVE] = np.clip(
            target[hm, Force.COLLECTIVE] - 0.20, 0, 1)

    # 7 influence, 8 circumstance
    civ.forces = propagate(civ.forces, civ.alpha, civ.adj, beta=beta,
                           layers=layers)
    civ.forces = np.clip(civ.forces + relax * (target - civ.forces), 0.0, 1.0)
    civ.alpha = update_conviction(civ.forces, civ.alpha, civ.adj)

    # 6 memory — what happened is still happening, and still spreading
    st.update(w.chronicle.tick(civ, dt_days))
    st["memory_spread"] = w.chronicle.spread(civ)

    # 9 cascade
    from earth1.thresholds import TRANSITION_RULES
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2 + civ.urban.astype(np.int64))
    _, li = np.unique(loc, return_inverse=True)
    nl = int(li.max()) + 1
    pop_l = np.bincount(li, minlength=nl).astype(np.float64)
    fired = 0
    for rule in TRANSITION_RULES:
        if rule.region_scope != "regional":
            continue
        met = np.ones(civ.n, dtype=bool)
        for force, op, thresh in rule.conditions:
            col = civ.forces[:, force.value]
            met &= (col > thresh) if op == ">" else (col < thresh)
        frac = np.bincount(li, weights=met.astype(np.float64),
                           minlength=nl) / np.maximum(pop_l, 1.0)
        hot = (frac >= critical_fraction) & (pop_l >= 10)
        if not hot.any():
            continue
        fired += int(hot.sum())
        m = hot[li]
        for fname, delta in rule.effects.items():
            k = getattr(Force, fname.upper(), None)
            if k is not None:
                civ.forces[m, k] = np.clip(civ.forces[m, k] + delta, 0, 1)
    st["cascades_fired"] = fired

    # 10 feedback — local, never global
    deg = np.maximum(np.asarray(civ.adj.sum(axis=1)).ravel(), 1.0)
    dev = civ.forces - (civ.adj @ civ.forces) / deg[:, None]
    civ.openness = np.clip(civ.openness + residue * dev[:, Force.CULTURE],
                           0, 1)
    civ.doubt = np.clip(civ.doubt + residue * dev[:, Force.FEAR], 0, 1)
    civ.desire_intensity = np.clip(
        civ.desire_intensity + residue * dev[:, Force.DESIRE], 0, 1)

    # ── BIRTH: a death frees a place, and someone new takes it ───────
    # Without this the world only ever shrinks. A newborn enters at 18
    # in the same country, inheriting traits from a living parent —
    # which is how a population carries its culture forward while
    # remaining a different population than the one before it.
    st.update(_be_born(w, rng))

    w.day += 1
    return st


def _be_born(w: World, rng, heritability: float = 0.45) -> dict:
    """Fill the places the dead left. Inheritance, not cloning."""
    civ, life, h = w.civ, w.life, w.health
    slots = np.flatnonzero(~h.alive)
    if slots.size == 0:
        return {"births": 0}
    living = np.flatnonzero(h.alive)
    if living.size < 10:
        return {"births": 0}

    # a country's births are proportional to its living population, so
    # the world's composition follows its own demography rather than a
    # global average
    parents = rng.choice(living, slots.size)
    civ.country[slots] = civ.country[parents]
    civ.region[slots] = civ.region[parents]
    civ.urban[slots] = civ.urban[parents]

    for t in ("openness", "empathy", "risk_appetite", "doubt",
              "desire_intensity", "conscientiousness", "agreeableness",
              "extraversion", "neuroticism"):
        a = getattr(civ, t)
        a[slots] = np.clip(heritability * a[parents]
                           + (1 - heritability) * float(a[living].mean())
                           + rng.normal(0, 0.08, slots.size), 0.0, 1.0)
    civ.age[slots] = 0.0                       # eighteen years old
    civ.age_bucket[slots] = 0
    civ.education[slots] = civ.education[parents]
    civ.forces[slots] = civ.forces[parents] * 0.5 + \
        civ.forces[living].mean(axis=0) * 0.5
    civ.alpha[slots] = 0.35                    # the young are not certain

    # a new life, materially: no savings, no scars, no history
    life.wealth[slots] = 0.0
    life.spells[slots] = 0
    life.tenure[slots] = 0.0
    life.employed[slots] = False
    life.in_lf[slots] = True
    life.firm[slots] = -1
    life.deprivation[slots] = 0.0
    if life.mental is not None:
        life.mental[slots] = life.mental_setpoint[slots]
        life.addiction[slots] = 0.0
        life.n_events[slots] = 0
        life.last_event[slots] = 0
    if life.force_baseline is not None:
        life.force_baseline[slots] = civ.forces[slots]
    if life.trait_baseline is not None:
        life.trait_baseline[slots] = np.stack(
            [civ.openness[slots], civ.doubt[slots],
             civ.desire_intensity[slots]], axis=1)

    w.knowledge.stock[slots] = np.clip(
        0.35 * w.knowledge.stock[parents]
        + 0.65 * float(w.knowledge.stock[living].mean())
        + rng.normal(0, 0.06, slots.size), 0.0, 1.0)
    w.knowledge.works_made[slots] = 0
    w.knowledge.discoveries[slots] = 0
    w.klass.homeless[slots] = False
    w.klass.criminal[slots] = False
    w.klass.crimes_committed[slots] = 0

    h.alive[slots] = True
    h.condition[slots] = 0
    h.cause_of_death[slots] = 0
    h.in_treatment[slots] = False
    h.diagnosed_day[slots] = -1.0
    h.lifetime_illnesses[slots] = 0
    return {"births": int(slots.size)}
