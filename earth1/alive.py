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

from earth1.influence import propagate, update_conviction, new_day_scratch
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
    w = World(civ=civ, life=life, fabric=fab,
                 feed=build_feed(civ, kn, seed=seed),
                 health=birth_health(pop),
                 knowledge=kn,
                 gov=gov, klass=klass, chronicle=Chronicle(),
                 climate=birth_climate(seed=seed),
                 flourishing=birth_flourishing(civ, life, seed=seed),
                 presence=birth_presence(civ, seed=seed),
                 mobility=birth_mobility(civ, life, seed=seed))
    from earth1.partnership import pair_at_genesis
    pair_at_genesis(w, np.random.default_rng(seed ^ 0x5A5A))   # state only
    return w


# ═══ THE CANONICAL DAY — one authoritative declaration (0.2) ═══════
# These are the values the production civilization has actually lived
# under since Epoch 0. Before 0.2 they existed in FIVE places: the
# daemon's STEP dict (these values), integration.py's copy,
# observe.futures' inline copy, chaos.world_step's DIVERGENT defaults
# (beta 1.0, residue 0.01, critical_fraction 0.15), and live_one_day's
# own defaults — which imported residue/critical_fraction from chaos,
# so every bare live_one_day(w, rng) call (branch, backtest, timeline,
# hormuz, assimilate, every research script) ran residue=0.01/cf=0.15
# while the world ran 0.02/0.12. The instrument and the product
# disagreed. Every entry point now consumes THIS dict; experiments may
# override explicitly, but a default is always this default.
CANONICAL_DAY = dict(beta=2.0, residue=0.02, critical_fraction=0.12,
                     relax=0.045, layers=2)   # relax: IT6 (candidate 76a574c)

# ONE ACCEPTED PHYSICS VERSION. Canonical Earth-1 physics == the
# validated laboratory candidate 76a574c (Phase 0.5 canonicalization,
# ops/alive/CANONICALIZATION_PROGRAM.md). No environment flag selects
# physics; EARTH1_TEST_* flags exist only for the Stage-B broken twins
# and are excluded from production by the release gate.
# Canonical = candidate v2 (76a574c) + H-CASCADE-1 episode-entry
# semantics (39994f0, founder-accepted 2026-08-23). Canonical does not
# mean validated: scientific status PRE-BENCHMARK (see
# ops/alive/CASCADE_PUBLIC_BENCHMARK_PREREG_v1.md).
PHYSICS_VERSION = "0.8-candidate-v4/posthumous-invariant"
# H-CASCADE-1 scope: rules whose firing means episode ENTRY.
EPISODE_ENTRY_RULES = frozenset({"identity_collapse", "collective_surge"})


# Per-agent arrays that constitute ordinary living-agent state. Rows dead
# at tick start are restored to these values at tick end. Health,
# knowledge, flourishing, class, contagion, weather, mobility and
# institutions already mask on alive; this list covers the writers that
# do not: propagate/relax/conviction (civ.forces, civ.alpha), the feed,
# the trait feedback (civ.openness/doubt/desire_intensity), life_tick,
# memory.tick (forces), and advance_age.
DECEASED_FROZEN = (
    ("civ", ("forces", "alpha", "openness", "doubt", "desire_intensity",
             "age")),
    ("life", ("occupation", "firm", "employed", "in_lf", "wage", "wealth",
              "cost", "tenure", "deprivation", "spells", "mental",
              "physical", "addiction", "relationship", "social_need",
              "political", "policy_net", "durables", "durable_spend",
              "owns_home", "rent", "arrears", "evicted", "last_event",
              "last_event_day", "n_events")),
)


def _living_view(adj, alive):
    """The graph as today's active dynamics see it: every edge INTO a
    deceased row carries zero weight. A per-tick view; the stored graph
    is untouched (relationship existence survives death)."""
    if alive.all():
        return adj
    m = adj.tocsr(copy=True)
    m.data = m.data * alive[m.indices]
    m.eliminate_zeros()
    return m


def _snapshot_deceased(w, dead):
    snap = {}
    for sub, names in DECEASED_FROZEN:
        o = getattr(w, sub)
        for nm in names:
            a = getattr(o, nm, None)
            if isinstance(a, np.ndarray) and a.shape[0] == dead.shape[0]:
                snap[(sub, nm)] = a[dead].copy()
    return snap


def _restore_deceased(w, dead, snap):
    for (sub, nm), v in snap.items():
        getattr(getattr(w, sub), nm)[dead] = v


