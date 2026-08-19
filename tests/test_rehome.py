"""Phase 0.0d semantic invariants — the fabric follows the person.

No stale locality or workplace identity may survive a move or a job
change. Each required failing control from the acceptance contract is
implemented by deliberately breaking the mechanism and proving the
invariant catches it.
"""
import numpy as np
import pytest

from earth1 import persistence, rehome
from earth1.alive import live_one_day
from earth1.rehome import (EMPLOYMENT_POLICY, MIGRATION_POLICY,
                           assert_policy_complete, policy_gaps,
                           rehome_employment, rehome_migrants)


def _nbrs(mat, i):
    m = mat.tocsr()
    return set(m.indices[m.indptr[i]:m.indptr[i + 1]].tolist())


def _migrate_one(w, rng=None, dest_country=None):
    """Move one agent the way class_tick does, then re-home."""
    rng = rng or np.random.default_rng(4)
    mover = int(np.flatnonzero(w.health.alive)[7])
    old_country = int(w.civ.country[mover])
    dest = dest_country if dest_country is not None else \
        int((old_country + 40) % 194)
    w.civ.country[mover] = dest
    w.klass.migrated[mover] = True
    w.life.employed[mover] = False
    w.life.firm[mover] = -1
    rehome_migrants(w, np.array([mover]), rng)
    return mover, old_country, dest


# ── migration: canonical context updates ────────────────────────────

def test_region_and_urban_update_from_destination(tiny_world):
    w = tiny_world
    mover, old_c, dest = _migrate_one(w)
    residents = np.flatnonzero((w.civ.country == dest) & w.health.alive)
    residents = residents[residents != mover]
    assert w.civ.region[mover] in set(w.civ.region[residents].tolist()), \
        "region not adopted from a destination resident"


def test_locality_key_is_valid_at_destination(tiny_world):
    """The old defect: country changed, region/urban stale, so the key
    country*1000+region*2+urban pointed at a place that does not exist."""
    w = tiny_world
    mover, old_c, dest = _migrate_one(w)
    residents = np.flatnonzero((w.civ.country == dest) & w.health.alive)
    residents = residents[residents != mover]
    dest_locs = set(w.presence.locality[residents].tolist())
    assert int(w.presence.locality[mover]) in dest_locs, \
        "presence.locality is not a real destination place"


def test_invalid_locality_lookup_is_detectable(tiny_world):
    """Required failing control: reproduce the OLD behaviour (country
    changes, nothing else) and prove the validity check FAILS."""
    w = tiny_world
    mover = int(np.flatnonzero(w.health.alive)[7])
    old_loc = int(w.presence.locality[mover])
    dest = int((w.civ.country[mover] + 40) % 194)
    w.civ.country[mover] = dest                # the pre-0.0d 'migration'
    residents = np.flatnonzero((w.civ.country == dest) & w.health.alive)
    residents = residents[residents != mover]
    dest_locs = set(w.presence.locality[residents].tolist())
    assert old_loc not in dest_locs, \
        "control cannot fail: source and dest share a locality index"


# ── migration: tie policies ─────────────────────────────────────────

def test_old_neighbour_ties_removed_and_rebuilt(tiny_world):
    w = tiny_world
    mover = int(np.flatnonzero(w.health.alive)[7])
    old_n = _nbrs(w.fabric.by_type["neighbours"], mover)
    _, old_c, dest = _migrate_one(w)
    new_n = _nbrs(w.fabric.by_type["neighbours"], mover)
    assert not (new_n & old_n), "old-locality neighbours survived the move"
    if new_n:
        c = w.civ.country[list(new_n)]
        assert (c == dest).all(), "rebuilt neighbours are not at destination"


def test_preserved_old_neighbour_tie_fails(tiny_world, monkeypatch):
    """Required failing control: sabotage removal, invariant must fire."""
    w = tiny_world
    mover = int(np.flatnonzero(w.health.alive)[7])
    old_n = _nbrs(w.fabric.by_type["neighbours"], mover)
    assert old_n, "mover needs neighbours for this control"
    monkeypatch.setattr(rehome, "_zero_rows_cols", lambda m, s: m.tocsr())
    _migrate_one(w)
    leaked = _nbrs(w.fabric.by_type["neighbours"], mover) & old_n
    assert leaked, "sabotage did not leak — the invariant test is vacuous"


