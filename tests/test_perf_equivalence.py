"""0.7 — performance work is only admissible under the equivalence
rule: same state + same seeds + same inputs ⇒ same outputs. The 0.7
optimizations (single rehome recompose, one-pass adj composition,
CSR membership test in rewiring) claim BIT identity, so these tests
demand it — not tolerance.
"""
import copy

import numpy as np
import pytest

from earth1 import persistence, rehome
from earth1.alive import birth_world, live_one_day


def _chained_reference_recompose(w):
    """The pre-0.7 composition: chained csr_plus_csr in by_type order.
    Kept here as the reference the fast path must match bit-for-bit."""
    fab = w.fabric
    total = None
    for m in fab.by_type.values():
        total = m if total is None else total + m
    adj = total.tocsr()
    adj.setdiag(0.0)
    adj.eliminate_zeros()
    return adj


@pytest.fixture(scope="module")
def lived_world():
    w = birth_world(4000, 7)
    r = np.random.default_rng(42)
    for _ in range(3):
        live_one_day(w, r)
    return w


def test_recompose_is_bit_identical_to_chained_adds(lived_world):
    w = copy.deepcopy(lived_world)
    ref = _chained_reference_recompose(w)
    rehome._recompose_adj(w)
    got = w.fabric.adj
    assert np.array_equal(got.indptr, ref.indptr)
    assert np.array_equal(got.indices, ref.indices)
    assert np.array_equal(got.data, ref.data), \
        "recompose drifted from the chained-add reference (ULP order?)"


def test_recompose_sums_duplicates_left_to_right():
    """The control that caught two real bugs: scipy's own dedup AND
    np.add.reduceat both sum in a different association and drift by
    ULPs. Values chosen so every wrong order differs."""
    from scipy import sparse
    a = sparse.csr_matrix((np.array([1.0]), (np.array([0]),
                          np.array([1]))), shape=(3, 3))
    b = sparse.csr_matrix((np.array([0.6]), (np.array([0]),
                          np.array([1]))), shape=(3, 3))
    c = sparse.csr_matrix((np.array([0.8]), (np.array([0]),
                          np.array([1]))), shape=(3, 3))

    class FakeFab:
        pass

    class FakeCiv:
        pass

    class FakeW:
        pass

    w = FakeW()
    w.fabric = FakeFab()
    w.fabric.by_type = {"t1": a, "t2": b, "t3": c}
    w.civ = FakeCiv()
    rehome._recompose_adj(w)
    got = w.fabric.adj[0, 1]
    assert got == (1.0 + 0.6) + 0.8         # 2.4000000000000004
    assert got != 1.0 + (0.6 + 0.8)         # 2.4 — the reduceat drift


def test_trajectory_hash_unchanged_by_optimizations():
    """15 canonical days from a fixed seed land on the exact
    world_hash the pre-0.7 code produced (recorded 2026-08-20 from
    the pristine tree at c6af56b). Runs in a fresh interpreter: other
    suites mutate module state in-process, which changes the
    trajectory and would make this pin order-dependent."""
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "import numpy as np\n"
        "from earth1.alive import birth_world, live_one_day\n"
        "from earth1 import persistence\n"
        "w = birth_world(4000, 7)\n"
        "r = np.random.default_rng(42)\n"
        "[live_one_day(w, r) for _ in range(15)]\n"
        "print(persistence.world_hash(w))\n" % str(root))
    import os
    clean_env = {k: v for k, v in os.environ.items()
                 if not k.startswith("EARTH1_")}
    p = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, cwd=root,
                       env=clean_env)
    assert p.returncode == 0, p.stderr[-500:]
    # PINNED TRAJECTORY of the CANONICAL physics (Phase 0.5, candidate
    # 76a574c canonicalized at 42b61c3). The previous pin
    # (7a55444a…55f06) was the incumbent physics; it is superseded by
    # the accepted physics, not by an optimization — any future change
    # to this value without a physics ruling is a regression.
    assert p.stdout.strip() == (
        "6b289fb1f0b578b753278b356e73a04a"
        "3594905d620eded15cad5f46a9eb929a")
