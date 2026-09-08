"""APPARATUS CYCLE 1 — regression pins for the graph/branching findings
of the external review (verified 2026-09-08): M04 paired branching,
M05a local _add_mutual clamp, M05b chronicle CSC-cache provenance and
the cascade_residues declaration, M05c empty-graph partner sampling.

Each test reproduces the reviewer's probe (evidence bundle
review_probes.py / verify_m04_m05.py) and asserts the FIXED behaviour.
"""
import copy
import dataclasses
import os
import sys
from types import SimpleNamespace

import numpy as np
from scipy import sparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# ── M05a: _add_mutual clamps only the added delta ───────────────────
#
# The repair is flag-gated DEFAULT OFF (EARTH1_REHOME_LOCAL_CLAMP=1):
# implementing it uncovered that the finding is LIVE, not latent —
# plasticity grows friends/weak weights past the nominal tie weight
# daily, so the old global clamp mass-rewrites the weak matrix on every
# migration day, and fixing that CHANGES the frozen-0.9 trajectory.
# Flipping the flag is a physics decision (v1.1 tier, with M01a).

def test_add_mutual_leaves_unrelated_edges_alone(monkeypatch):
    """Reviewer probe: a 0.9 edge elsewhere in the matrix survives
    adding an unrelated 0.4 edge (it used to be clamped to 0.4)."""
    monkeypatch.setenv("EARTH1_REHOME_LOCAL_CLAMP", "1")
    from earth1.rehome import _add_mutual
    mat = sparse.csr_matrix(([.9, .9], ([0, 1], [1, 0])), shape=(4, 4))
    got = _add_mutual(mat, np.array([2]), np.array([3]), 0.4, 4)
    assert got[0, 1] == 0.9 and got[1, 0] == 0.9
    assert got[2, 3] == 0.4 and got[3, 2] == 0.4


def test_add_mutual_still_clamps_readded_edges(monkeypatch):
    """The clamp's original purpose is intact: re-adding an existing
    edge must not double it — at the delta's own coordinates only."""
    monkeypatch.setenv("EARTH1_REHOME_LOCAL_CLAMP", "1")
    from earth1.rehome import _add_mutual
    mat = sparse.csr_matrix(([.9, .9, .4, .4],
                             ([0, 1, 2, 3], [1, 0, 3, 2])), shape=(4, 4))
    got = _add_mutual(mat, np.array([2]), np.array([3]), 0.4, 4)
    assert got[2, 3] == 0.4 and got[3, 2] == 0.4      # not 0.8
    assert got[0, 1] == 0.9                            # untouched


def test_add_mutual_default_keeps_the_frozen_global_clamp(monkeypatch):
    """Documents the FROZEN artifact, the way test_branch_pairing pins
    the desynced baseline: without the flag, freeze-0.9 keeps the
    whole-matrix clamp bit-for-bit. If this ever changes silently, the
    frozen trajectory changed without a founder ruling."""
    monkeypatch.delenv("EARTH1_REHOME_LOCAL_CLAMP", raising=False)
    from earth1.rehome import _add_mutual
    mat = sparse.csr_matrix(([.9, .9], ([0, 1], [1, 0])), shape=(4, 4))
    got = _add_mutual(mat, np.array([2]), np.array([3]), 0.4, 4)
    assert got[0, 1] == 0.4                # the M05a defect, frozen


def test_add_mutual_flag_on_matches_old_clamp_on_single_weights(monkeypatch):
    """Where a matrix IS single-weight (the non-plastic types:
    diaspora/neighbours/colleagues) the local clamp is bitwise
    identical to the frozen whole-matrix clamp."""
    monkeypatch.setenv("EARTH1_REHOME_LOCAL_CLAMP", "1")
    from earth1.rehome import _add_mutual
    rng = np.random.default_rng(0)
    r0 = rng.integers(0, 50, 150)
    c0 = rng.integers(0, 50, 150)
    keep = r0 != c0
    m = sparse.csr_matrix((np.full(int(keep.sum()), .4),
                           (r0[keep], c0[keep])), shape=(50, 50))
    m = m.maximum(m.T).tocsr()                # symmetric, all .4
    rows = np.array([1, 7, 7], dtype=np.int64)
    cols = np.array([2, 9, 30], dtype=np.int64)

    # the pre-M05a algorithm, verbatim
    rr = np.concatenate([rows, cols])
    cc = np.concatenate([cols, rows])
    delta = sparse.csr_matrix(
        (np.full(rr.size, .4, dtype=m.dtype), (rr, cc)), shape=(50, 50))
    old = (m + delta).tocsr()
    np.minimum(old.data, .4, out=old.data)
    old.sum_duplicates()

    new = _add_mutual(m, rows, cols, .4, 50)
    assert (new != old).nnz == 0
    assert np.array_equal(new.data, old.data)


# ── M05b: indexed chronicle spread must see graph mutation ──────────

class _ZeroRng:
    """random() -> 0 everywhere: any positive exposure is caught, so
    the spread is deterministic and the two code paths comparable."""

    def random(self, n):
        return np.zeros(n)


