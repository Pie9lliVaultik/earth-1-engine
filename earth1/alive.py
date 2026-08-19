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
    feed: object = None
    climate: object = None
    flourishing: object = None
    presence: object = None      # where bodies physically are
    mobility: object = None      # cars, flights, roads
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
    from earth1.contagion import birth_presence
    from earth1.flourishing import birth_flourishing
    from earth1.mobility import birth_mobility
    from earth1.weather import birth_climate

    gov, klass = birth_institutions(civ, seed=seed)
    kn = birth_knowledge(civ, life, seed=seed)
    from earth1.feed import build_feed
    return World(civ=civ, life=life, fabric=fab,
                 feed=build_feed(civ, kn, seed=seed),
                 health=birth_health(pop),
                 knowledge=kn,
                 gov=gov, klass=klass, chronicle=Chronicle(),
                 climate=birth_climate(seed=seed),
                 flourishing=birth_flourishing(civ, life, seed=seed),
                 presence=birth_presence(civ, seed=seed),
                 mobility=birth_mobility(civ, life, seed=seed))


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
    alive_at_tick_start = int(w.health.alive.sum())
    st.update(govern(civ, life, w.gov, rng, dt_days))
    st.update(apply_policy_and_war(civ, life, w.gov, w.health, rng, dt_days))

    # 0.0a time — everyone is one day older. Before life/health so the
    # day's hazards (cancer t^5, falls, road deaths, fertility) see
    # today's age, and before _be_born so newborns are not aged on
    # their birth day. Age was frozen here for the world's entire
    # pre-Epoch-1 history (BIBLE R17).
    from earth1.generational import advance_age
    advance_age(civ, dt_days)

    # 1 matter
    st_life = life_tick(civ, life, rng, dt_days=dt_days, couple_forces=False)
    _lost = st_life.pop("lost_idx", None)
    _found = st_life.pop("found_idx", None)
    st.update(st_life)
    # 2 bodies
    st.update(health_tick(civ, life, w.health, rng, float(w.day), dt_days))
    # 4 class
    st_cls = class_tick(civ, life, w.knowledge, w.gov, w.klass, rng,
                        dt_days, alive=w.health.alive)
    _migrated = st_cls.pop("migrated_idx", None)
    st.update(st_cls)

    # 0.0d — the fabric follows the person: severed and rebuilt through
    # the declared re-homing policies, one batched pass per day
    if (_migrated is not None and len(_migrated)) or        (_lost is not None and len(_lost)) or        (_found is not None and len(_found)):
        from earth1.rehome import rehome_employment, rehome_migrants
        st["rehomed_migrants"] = rehome_migrants(w, _migrated, rng)
        # migration ENDS the job (class_tick sets employed=False after
        # life_tick has already built its lost set), so migrants must be
        # merged into the employment severing or their colleague ties
        # outlive the move — found in production: 179 of 180 phantom
        # workplaces in the first 0.0d window were exactly the employed
        # migrants. This is the VIA_EMPLOYMENT policy, actually wired.
        _lost_all = _lost
        if _migrated is not None and len(_migrated):
            base = _lost if _lost is not None else np.array([], dtype=np.int64)
            _lost_all = np.unique(np.concatenate([base, _migrated]))
        st["rehomed_workers"] = rehome_employment(w, _lost_all, _found, rng)
    # 5 knowledge
    st.update(knowledge_tick(civ, life, w.knowledge, rng, dt_days,
                             alive=w.health.alive))

    # 5b THE SKY — a correlated shock that lands on a PLACE
    if w.climate is not None:
        from earth1.weather import weather_tick
        st.update(weather_tick(civ, life, w.health, w.climate, rng,
                               dt_days, alive=w.health.alive))

    # 5c THE BODY'S DEMANDS AND THE REASONS TO KEEP GOING
    if w.flourishing is not None:
        from earth1.flourishing import flourishing_tick
        st.update(flourishing_tick(
            civ, life, w.flourishing, w.knowledge, w.health, rng, dt_days,
            alive=w.health.alive,
            discoveries_today=st.get("discoveries_today", 0),
            works_today=st.get("works_today", 0),
            welfare=w.gov.welfare[civ.country],
            soil=w.climate.soil if w.climate is not None else None))

    target = life_force_target(civ, life)
    # a homeless person's circumstances are not their wage: being on the
    # street is its own condition and it dominates
    if w.klass.homeless.any():
        hm = w.klass.homeless
        target[hm, Force.FEAR] = np.clip(target[hm, Force.FEAR] + 0.25, 0, 1)
        target[hm, Force.COLLECTIVE] = np.clip(
            target[hm, Force.COLLECTIVE] - 0.20, 0, 1)

    # 7 influence, 8 circumstance
    from earth1.susceptibility import compute as susceptibility_of
    sus = susceptibility_of(civ, life, w.flourishing)
    civ.forces = propagate(civ.forces, civ.alpha, civ.adj, beta=beta,
                           layers=layers, susceptibility=sus)
    # ── BODIES IN THE SAME PLACE ─────────────────────────────────────
    # Contagion runs AFTER the conviction kernel and before the feed,
    # because that is the real order of a day: you are among people, you
    # talk to the people you know, then you look at a screen. Three
    # geometries, three timescales, three different things transmitted.
    if w.presence is not None:
        from earth1.contagion import contagion_tick, shared_attention
        st.update(contagion_tick(civ, life, w.presence, rng,
                                 susceptibility=sus, dt_days=dt_days,
                                 alive=w.health.alive))
        st.update(shared_attention(civ, w.presence, rng, dt_days,
                                   alive=w.health.alive,
                                   susceptibility=sus))

    # ── MOVING AROUND: roads kill, flights mix and import disease ────
    if w.mobility is not None:
        from earth1.mobility import mobility_tick
        st.update(mobility_tick(civ, life, w.mobility, w.health,
                                w.flourishing, rng, dt_days,
                                alive=w.health.alive))

    # THE FEED — a different physics, applied after conversation
    if w.feed is not None:
        from earth1.feed import feed_tick
        st.update(feed_tick(civ, w.feed, civ.alpha, susceptibility=sus,
                            beta=beta, dt_days=dt_days))
    st["mean_susceptibility_fear"] = float(sus[:, Force.FEAR].mean())
    st["susceptibility_spread"] = float(sus.std())
    civ.forces = np.clip(civ.forces + relax * (target - civ.forces), 0.0, 1.0)
    civ.alpha = update_conviction(civ.forces, civ.alpha, civ.adj)

    # 6 memory — what happened is still happening, and still spreading
    st.update(w.chronicle.tick(civ, dt_days))
    st["memory_spread"] = w.chronicle.spread(civ, rng)

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

    # ── 0.1d: the end-of-tick mortality contract ─────────────────────
    # "deaths" means GROSS deaths across the COMPLETE tick — every
    # killer (disease, war, weather, want, road), counted after all of
    # them and after births, so the identity
    #     alive_end == alive_start - deaths + births
    # closes exactly, every day. health_tick's own count (disease only)
    # is preserved under an explicit name; its mid-tick "alive" reading
    # is overwritten with the terminal one. The journal's previous
    # "deaths" undercounted by every late-tick killer (0.1 ledger).
    st["disease_deaths"] = int(st.get("deaths", 0))
    alive_at_tick_end = int(w.health.alive.sum())
    st["deaths"] = (alive_at_tick_start - alive_at_tick_end
                    + int(st.get("births", 0)))
    st["alive"] = alive_at_tick_end

    w.day += 1
    return st


