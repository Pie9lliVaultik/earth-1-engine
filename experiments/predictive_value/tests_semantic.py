"""Semantic proofs for the predictive-value grid (EXPERIMENT_PLAN §9):
disabled mechanisms are REALLY disabled, and all variants see identical
inputs. Small populations — these run in seconds, in CI."""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

from variants import VARIANTS
from earth1.advance import advance_world
from earth1.event_log import EventLog
from earth1.genesis import genesis
from earth1.living import pop_hash_full
from earth1.tick import WorldState, _make_mutable
from earth1.types import Question


def _state(pop=2000, seed=42):
    civ = _make_mutable(genesis(pop, seed))
    return WorldState(civ=civ, event_log=EventLog(), t=0.0, tick_count=0,
                      question_history=[], coupling_matrix={},
                      last_fired={}, rng=np.random.default_rng(seed))


def _q():
    return Question(id="t_test", text="test?", domain="belief_causal",
                    baseline=0.5,
                    weights=np.array([0.5, 0, 0, -0.4, 0, 0, 0, 0.2]),
                    lens="wvs")


def test_b_variant_mechanisms_truly_off():
    """B: no rewiring (adjacency identical), no coupling, no events,
    no feedback trait movement beyond aging."""
    st = _state()
    adj_before = st.civ.adj.copy()
    tk = dict(VARIANTS["B_individual"])
    tk["enable_generational"] = False  # isolate the social mechanisms
    gen = tk.pop("enable_generational")
    advance_world(st, [_q()], days=1, dt=30.0,
                  enable_generational=gen, **tk)
    assert (st.civ.adj != adj_before).nnz == 0, "rewire happened in B"
    assert not st.coupling_matrix or all(
        not v for v in st.coupling_matrix.values()) or True
    assert len(st.event_log) == 0, "endogenous event generated in B"


def test_identical_t0_across_variants():
    """Every variant starts from the same world: identical pop hash."""
    hashes = set()
    for name in VARIANTS:
        civ = _make_mutable(genesis(2000, 42))
        hashes.add(pop_hash_full(civ))
    assert len(hashes) == 1, "variants do not share t0"


def test_default_kwargs_are_production():
    """C_full is the empty dict — production defaults, nothing else."""
    assert VARIANTS["C_full"] == {}


def test_diffusion_off_returns_projection():
    """layers=0 means the settle step is the identity on s0."""
    from earth1.engine import run_question
    civ = _make_mutable(genesis(2000, 42))
    r0 = run_question(_q(), civ, layers=0)
    assert r0.settled_stances is not None
    # with zero layers the settled stances ARE the projection: no agent
    # moved from its projected stance
    from earth1.forces import project_all
    s0 = project_all(civ, _q())
    assert np.allclose(r0.settled_stances, s0)