def test_household_and_friends_become_diaspora(tiny_world):
    """Co-residence ends; kinship survives as the fabric's own
    migration-corridor semantic. You keep your people."""
    w = tiny_world
    mover = int(np.flatnonzero(w.health.alive)[7])
    old_hh = _nbrs(w.fabric.by_type["household"], mover)
    old_fr = _nbrs(w.fabric.by_type["friends"], mover)
    kin = (old_hh | old_fr) & set(np.flatnonzero(w.health.alive).tolist())
    _migrate_one(w)
    assert not _nbrs(w.fabric.by_type["household"], mover), \
        "co-residence survived migration"
    assert not _nbrs(w.fabric.by_type["friends"], mover), \
        "same-locality friendship rows survived"
    dias = _nbrs(w.fabric.by_type["diaspora"], mover)
    assert kin <= dias, "kinship was lost instead of becoming diaspora"


def test_no_reverse_references_locate_mover_in_old_community(tiny_world):
    w = tiny_world
    mover = int(np.flatnonzero(w.health.alive)[7])
    old_n = _nbrs(w.fabric.by_type["neighbours"], mover)
    old_w = _nbrs(w.fabric.by_type["weak"], mover)
    _migrate_one(w)
    for o in old_n:
        assert mover not in _nbrs(w.fabric.by_type["neighbours"], o), \
            f"agent {o} still lists the mover as a neighbour"
    for o in old_w:
        assert mover not in _nbrs(w.fabric.by_type["weak"], o)


def test_migration_policy_completeness_gate(tiny_world, monkeypatch):
    """Required failing control: omit one category -> CI fails."""
    assert_policy_complete(tiny_world.fabric)
    trimmed = {k: v for k, v in MIGRATION_POLICY.items()
               if k != "neighbours"}
    monkeypatch.setattr(rehome, "MIGRATION_POLICY", trimmed)
    with pytest.raises(ValueError, match="no re-homing policy"):
        assert_policy_complete(tiny_world.fabric)


# ── employment ──────────────────────────────────────────────────────

def _employ(w, i, firm):
    w.life.employed[i] = True
    w.life.firm[i] = firm


def test_colleague_ties_follow_the_job(tiny_world, rng):
    w = tiny_world
    i = int(np.flatnonzero(w.health.alive)[9])
    old_c = _nbrs(w.fabric.by_type["colleagues"], i)
    # lose the job
    w.life.employed[i] = False
    w.life.firm[i] = -1
    rehome_employment(w, np.array([i]), np.array([], dtype=int), rng)
    assert not _nbrs(w.fabric.by_type["colleagues"], i), \
        "unemployment kept a phantom workplace"
    # new firm, new colleagues — never the old ones
    firms = np.unique(w.life.firm[w.life.employed & w.health.alive])
    firms = firms[firms >= 0]
    new_firm = int(firms[3])
    _employ(w, i, new_firm)
    rehome_employment(w, np.array([], dtype=int), np.array([i]), rng)
    new_c = _nbrs(w.fabric.by_type["colleagues"], i)
    coworkers = set(np.flatnonzero((w.life.firm == new_firm)
                                   & w.life.employed).tolist()) - {i}
    assert new_c <= coworkers | set(), \
        "rebuilt colleague ties are not actual coworkers"
    assert not (new_c & old_c - coworkers), \
        "previous-firm colleague state resurrected"
    for j in new_c:
        assert i in _nbrs(w.fabric.by_type["colleagues"], j), \
            "one-sided colleague tie"


def test_stale_colleague_matrix_fails(tiny_world, monkeypatch, rng):
    """Required failing control: leave the old colleague matrix."""
    w = tiny_world
    # pick an agent that actually has colleagues (employed at genesis)
    m = w.fabric.by_type["colleagues"].tocsr()
    deg = np.diff(m.indptr)
    i = int(np.flatnonzero((deg > 0) & w.health.alive)[0])
    old_c = _nbrs(w.fabric.by_type["colleagues"], i)
    assert old_c, "agent needs colleagues for this control"
    monkeypatch.setattr(rehome, "_zero_rows_cols", lambda m, s: m.tocsr())
    w.life.employed[i] = False
    w.life.firm[i] = -1
    rehome_employment(w, np.array([i]), np.array([], dtype=int), rng)
    assert _nbrs(w.fabric.by_type["colleagues"], i) & old_c, \
        "sabotage did not leak — invariant test is vacuous"


