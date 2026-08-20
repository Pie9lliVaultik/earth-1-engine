"""RE-HOMING — the fabric follows the person. Phase 0.0d.

A change in an Earthling's physical or social context must update every
fabric relation whose semantics depend on that context. Before this
module, migration changed `civ.country` and nothing else: `region` and
`urban` kept the OLD country's values (so the locality key
`country*1000 + region*2 + urban` became an invalid address), the
comment said "arriving costs you your ties" while no tie changed, and
colleague ties stayed frozen at the day-0 firm assignment forever —
through every job change in the world's history.

THE CONTRACT. Every tie type in the fabric carries a declared policy
for each context event. CI fails if a fabric tie type has no policy
(tests/test_rehome.py) — the 0.0b pattern, applied to relations.

  MIGRATION
    neighbours   REMOVE + REBUILD   locality-keyed; old ones are gone,
                                    new ones drawn at the destination
    weak         REMOVE + REBUILD   country-keyed acquaintances
    colleagues   (via employment)   migration ends the job; the
                                    employment path removes the ties
    household    CONVERT->diaspora  co-residence ends; kinship becomes
                                    a migration-corridor tie — the
                                    fabric's own diaspora semantic,
                                    "you keep your people" (weight 0.55)
    friends      CONVERT->diaspora  friends back home persist as
                                    long-distance ties
    diaspora     KEEP               that is what it is for
    media        KEEP               global hubs are location-free

  EMPLOYMENT
    colleagues   REMOVE on loss; REBUILD from the new firm's actual
                 coworkers on hire. Unemployment holds no phantom
                 workplace; re-employment cannot resurrect a previous
                 firm's ties because they were removed at loss.
    (all other types unaffected by job change)

Presence follows the body: a migrant's locality/density are adopted
from a sampled living resident of the destination — the key is valid
by construction because a real resident carries it. `region` and
`urban` update from the same resident.

Costs, measured thinking: ~100-300 migrations and ~5k job changes per
day at 4M. All edits are batched into one pass per tick; adj is
recomposed from the typed matrices (O(nnz) ≈ 80M, ~1s) rather than
delta-tracked, which trades a predictable second for a class of
bookkeeping bugs. Firm and country member lookups use one argsort
index per tick, not per-agent scans.
"""
from __future__ import annotations

import numpy as np

KEEP = "KEEP"
REMOVE = "REMOVE"
REMOVE_REBUILD = "REMOVE_REBUILD"
CONVERT_DIASPORA = "CONVERT_DIASPORA"
VIA_EMPLOYMENT = "VIA_EMPLOYMENT"

DIASPORA_W = 0.55        # TIE_SPEC diaspora weight
NEIGHBOUR_W, NEIGHBOUR_K = 0.40, 5
WEAK_W, WEAK_K = 0.15, 2
COLLEAGUE_W, COLLEAGUE_K = 0.60, 6

MIGRATION_POLICY = {
    "household": CONVERT_DIASPORA,
    "colleagues": VIA_EMPLOYMENT,
    "neighbours": REMOVE_REBUILD,
    "friends": CONVERT_DIASPORA,
    "weak": REMOVE_REBUILD,
    "diaspora": KEEP,
    "media": KEEP,
}
EMPLOYMENT_POLICY = {
    "household": KEEP,
    "colleagues": REMOVE_REBUILD,
    "neighbours": KEEP,
    "friends": KEEP,
    "weak": KEEP,
    "diaspora": KEEP,
    "media": KEEP,
}


def policy_gaps(fab):
    """Fabric tie types with no declared re-homing policy, per event."""
    types = set(fab.by_type)
    return {"migration": sorted(types - set(MIGRATION_POLICY)),
            "employment": sorted(types - set(EMPLOYMENT_POLICY)),
            "stale": sorted((set(MIGRATION_POLICY)
                             | set(EMPLOYMENT_POLICY)) - types)}


def assert_policy_complete(fab):
    gaps = policy_gaps(fab)
    if gaps["migration"] or gaps["employment"]:
        raise ValueError(
            f"fabric tie types with no re-homing policy: "
            f"migration={gaps['migration']} employment={gaps['employment']}"
            f" — a context change would leave them semantically stale")
    if gaps["stale"]:
        raise ValueError(f"re-homing policy names unknown tie types: "
                         f"{gaps['stale']}")


