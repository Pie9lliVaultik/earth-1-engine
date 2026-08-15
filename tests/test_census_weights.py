"""Population-weighting fix (external review P0): at 100k agents the
min-per-country floor puts 174/194 countries AT the floor — India holds
11.2% of agents vs 17.9% of humanity, and unweighted world reads
overweight small countries ~40x."""
import sys
sys.path.insert(0, ".")

import numpy as np

from earth1.genesis import genesis, census_weights, GENESIS_COUNTRY_CODES
from earth1.engine import build_genesis_civilization, run_question
from earth1.types import Question, NUM_FORCES


def test_weights_mean_one_and_positive():
    civ = genesis(50_000, seed=42)
    w = census_weights(civ)
    assert abs(w.mean() - 1.0) < 1e-9
    assert np.all(w > 0)


def test_india_upweighted_small_countries_downweighted():
    civ = genesis(100_000, seed=42)
    w = census_weights(civ)
    idx_in = GENESIS_COUNTRY_CODES.index("IN")
    idx_cy = GENESIS_COUNTRY_CODES.index("CY")
    assert w[civ.country == idx_in].mean() > 1.3   # India underrepresented
    assert w[civ.country == idx_cy].mean() < 0.1   # Cyprus 40x overrepresented


def test_weighted_share_recovers_census():
    civ = genesis(100_000, seed=42)
    w = census_weights(civ)
    idx_in = GENESIS_COUNTRY_CODES.index("IN")
    weighted_share = w[civ.country == idx_in].sum() / w.sum()
    assert abs(weighted_share - 0.179) < 0.01  # census 17.9%


def test_run_question_exposes_weighted_read():
    civ = build_genesis_civilization(20_000, seed=42)
    wts = np.zeros(NUM_FORCES)
    wts[0] = 0.8
    q = Question(id="wq", text="t", domain="belief_causal",
                 baseline=0.5, weights=wts, lens="wvs")
    r = run_question(q, civ)
    assert r.yes_pct_weighted is not None
    assert 0.0 <= r.yes_pct_weighted <= 1.0
    assert abs(r.yes_pct_weighted - r.yes_pct) > 1e-9  # floor distortion is real
