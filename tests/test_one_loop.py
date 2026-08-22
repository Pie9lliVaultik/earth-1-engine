"""Phase 0.2 semantic invariants — there is ONE definition of a day.

`live_one_day` is canonical physics; `chaos.world_step` is only a
wrapper over it. Each required failing control deliberately breaks the
mechanism and proves the invariant catches it.
"""
import copy

import numpy as np
import pytest

from earth1 import chaos, persistence
from earth1.alive import CANONICAL_DAY, live_one_day
from earth1.chaos import world_step


# ── invariants 1+2: N-step state parity between entry points ────────

@pytest.mark.parametrize("n_steps", [1, 5])
def test_entry_points_produce_identical_state(tiny_world, n_steps):
    """world_step(w) == live_one_day(w) for N consecutive steps, from
    identical state + identical RNG. Same persistent state, bit-exact."""
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    ra, rb = np.random.default_rng(99), np.random.default_rng(99)
    for _ in range(n_steps):
        world_step(a, ra)
        live_one_day(b, rb)
    assert persistence.world_hash(a) == persistence.world_hash(b)
    # invariant 6: RNG consumption identical — the streams must be in
    # the same state afterwards
    assert ra.bit_generator.state == rb.bit_generator.state


def test_entry_points_interchangeable_mid_stream(tiny_world):
    """Mixing entry points day by day equals either alone — there is no
    'chaos mode' the world can be in."""
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    ra, rb = np.random.default_rng(5), np.random.default_rng(5)
    world_step(a, ra); live_one_day(a, ra); world_step(a, ra)
    live_one_day(b, rb); live_one_day(b, rb); live_one_day(b, rb)
    assert persistence.world_hash(a) == persistence.world_hash(b)


def test_reduced_stepper_would_fail_parity(tiny_world):
    """Failing control: a reduced (civ,life)-only stepper — the OLD
    world_step's physics — must diverge from the canonical loop."""
    from earth1.influence import (propagate, update_conviction,
                                  new_day_scratch)
    from earth1.life import life_force_target, life_tick

    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    ra, rb = np.random.default_rng(3), np.random.default_rng(3)
    live_one_day(a, ra)
    # the reduced day: matter + influence + conviction only
    civ, life = b.civ, b.life
    life_tick(civ, life, rb, dt_days=1.0, couple_forces=False)
    target = life_force_target(civ, life, b.flourishing)
    scratch = new_day_scratch(civ.n)
    civ.forces = propagate(civ.forces, civ.alpha, civ.adj,
                           day=b.day + 1, scratch=scratch)
    civ.forces = np.clip(civ.forces + CANONICAL_DAY["relax"]
                         * (target - civ.forces), 0, 1)
    civ.alpha = update_conviction(civ.forces, civ.alpha, civ.adj,
                                  scratch=scratch)
    assert persistence.world_hash(a) != persistence.world_hash(b), \
        "the parity instrument cannot distinguish reduced physics"


def test_historical_beta_would_fail_parity(tiny_world):
    """Failing control: the old hard-coded beta=1.0 must be detectably
    different from the canonical day."""
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    world_step(a, np.random.default_rng(7))
    # post-canonicalization the social law has no beta; the historical
    # divergent default that the canonical day still consumes is relax
    # (0.25 incumbent vs 0.045 canonical)
    world_step(b, np.random.default_rng(7), relax=0.25)
    assert persistence.world_hash(a) != persistence.world_hash(b)


# ── invariant 5: one authoritative configuration ────────────────────

def test_beta_has_one_declaration():
    """Every entry point consumes CANONICAL_DAY. No local copies, no
    divergent defaults anywhere on the live path."""
    import inspect

    from earth1 import alive, integration, observe
    import scripts.world_alive as daemon

    assert daemon.STEP is alive.CANONICAL_DAY
    assert integration.STEP is alive.CANONICAL_DAY
    sig = inspect.signature(alive.live_one_day)
    assert sig.parameters["beta"].default == alive.CANONICAL_DAY["beta"]
    assert sig.parameters["residue"].default == \
        alive.CANONICAL_DAY["residue"]
    assert sig.parameters["critical_fraction"].default == \
        alive.CANONICAL_DAY["critical_fraction"]
    # chaos carries NO configuration of its own any more
    src = inspect.getsource(chaos)
    for needle in ("RESIDUE_RATE =", "CRITICAL_FRACTION =", "RELAX =",
                   "beta: float = 1.0"):
        assert needle not in src, f"chaos.py still declares {needle!r}"


def test_wrapper_has_no_physics():
    """world_step must contain no simulation of its own — delegation
    only. If someone re-grows a second loop here, this fails."""
    import inspect
    src = inspect.getsource(chaos.world_step)
    assert "live_one_day" in src
    for forbidden in ("propagate(", "life_tick(", "TRANSITION_RULES",
                      "bincount", "np.clip"):
        assert forbidden not in src, \
            f"world_step contains physics ({forbidden!r}) — the second " \
            f"loop is growing back"