def test_one_sided_relationship_fails_mutuality(tiny_world):
    """Required failing control: create an asymmetric edge, prove the
    mutuality check detects it."""
    w = tiny_world
    from scipy import sparse
    i, j = 3, 900
    m = w.fabric.by_type["colleagues"].tolil()
    m[i, j] = 0.6                              # one direction only
    w.fabric.by_type["colleagues"] = m.tocsr()
    assert j in _nbrs(w.fabric.by_type["colleagues"], i)
    assert i not in _nbrs(w.fabric.by_type["colleagues"], j), \
        "control cannot fail: edge became mutual on its own"


def test_add_mutual_never_creates_one_sided_or_doubled(tiny_world):
    w = tiny_world
    m0 = w.fabric.by_type["colleagues"]
    m1 = rehome._add_mutual(m0, np.array([5]), np.array([800]), 0.6,
                            w.civ.n)
    assert 800 in _nbrs(m1, 5) and 5 in _nbrs(m1, 800)
    # re-adding the same edge must not double the weight
    m2 = rehome._add_mutual(m1, np.array([5]), np.array([800]), 0.6,
                            w.civ.n)
    assert float(m2[5, 800]) == pytest.approx(0.6)


# ── persistence and live evolution ──────────────────────────────────

def test_rehomed_state_survives_roundtrip(tiny_world, tmp_path, rng):
    w = tiny_world
    _migrate_one(w)
    i = int(np.flatnonzero(w.health.alive)[9])
    w.life.employed[i] = False
    w.life.firm[i] = -1
    rehome_employment(w, np.array([i]), np.array([], dtype=int), rng)
    h = persistence.world_hash(w)
    persistence.save_world(w, tmp_path / "w.pkl")
    back, _, info = persistence.load_world(tmp_path / "w.pkl")
    assert info["lost"] == []
    assert persistence.world_hash(back) == h


def test_live_ticks_do_not_reconstruct_stale_context(tiny_world, rng):
    """No downstream module may quietly rebuild old-region or old-firm
    ties after several days of live evolution."""
    w = tiny_world
    mover, old_c, dest = _migrate_one(w)
    old_n = _nbrs(w.fabric.by_type["neighbours"], mover)
    for _ in range(5):
        live_one_day(w, rng)
    assert int(w.civ.country[mover]) == dest or not w.health.alive[mover]
    if w.health.alive[mover] and not w.klass.migrated[mover] is False:
        n_now = _nbrs(w.fabric.by_type["neighbours"], mover)
        stale = {x for x in n_now
                 if w.health.alive[x] and int(w.civ.country[x]) == old_c}
        assert not stale, "old-country neighbour ties reconstructed"
        col = _nbrs(w.fabric.by_type["colleagues"], mover)
        if not w.life.employed[mover]:
            assert not col, "phantom workplace grew back"
    assert np.isfinite(w.civ.forces).all()


def test_full_tick_path_rehomes_migrants(tiny_world, rng):
    """Drive migration through live_one_day itself (class_tick -> alive
    wiring -> rehome) rather than calling rehome directly."""
    w = tiny_world
    w.life.deprivation[:] = 0.95         # everyone wants to leave
    w.civ.age[:] = 0.2
    moved_any = False
    for _ in range(30):
        st = live_one_day(w, rng)
        if st.get("rehomed_migrants", 0) > 0:
            moved_any = True
            break
    assert moved_any, "no migration fired through the live path in 30 days"
    m = np.flatnonzero(w.klass.migrated & w.health.alive)
    assert m.size
    i = int(m[0])
    residents = np.flatnonzero((w.civ.country == w.civ.country[i])
                               & w.health.alive)
    residents = residents[residents != i]
    assert int(w.presence.locality[i]) in \
        set(w.presence.locality[residents].tolist())


def test_employed_migrant_loses_colleague_ties_via_live_path(tiny_world,
                                                             rng):
    """PRODUCTION MISS, first 0.0d window: 179 of 180 phantom
    workplaces were employed migrants. class_tick ends the job AFTER
    life_tick built its lost set, so migrants never reached the
    employment severing. The live path must sever their colleague ties
    in the same tick as the move."""
    w = tiny_world
    w.life.deprivation[:] = 0.95
    w.civ.age[:] = 0.2
    for _ in range(40):
        st = live_one_day(w, rng)
        if st.get("rehomed_migrants", 0) > 0:
            break
    else:
        pytest.fail("no migration fired in 40 days")
    col = w.fabric.by_type["colleagues"].tocsr()
    movers = np.flatnonzero(w.klass.migrated & w.health.alive
                            & ~w.life.employed)
    assert movers.size
    for i in movers:
        assert not _nbrs(col, int(i)),             f"migrant {i} kept a phantom workplace through the live path"
