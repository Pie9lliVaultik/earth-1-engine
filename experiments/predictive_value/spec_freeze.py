"""Freeze the predictive-value experiment spec BEFORE any result exists
and BEFORE W5 data lands (EXPERIMENT_PLAN.md §10 step 1).

Writes frozen/spec.json: dataset hashes, seeds, variant table, metric
definitions, the seeded 12-country guard holdout, commit SHA, physics
version. Append-only from then on.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

from variants import VARIANTS  # noqa: E402
from earth1.forces import PHYSICS_VERSION  # noqa: E402
from earth1.wvs_paired import WVS_PAIRED  # noqa: E402

DATASETS = [
    "earth1/wvs_paired.py",
    "data/wdi_tide.json",
    "data/perceived_cases.json",
    "data/question_profiles.json",
    "data/temporal_partition.json",
    "data/g5_preregistration.json",
]


def sha(path: str) -> str:
    return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()


def main() -> None:
    countries = sorted({c for q in WVS_PAIRED for c in q.overlapping_countries})
    # seeded guard holdout: 12 of 37, deterministic, tuned on by NOTHING
    ranked = sorted(countries, key=lambda c: hashlib.sha256(
        f"earth1-pv-holdout-2026-08-17|{c}".encode()).hexdigest())
    holdout = sorted(ranked[:12])

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    spec = {
        "frozen_at_commit": commit,
        "physics_version": PHYSICS_VERSION,
        "dataset_sha256": {p: sha(p) for p in DATASETS},
        "seeds": [42, 43, 44, 45, 46],
        "pop": 50000,
        "temporal": {"years": 7.0, "dt_days": 30.0},
        "variants": VARIANTS,
        "benchmarks": ["temporal_w6w7", "event_a3"],
        "metrics": ["mae_delta", "sign_accuracy_CONTAMINATED",
                    "heterogeneity_r", "pooled_r", "calibration_slope"],
        "countries_all": countries,
        "countries_guard_holdout": holdout,
        "honesty": {
            "w6w7_label": "development/diagnostic — NOT blind "
                          "(per-question outcomes inspected before design)",
            "untouched_test": "WVS Wave 8 when published; EVS 2017 "
                              "out-of-set countries; frozen betas, no "
                              "re-registration",
            "w5_status": "NOT in repo at freeze time — spec cannot have "
                         "been shaped by training data",
        },
        "conclusions_space": ["C>B>A", "B>A,C~B", "B~C~A"],
        "registered_prediction": {
            "event_class": "C>B>A0",
            "secular_no_dev_channel": "B~C~A0",
            "secular_with_dev_channel": "open — the experiment's question",
        },
    }
    out = os.path.join(os.path.dirname(__file__), "frozen", "spec.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(spec, f, indent=1)
    print(f"SPEC-FROZEN at {commit[:10]} physics {PHYSICS_VERSION} | "
          f"guard holdout: {','.join(holdout)}")


if __name__ == "__main__":
    main()