# ── sparse helpers (shared semantics with rebirth) ──────────────────

def _rows_of(mat, slots):
    """(rows, cols, data) triples of every edge touching `slots`."""
    m = mat.tocsr()
    rr, cc = [], []
    for i in slots:
        js = m.indices[m.indptr[i]:m.indptr[i + 1]]
        rr.extend([i] * js.size)
        cc.extend(js.tolist())
    return np.array(rr, dtype=np.int64), np.array(cc, dtype=np.int64)


def _zero_rows_cols(mat, slots):
    m = mat.tocsr()
    for i in slots:
        m.data[m.indptr[i]:m.indptr[i + 1]] = 0.0
    mask = np.isin(m.indices, slots)
    if mask.any():
        m.data[mask] = 0.0
    m.eliminate_zeros()
    return m


def _add_mutual(mat, rows, cols, weight, n):
    """Add mutual edges through one canonical path — always symmetric."""
    from scipy import sparse
    if len(rows) == 0:
        return mat.tocsr()
    r = np.concatenate([rows, cols])
    c = np.concatenate([cols, rows])
    delta = sparse.csr_matrix((np.full(r.size, weight), (r, c)),
                              shape=(n, n))
    out = (mat + delta).tocsr()
    # duplicate coordinates sum on addition; clamp to the tie weight so
    # a re-added edge can never silently double
    np.minimum(out.data, weight, out=out.data)
    return out


def _member_index(keys):
    """argsort-based group index: value -> slice of member ids."""
    order = np.argsort(keys, kind="stable")
    sorted_keys = keys[order]
    starts = np.searchsorted(sorted_keys, np.unique(sorted_keys))
    return order, sorted_keys


def _sample_members(keys, order, sorted_keys, value, k, rng, exclude):
    lo = np.searchsorted(sorted_keys, value, side="left")
    hi = np.searchsorted(sorted_keys, value, side="right")
    pool = order[lo:hi]
    pool = pool[pool != exclude]
    if pool.size == 0:
        return pool
    take = min(k, pool.size)
    return rng.choice(pool, size=take, replace=False)


# ── migration ───────────────────────────────────────────────────────

def rehome_migrants(w, idx, rng, recompose=True):
    """Execute MIGRATION_POLICY for movers `idx` (country already set
    by class_tick; everything context-dependent is updated here)."""
    if idx is None or len(idx) == 0:
        return 0
    from scipy import sparse
    assert_policy_complete(w.fabric)
    civ, fab = w.civ, w.fabric
    idx = np.asarray(idx)
    n = civ.n

    # destination context from a sampled LIVING resident of the new
    # country — region, urban, locality and density are then valid by
    # construction (a real resident carries a real key)
    alive = w.health.alive
    order = np.argsort(civ.country, kind="stable")
    sk = civ.country[order]
    for i in idx:
        lo = np.searchsorted(sk, civ.country[i], "left")
        hi = np.searchsorted(sk, civ.country[i], "right")
        pool = order[lo:hi]
        pool = pool[alive[pool] & (pool != i)]
        if pool.size:
            host = int(pool[rng.integers(pool.size)])
            civ.region[i] = civ.region[host]
            civ.urban[i] = civ.urban[host]
            if w.presence is not None:
                w.presence.locality[i] = w.presence.locality[host]
                w.presence.density[i] = w.presence.density[host]
        if w.presence is not None:
            w.presence.gathering[i] = -1

    # CONVERT household + friends -> diaspora (you keep your people)
    conv_r, conv_c = [], []
    for name in ("household", "friends"):
        rr, cc = _rows_of(fab.by_type[name], idx)
        conv_r.extend(rr.tolist())
        conv_c.extend(cc.tolist())
        fab.by_type[name] = _zero_rows_cols(fab.by_type[name], idx)
    if conv_r:
        keep = w.health.alive[np.array(conv_c)]
        conv_r = np.array(conv_r)[keep]
        conv_c = np.array(conv_c)[keep]
        fab.by_type["diaspora"] = _add_mutual(
            fab.by_type["diaspora"], conv_r, conv_c, DIASPORA_W, n)

    # the migrant founds a new one-person household at the destination
    fab.household[idx] = np.arange(idx.size) + int(fab.household.max()) + 1

    # REMOVE + REBUILD locality/country-keyed ties at the destination
    for name, (weight, k) in (("neighbours", (NEIGHBOUR_W, NEIGHBOUR_K)),
                              ("weak", (WEAK_W, WEAK_K))):
        fab.by_type[name] = _zero_rows_cols(fab.by_type[name], idx)
        if name == "neighbours" and w.presence is not None:
            keys = w.presence.locality.astype(np.int64)
        else:
            keys = civ.country.astype(np.int64)
        o = np.argsort(keys, kind="stable")
        skk = keys[o]
        rows, cols = [], []
        for i in idx:
            got = _sample_members(keys, o, skk, keys[i], k, rng, i)
            got = got[w.health.alive[got]]
            rows.extend([i] * got.size)
            cols.extend(got.tolist())
        fab.by_type[name] = _add_mutual(
            fab.by_type[name], np.array(rows, dtype=np.int64),
            np.array(cols, dtype=np.int64), weight, n)

    # 0.7: the daily loop recomposes once after rehome_employment, which
    # always follows this call with no adj reader in between
    if recompose:
        _recompose_adj(w)
    return int(idx.size)