# ── invariants 3+4: each subsystem once, cascade once ───────────────

def test_each_subsystem_runs_exactly_once_per_day(tiny_world, rng,
                                                  monkeypatch):
    """Count every subsystem entry during one canonical day."""
    import earth1.alive as alive_mod
    counts = {}

    def counting(mod, name):
        real = getattr(mod, name)
        def wrapper(*a, **k):
            counts[name] = counts.get(name, 0) + 1
            return real(*a, **k)
        monkeypatch.setattr(mod, name, wrapper)

    import earth1.contagion as contagion
    import earth1.feed as feed
    import earth1.flourishing as flourishing
    import earth1.health as health
    import earth1.influence as influence
    import earth1.institutions as institutions
    import earth1.knowledge as knowledge
    import earth1.life as life_mod
    import earth1.mobility as mobility
    import earth1.weather as weather

    counting(institutions, "govern")
    counting(institutions, "apply_policy_and_war")
    counting(institutions, "class_tick")
    counting(life_mod, "life_tick")
    counting(health, "health_tick")
    counting(knowledge, "knowledge_tick")
    counting(weather, "weather_tick")
    counting(flourishing, "flourishing_tick")
    # propagate/update_conviction are bound at alive.py's top-level
    # import, so they must be patched where they are USED
    counting(alive_mod, "propagate")
    counting(alive_mod, "update_conviction")
    counting(contagion, "contagion_tick")
    counting(mobility, "mobility_tick")
    counting(feed, "feed_tick")

    world_step(tiny_world, rng)          # via the wrapper, deliberately

    wrong = {k: v for k, v in counts.items() if v != 1}
    assert not wrong, f"subsystems not run exactly once: {wrong}"
    assert len(counts) == 13, f"subsystems missing: ran {sorted(counts)}"


def test_cascade_fires_at_most_once_per_day(tiny_world, rng, monkeypatch):
    """The cascade rule table is consulted exactly once per day — there
    is no second cascade implementation to consult it again."""
    import earth1.alive as alive_mod
    from earth1 import thresholds
    reads = []
    real = thresholds.TRANSITION_RULES

    class CountingRules:
        def __iter__(self):
            reads.append(1)
            return iter(real)

    monkeypatch.setattr(thresholds, "TRANSITION_RULES", CountingRules())
    live_one_day(tiny_world, rng)
    assert len(reads) == 1, \
        f"cascade rules consulted {len(reads)}x in one day"


def test_double_cascade_is_detectable(tiny_world, rng, monkeypatch):
    """Failing control: consult the rules twice, the counter must see 2."""
    from earth1 import thresholds
    reads = []
    real = thresholds.TRANSITION_RULES

    class CountingRules:
        def __iter__(self):
            reads.append(1)
            return iter(real)

    monkeypatch.setattr(thresholds, "TRANSITION_RULES", CountingRules())
    live_one_day(tiny_world, rng)
    for _ in thresholds.TRANSITION_RULES:        # the sabotage: a 2nd read
        break
    assert len(reads) == 2, "the cascade counter cannot fail"


def test_omitted_subsystem_is_detectable(tiny_world, monkeypatch):
    """Failing control: skip one live subsystem (weather) and the state
    comparison must diverge from the canonical day."""
    import earth1.weather as weather
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    live_one_day(a, np.random.default_rng(11))
    monkeypatch.setattr(weather, "weather_tick",
                        lambda *args, **kw: {})
    live_one_day(b, np.random.default_rng(11))
    assert persistence.world_hash(a) != persistence.world_hash(b), \
        "omitting a subsystem is invisible to the comparison"


def test_altered_rng_consumption_breaks_continuation(tiny_world):
    """Failing control: a wrapper that consumes one extra draw must
    diverge over multiple steps."""
    a = copy.deepcopy(tiny_world)
    b = copy.deepcopy(tiny_world)
    ra, rb = np.random.default_rng(21), np.random.default_rng(21)
    for _ in range(3):
        world_step(a, ra)
    for _ in range(3):
        rb.random()                       # the sabotage: one extra draw
        live_one_day(b, rb)
    assert persistence.world_hash(a) != persistence.world_hash(b)


# ── invariant 7: save→restore→continue stays exact through wrapper ──

def test_wrapper_persistence_continuation(tiny_world, tmp_path):
    a = copy.deepcopy(tiny_world)
    twin = copy.deepcopy(tiny_world)
    ra = np.random.default_rng(31)
    world_step(a, ra)
    persistence.save_world(a, tmp_path / "w.pkl", rng=ra)
    back, state, _ = persistence.load_world(tmp_path / "w.pkl")
    world_step(back, persistence.rng_from_state(state))

    rt = np.random.default_rng(31)
    live_one_day(twin, rt)
    live_one_day(twin, rt)
    assert persistence.world_hash(back) == persistence.world_hash(twin)