def cascade_residue_levels(residues, day):
    """Recovered f933c59 EventLog semantics (PF-DECAY-1, frozen):
    factor = 2^(-(day - t_f)/h); h <= 0 means factor 1.0 — a PERMANENT
    level, not zero; a residue leaves the active set when factor < 0.01
    or max|effect|*factor < 0.01. Returns (levels, surviving) where
    levels is a list of (loc_key, signed level vector) over the active
    set. Pure — the PF-DECAY-1 KAs test this function against the
    analytic law directly."""
    levels, surviving = [], []
    for r in residues:
        dt = day - r["day"]
        h = r["h"]
        factor = 1.0 if h <= 0 else 2.0 ** (-dt / h)
        mx = float(np.max(np.abs(r["effects"])))
        if factor < 0.01 or mx * factor < 0.01:
            continue
        surviving.append(r)
        levels.append((r["loc"], r["effects"] * factor))
    return levels, surviving


def effective_forces(w):
    """PF-DECAY-2: the EXPRESSION view — stored forces plus the
    read-time cascade-residue overlay (legacy f933c59
    effective_deltas semantics: summed active levels per locality,
    total clipped to ±0.5, result clipped to [0,1]). Consumed by the
    readout layer only; the dynamic loop and the transition detector
    read w.civ.forces (the trigger substrate) directly. Derived, not
    evolved: calling this never mutates state."""
    civ = w.civ

    def _ro(a):
        # the effective view is IMMUTABLE: a consumer that tried to
        # write through it would otherwise alias canonical state in
        # the no-residue branch — the exact hidden-feedback path the
        # consumer-audit ruling forbids. Mutation raises loudly.
        v = a.view()
        v.setflags(write=False)
        return v

    res = getattr(w.chronicle, "cascade_residues", None)
    if not res:
        return _ro(civ.forces)
    levels, _ = cascade_residue_levels(res, w.day)
    if not levels:
        return _ro(civ.forces)
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2
           + civ.urban.astype(np.int64))
    shift = np.zeros_like(civ.forces)
    for lk, vec in levels:
        shift[loc == lk] += vec
    np.clip(shift, -0.5, 0.5, out=shift)
    return _ro(np.clip(civ.forces + shift, 0.0, 1.0))