def _be_born(w: World, rng, heritability: float = 0.45) -> dict:
    """Children are CONCEIVED, not conjured to replace the dead.

    Filling every empty slot each tick conserved the population exactly,
    which is false of every real society — it can never grow and can
    never collapse. Births now come from partnered people of fertile age
    at a rate set by their country's fertility, and they occupy free
    capacity. When births outrun deaths the population grows; when they
    do not, it shrinks.
    """
    from earth1.genesis import GENESIS_COUNTRIES
    civ, life, h = w.civ, w.life, w.health
    free = np.flatnonzero(~h.alive)
    if free.size == 0:
        return {"births": 0, "population": int(h.alive.sum())}
    living = np.flatnonzero(h.alive)
    if living.size < 10:
        return {"births": 0, "population": int(living.size)}

    tfr = np.array([float(c.get("tfr", 2.0) or 2.0)
                    for c in GENESIS_COUNTRIES])
    # a woman has TFR children across ~25 fertile years; half the
    # population bears them, so the per-capita daily hazard is small
    fertile = (h.alive & (civ.age > 0.03) & (civ.age < 0.45)
               & (life.relationship > 0.55)
               & (np.clip(life.deprivation, 0, 1) < 0.6))
    rate = tfr[civ.country] / (25.0 * 365.0) * 0.5
    conceived = fertile & (rng.random(civ.n) < rate)
    n_new = int(min(conceived.sum(), free.size))
    if n_new == 0:
        return {"births": 0, "population": int(h.alive.sum())}
    slots = free[:n_new]
    parents = np.flatnonzero(conceived)[:n_new]

    # THE CENTRAL RESET SCHEMA (0.0b). Every per-agent field's rebirth
    # behaviour is declared in earth1/rebirth.py and enforced by CI —
    # never a hand-maintained scatter of assignments here. The previous
    # occupant's ties, body, home, memories and record are gone; the
    # newborn is birth initialization plus declared parental
    # inheritance, nothing else.
    from earth1.rebirth import apply_rebirth
    apply_rebirth(w, slots, parents, rng, heritability=heritability)

    return {"births": int(slots.size),
            "population": int(h.alive.sum())}
