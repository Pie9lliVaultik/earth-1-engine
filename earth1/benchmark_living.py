"""BENCHMARK, LIVING — the official one-ontology benchmark entry point.

Reads ONLY `alive.World` through `answer_living`; constructs no other
Earth. Runs the registered question set (`benchmark_questions`) and
reports predicted vs target with full provenance. The per-question
weight calibration on the living stack is Benchmark A (Phase 1), so
every number here is stamped UNCALIBRATED; this module is the
harness the Phase-1 loop calibrates INTO, not a claim of fidelity.
The retired engine harness is `legacy_benchmark` (LEGACY_COMPARISON_
ONLY, opt-in import) and can never be selected here.
"""
from __future__ import annotations

import time

import numpy as np

from earth1.answer_living import answer_question, _provenance
from earth1.benchmark_questions import BENCHMARK_QUESTIONS


def run(w, questions=None) -> dict:
    qs = list(questions or BENCHMARK_QUESTIONS)
    results = [answer_question(w, q) for q in qs]
    errs = [r["global_error_uncalibrated"] for r in results
            if "global_error_uncalibrated" in r]
    return {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "entry_point": "earth1.benchmark_living.run",
            "ontology": "alive.World (sole)",
            "provenance": _provenance(w),
            "n_questions": len(results),
            "mae_global_uncalibrated": float(np.mean(errs)) if errs
            else None,
            "results": results}
