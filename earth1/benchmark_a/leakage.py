"""No-target-leakage contract (Benchmark A v2). The scorer calls
assert_anchor_oos on EVERY scored row and fails closed."""
from __future__ import annotations


def assert_anchor_oos(row: dict) -> None:
    c = row.get("country")
    tr = row.get("anchor_train_countries")
    if c is None or tr is None:
        raise ValueError(f"anchor provenance missing on scored row: {row.keys()}")
    if c in set(tr):
        raise ValueError(f"TARGET LEAKAGE: scored country {c} inside its own anchor's training set")
