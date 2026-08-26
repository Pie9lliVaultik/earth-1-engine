"""Benchmark A v2 frozen KAs: exact marginal preservation and the
no-target-leakage scorer contract."""
import numpy as np

from earth1.benchmark_a.mean_preserving import (center_latent, ka_mean_preservation,
                                                solve_K)


def test_ka_mean_preservation():
    r = ka_mean_preservation()
    assert r["pass"], r
    assert r["worst_abs_mean_error"] <= 1e-8


def test_marginal_exact_on_pathological_spread():
    rng = np.random.default_rng(7)
    d = center_latent(rng.normal(0, 6.0, 10000))       # extreme spread
    for anchor in (0.03, 0.5, 0.97):
        K, p = solve_K(anchor, d)
        assert abs(p.mean() - anchor) <= 1e-8
        assert p.std() > 0.01                          # structure survives


def test_extreme_anchor_wide_spread_converges():
    """The exact regime that pinned the fixed bracket (VOID 2026-08-26)."""
    rng = np.random.default_rng(3)
    d = center_latent(rng.standard_t(3, 8000) * 5.0)     # spread ~10
    for anchor in (0.997, 0.003, 0.9995):
        K, p = solve_K(anchor, d)
        assert abs(p.mean() - anchor) <= 1e-8, (anchor, p.mean())


def test_leakage_guard_fails_closed():
    from earth1.benchmark_a.leakage import assert_anchor_oos
    ok = {"country": "DE", "anchor_train_countries": ["FR", "IT"], "anchor_model": "mrp"}
    assert_anchor_oos(ok)
    bad = {"country": "DE", "anchor_train_countries": ["FR", "DE"], "anchor_model": "mrp"}
    try:
        assert_anchor_oos(bad)
    except ValueError:
        return
    raise AssertionError("leakage guard did not fail closed")