# ── employment ──────────────────────────────────────────────────────

def rehome_employment(w, lost_idx, found_idx, rng):
    """Execute EMPLOYMENT_POLICY: sever colleague ties on loss, build
    them from the new firm's actual coworkers on hire."""
    lost_idx = np.asarray(lost_idx) if lost_idx is not None else np.array([], dtype=int)
    found_idx = np.asarray(found_idx) if found_idx is not None else np.array([], dtype=int)
    if lost_idx.size == 0 and found_idx.size == 0:
        return 0
    assert_policy_complete(w.fabric)
    civ, life, fab = w.civ, w.life, w.fabric
    n = civ.n

    movers = np.unique(np.concatenate([lost_idx, found_idx]))
    fab.by_type["colleagues"] = _zero_rows_cols(
        fab.by_type["colleagues"], movers)

    if found_idx.size:
        firm_keys = np.where(life.employed, life.firm, -1 - np.arange(n))
        o = np.argsort(firm_keys, kind="stable")
        sk = firm_keys[o]
        rows, cols = [], []
        for i in found_idx:
            got = _sample_members(firm_keys, o, sk, firm_keys[i],
                                  COLLEAGUE_K, rng, i)
            got = got[w.health.alive[got]]
            rows.extend([i] * got.size)
            cols.extend(got.tolist())
        fab.by_type["colleagues"] = _add_mutual(
            fab.by_type["colleagues"], np.array(rows, dtype=np.int64),
            np.array(cols, dtype=np.int64), COLLEAGUE_W, n)

    _recompose_adj(w)
    return int(movers.size)


def _recompose_adj(w):
    """adj = sum of the typed matrices — one canonical composition,
    no delta bookkeeping to drift. Keeps the alive.py:64 alias true.

    (0.7 note: a one-pass COO-concat + lexsort rebuild was tried and
    proven bit-identical — but SLOWER at 4M (global sort of ~60M
    triplets loses to the pairwise sorted merges csr_plus_csr does).
    The chain stays; the daily loop calls it one time fewer instead.)"""
    fab = w.fabric
    total = None
    for m in fab.by_type.values():
        total = m if total is None else total + m
    fab.adj = total.tocsr()
    # 0.7: setdiag(0.0) on a diagonal-free CSR INSERTS 4M explicit
    # zeros (a full structure rebuild) that eliminate_zeros then strips
    # back out — ~10% of a world-day spent on a semantic no-op. No tie
    # type carries self-loops, so the guard almost never fires; when it
    # does, the old path runs unchanged. Bit-identical either way:
    # values untouched, and eliminate_zeros only runs when there is an
    # explicit zero to remove.
    if np.count_nonzero(fab.adj.diagonal()):
        fab.adj.setdiag(0.0)
    if not np.all(fab.adj.data):
        fab.adj.eliminate_zeros()
    w.civ.adj = fab.adj