def live_one_day(w: World, rng, *,
                 beta: float = CANONICAL_DAY["beta"],
                 residue: float = CANONICAL_DAY["residue"],
                 critical_fraction: float = CANONICAL_DAY["critical_fraction"],
                 relax: float = CANONICAL_DAY["relax"],
                 layers: int = CANONICAL_DAY["layers"],
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
    # POSTHUMOUS INVARIANT (founder ruling 2026-08-23, ops/alive/
    # POSTHUMOUS_INFLUENCE.md): death ends active agency, not legacy.
    # Rows dead at tick START take no ordinary living-agent update this
    # tick: their last living state is restored at the end of the tick
    # (see _restore_deceased). Explicit legacy paths — bereavement at
    # death, memories whose scope includes them, inheritance at rebirth
    # — do not read these rows dynamically and are untouched.
    _dead0 = ~w.health.alive
    _dead0_alive = w.health.alive.copy()
    _frozen = _snapshot_deceased(w, _dead0) if _dead0.any() else None
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
        # recompose=False: rehome_employment always recomposes adj right
        # below, and nothing reads adj between the two calls (0.7
        # profile: each recompose ~7% of a 4M world-day)
        st["rehomed_migrants"] = rehome_migrants(w, _migrated, rng,
                                                 recompose=False)
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

    target = life_force_target(civ, life, w.flourishing)
    # the day's encounter evidence (consumed by update_conviction)
    scratch = new_day_scratch(civ.n)
    # a homeless person's circumstances are not their wage: being on the
    # street is its own condition and it dominates
    if w.klass.homeless.any():
        hm = w.klass.homeless
        target[hm, Force.FEAR] = np.clip(target[hm, Force.FEAR] + 0.25, 0, 1)
        target[hm, Force.COLLECTIVE] = np.clip(
            target[hm, Force.COLLECTIVE] - 0.20, 0, 1)

    # PF-DECAY-2 (founder-ruled open-loop topology): the recovered
    # decay_half_life residues NEVER enter the dynamic loop. Stored
    # forces are the trigger substrate B_t (f933c59 semantics: the
    # detector and every world operator read raw state); the decaying
    # level is a READ-TIME OVERLAY served by effective_forces() to
    # the readout layer only. The PF-DECAY-1 target-path application
    # was the accidental self-excitation edge and is gone. Residue
    # expiry is maintained in the cascade step below.
    import os as _os

    # ── STAGE-B BROKEN TWINS (TEST-ONLY; Standing Rule 2) ─────────
    # These flags deliberately reintroduce ruled-out defects so the
    # acceptance instruments can prove they detect them. They are
    # never set outside the adversarial battery.
    if _os.environ.get("EARTH1_TEST_CLOSED_LOOP") == "1":
        # B7: the PF-DECAY-1 closed loop, resurrected: residues feed
        # the target path again
        _cres = getattr(w.chronicle, "cascade_residues", None)
        if _cres:
            _lv, _ = cascade_residue_levels(_cres, w.day)
            if _lv:
                _locr = (civ.country.astype(np.int64) * 1000
                         + civ.region.astype(np.int64) * 2
                         + civ.urban.astype(np.int64))
                _sh = np.zeros_like(target)
                for _lk, _vec in _lv:
                    _sh[_locr == _lk] += _vec
                np.clip(_sh, -0.5, 0.5, out=_sh)
                target = np.clip(target + _sh, 0.0, 1.0)

    # 7 influence, 8 circumstance
    from earth1.susceptibility import compute as susceptibility_of
    sus = susceptibility_of(civ, life, w.flourishing)
    # POSTHUMOUS INVARIANT: the deceased are not ordinary peers. Edges
    # to dead rows are kept (relationship existence is history) but
    # carry no weight in today's active dynamics — partner sampling,
    # conviction evidence and the neighbourhood feedback all see a
    # living-only view. No edge is deleted here.
    adj_live = _living_view(civ.adj, w.health.alive)
    civ.forces = propagate(civ.forces, civ.alpha, adj_live,
                           day=w.day + 1, scratch=scratch,
                           susceptibility=sus)
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
        st.update(feed_tick(civ, _living_view(w.feed, w.health.alive),
                            civ.alpha, day=w.day + 1, scratch=scratch,
                            susceptibility=sus))
    st["mean_susceptibility_fear"] = float(sus[:, Force.FEAR].mean())
    st["susceptibility_spread"] = float(sus.std())
    civ.forces = np.clip(civ.forces + relax * (target - civ.forces), 0.0, 1.0)
    civ.alpha = update_conviction(civ.forces, civ.alpha, adj_live,
                                  scratch=scratch)

    # 5b tie plasticity (0.5 port) — the fabric responds to the day's
    # interaction: agreement strengthens friends/weak ties, disagreement
    # weakens, a few people find kindred replacements. Runs right after
    # influence+conviction because that IS the interaction. One
    # execution point; friends+weak only (ledger tie_type_ownership).
    from earth1.plasticity import plasticity_tick
    st.update(plasticity_tick(w, rng, dt_days))

    # 6 memory — what happened is still happening, and still spreading
    st.update(w.chronicle.tick(civ, dt_days))
    st["memory_spread"] = w.chronicle.spread(civ, rng)

    # 9 cascade
    from earth1.thresholds import TRANSITION_RULES
    loc = (civ.country.astype(np.int64) * 1000
           + civ.region.astype(np.int64) * 2 + civ.urban.astype(np.int64))
    uloc, li = np.unique(loc, return_inverse=True)
    nl = int(li.max()) + 1
    pop_l = np.bincount(li, weights=w.health.alive.astype(np.float64),
                        minlength=nl)          # living residents only
    fired = 0
    # 0.8 probe-1 CONTRADICTION repair (founder-authorized,
    # experimental flag): TransitionRule declares cooldown_days but the
    # incumbent block never read it, so threshold "events" fired every
    # day a locality stayed hot — a -0.10 event became a -0.10/day
    # grinder that railed IDENTITY/TEMPERAMENT. With
    # EARTH1_CASCADE_COOLDOWN=1 a (rule, locality) pair fires at most
    # once per its declared cooldown. State lives on the chronicle
    # (cascades are events; the chronicle is the event memory), created
    # lazily ONLY under the flag so incumbent hashes are untouched, and
    # persists through the canonical serializer for exact restart.
    # decay_half_life remains declared-but-unconsumed: its intended
    # state semantics are ambiguous — recorded as a second unresolved
    # contradiction, NOT invented here.
    # CANONICAL (candidate 76a574c): cooldown per (rule, locality),
    # strict-<, restart-persistent (probe-1 contract, f933c59
    # semantics); a firing creates bounded residue state whose decaying
    # level is a READ-TIME OVERLAY (effective_forces) — open-loop
    # (PF-DECAY-2): nothing here writes stored forces. The legacy
    # instant permanent write is gone.
    if getattr(w.chronicle, "cascade_last_fired", None) is None:
        w.chronicle.cascade_last_fired = {}
    # H-CASCADE-1 (ops/alive/H_CASCADE_1.md, CANONICAL 2026-08-23): for the
    # EPISODE_ENTRY_RULES a firing means ENTRY into an episode
    # (cold→hot), never "still hot after the cooldown elapsed".
    # Episode state = set of (rule, locality) currently hot, on the
    # chronicle (persisted/cloned with it). None ⇒ uninitialized: the
    # first step records the current hot set and fires nothing for the
    # scoped rules (no synthetic day-zero transition).
    _ep = getattr(w.chronicle, "cascade_episode_active", None)
    _ep_init = _ep is None
    if _ep_init:
        _ep = w.chronicle.cascade_episode_active = set()
    _cres = getattr(w.chronicle, "cascade_residues", None)
    if _cres:
        # expiry maintenance only (legacy 0.01 active-set rule)
        _, _surv = cascade_residue_levels(_cres, w.day)
        w.chronicle.cascade_residues = _surv
        st["cascade_residue_active"] = len(_surv)
    # B8 broken twin (TEST-ONLY): detector reads the EFFECTIVE view —
    # the contaminated-substrate defect KA10 must catch
    _det_forces = civ.forces
    if _os.environ.get("EARTH1_TEST_DETECTOR_EFFECTIVE") == "1":
        _det_forces = np.asarray(effective_forces(w))
    for rule in TRANSITION_RULES:
        if rule.region_scope != "regional":
            continue
        met = w.health.alive.copy()         # the dead do not participate
        for force, op, thresh in rule.conditions:
            col = _det_forces[:, force.value]
            met &= (col > thresh) if op == ">" else (col < thresh)
        frac = np.bincount(li, weights=met.astype(np.float64),
                           minlength=nl) / np.maximum(pop_l, 1.0)
        hot = (frac >= critical_fraction) & (pop_l >= 10)
        if rule.name in EPISODE_ENTRY_RULES:
            hot_now = {(rule.name, int(uloc[h]))
                       for h in np.flatnonzero(hot)}
            mine = {k for k in _ep if k[0] == rule.name}
            _ep -= mine - hot_now              # hot→cold: close
            entered = hot_now - mine           # cold→hot: open
            _ep |= entered
            if _ep_init:
                entered = set()                # establish state only
            for hidx in np.flatnonzero(hot):
                if (rule.name, int(uloc[hidx])) not in entered:
                    hot[hidx] = False          # hot→hot: no event
        if hot.any():
            state = w.chronicle.cascade_last_fired
            for hidx in np.flatnonzero(hot):
                key = (rule.name, int(uloc[hidx]))
                last = state.get(key)
                if last is not None and \
                        (w.day - last) < rule.cooldown_days:
                    hot[hidx] = False
                else:
                    state[key] = int(w.day)
        if not hot.any():
            continue
        fired += int(hot.sum())
        if getattr(w.chronicle, "cascade_residues", None) is None:
            w.chronicle.cascade_residues = []
        eff = np.zeros(civ.forces.shape[1])
        for fname, delta in rule.effects.items():
            k = getattr(Force, fname.upper(), None)
            if k is not None:
                eff[k] = delta
        for hidx in np.flatnonzero(hot):
            w.chronicle.cascade_residues.append(
                {"rule": rule.name, "loc": int(uloc[hidx]),
                 "day": int(w.day), "effects": eff.copy(),
                 "h": float(rule.decay_half_life)})
    st["cascades_fired"] = fired

    # 10 feedback — local, never global
    deg = np.maximum(np.asarray(adj_live.sum(axis=1)).ravel(), 1.0)
    dev = civ.forces - (adj_live @ civ.forces) / deg[:, None]
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
    # the newly dead leave the labour force and their firm (a death is
    # the end of employment; rebirth already resets these on reuse)
    if _frozen is not None:
        _restore_deceased(w, _dead0, _frozen)
    _dead_now = ~w.health.alive
    # partnership is state only: a death widows the survivor
    from earth1.partnership import dissolve_on_death
    st["widowed"] = dissolve_on_death(life, _dead_now & _dead0_alive)
    _rel = _dead_now & (life.employed | life.in_lf | (life.firm >= 0))
    if _rel.any():
        life.employed[_rel] = False
        life.in_lf[_rel] = False
        life.firm[_rel] = -1
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
    # 0.7 precision modes: fold mid-tick f64 reassignments back to the
    # world's declared precision at the day boundary. No-op (an
    # attribute check) for the float64 reference Earth.
    if getattr(w, "_precision", None) not in (None, "float64"):
        from earth1.precision import recoerce
        recoerce(w)
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