def test_chronicle_indexed_spread_sees_graph_mutation(monkeypatch):
    """Reviewer probe: prime the CSC cache, add edge 0-2 by REBINDING
    civ.adj (what rehome._recompose_adj does), spread again. The
    indexed path used to keep spreading on last rebuild's graph."""
    from earth1.memory import Chronicle, Memory
    old = sparse.csr_matrix(([1., 1.], ([0, 1], [1, 0])), shape=(3, 3))
    new = sparse.csr_matrix(([1., 1., 1., 1.],
                             ([0, 1, 0, 2], [1, 0, 2, 0])), shape=(3, 3))
    civ = SimpleNamespace(n=3, adj=old)
    c = Chronicle(events=[Memory("m", "m", 0., np.zeros(8),
                                 np.array([True, False, False]))])
    monkeypatch.setenv("EARTH1_CHRONICLE_INDEX", "v1")
    c.spread(civ, _ZeroRng(), rate=0.)   # primes the cache on old adj
    civ.adj = new                        # edge 0-2 added; cache stale
    ref_c = copy.deepcopy(c)
    ref_civ = copy.deepcopy(civ)
    c.spread(civ, _ZeroRng(), rate=1.)
    monkeypatch.setenv("EARTH1_CHRONICLE_INDEX", "off")
    ref_c.spread(ref_civ, _ZeroRng(), rate=1.)   # reference: batched path
    assert c.events[0].scope.tolist() == [True, True, True]
    assert np.array_equal(c.events[0].scope, ref_c.events[0].scope)
    # provenance is recorded beside the rebuilt cache
    assert civ._adj_csc_src is civ.adj


def test_cascade_residues_is_a_declared_chronicle_field():
    """M05b companion (state-identity request): the residue store is a
    declared field with the None sentinel alive.py keys on — no longer
    an invisible instance attribute."""
    from earth1.memory import Chronicle
    names = {f.name for f in dataclasses.fields(Chronicle)}
    assert "cascade_residues" in names
    assert Chronicle().cascade_residues is None


# ── M05c: partner sampling on an empty graph ────────────────────────

def test_sample_partners_empty_graph_returns_absent():
    """Reviewer probe: IndexError on a zero-nnz graph. Now: every
    partner absent, nothing raised."""
    from earth1.influence import sample_partners
    partner, has = sample_partners(sparse.csr_matrix((3, 3)),
                                   np.random.default_rng(1))
    assert partner.tolist() == [-1, -1, -1]
    assert not has.any()


def test_sample_partners_empty_graph_consumes_the_same_draws():
    """The early return sits AFTER the rng.random(n) draw: stream
    consumption is graph-independent, so paired arms stay aligned."""
    from earth1.influence import sample_partners
    r1, r2 = np.random.default_rng(9), np.random.default_rng(9)
    sample_partners(sparse.csr_matrix((5, 5)), r1)
    r2.random(5)
    assert r1.random() == r2.random()


def test_sample_partners_nonempty_path_untouched():
    from earth1.influence import sample_partners
    m = sparse.csr_matrix(([1., 1.], ([0, 1], [1, 0])), shape=(3, 3))
    partner, has = sample_partners(m, np.random.default_rng(3))
    assert partner[0] == 1 and partner[1] == 0 and partner[2] == -1
    assert has.tolist() == [True, True, False]


def test_propagate_on_empty_graph_is_identity():
    """Through the caller: a day of dyadic influence on an edgeless
    world moves nobody and raises nothing."""
    from earth1.influence import new_day_scratch, propagate
    f = np.random.default_rng(0).random((4, 8))
    out = propagate(f, np.full(4, .5), sparse.csr_matrix((4, 4)),
                    day=3, scratch=new_day_scratch(4))
    assert np.array_equal(out, f)


# ── M04: public branch.run pairs its control arm ────────────────────

def test_null_branch_run_reports_zero_effect(tiny_world):
    """Reviewer probe: a zero-impact scenario through the public run()
    reported 5 jobs lost, 3 gained, savings moved — pure rng-desync.
    With the null-matched control both arms are bit-identical."""
    from earth1 import branch
    rep = branch.run(tiny_world, [branch.null_branch()],
                     days=7, repeats=1, seed=42)
    f = rep["branches"]["__null__"]["consequences"]
    assert f["jobs_lost"] == 0
    assert f["jobs_gained_elsewhere"] == 0
    assert f["jobs_lost_cumulative"] == 0
    assert f["jobs_lost_peak"] == 0
    assert f["hope_change"] == 0.0
    assert f["savings_change_days"] == 0.0
    assert float(np.abs(np.array(f["jobs_by_country_vector"])).sum()) == 0.0
    assert f["people_pushed_into_destitution"] == 0
    assert f["excess_deaths"] == 0
    assert f["displaced"] == 0
    assert f["world_hash_treatment"] == f["world_hash_control"]


def test_null_branch_run_matches_control_per_persists_days(tiny_world):
    """The control must carry the TREATMENT's persists_days: a 1-day
    null memory leaves the world at day ~6 and stops consuming draws,
    so an unmatched 365-day control desyncs from day 7 on. Two null
    scenarios with different persists must EACH pair exactly."""
    from earth1 import branch
    short = branch.null_branch(persists_days=1.0)
    short.id = "__null_short__"
    long = branch.null_branch(persists_days=365.0)
    rep = branch.run(tiny_world, [short, long],
                     days=8, repeats=1, seed=7)
    for key in ("__null_short__", "__null__"):
        f = rep["branches"][key]["consequences"]
        assert f["jobs_lost"] == 0, key
        assert f["jobs_lost_cumulative"] == 0, key
        assert f["world_hash_treatment"] == f["world_hash_control"], key
