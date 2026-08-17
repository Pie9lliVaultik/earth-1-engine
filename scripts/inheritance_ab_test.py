"""Inheritance-ontology adjudication: A ("current") vs B ("entry").

The question (registered 2026-08-17): is the endogenous conservative
drift produced by present-state inheritance a meaningful causal
mechanism or a bookkeeping artifact? Neither drift nor stationarity is
a bug by definition — the arm that better reproduces real longitudinal
cohort behavior wins.

Court: the G5 temporal leg — calibrate on WVS Wave 6, evolve 7 years
with ALL endogenous mechanisms on, score against observed Wave 7
deltas. Identical pop, seed, questions, step count for both arms; the
ONLY difference is EARTH1_INHERITANCE_BASIS.

Also reported: the direction census — what fraction of observed W6->W7
deltas are liberalizing vs each arm's predicted direction. A predicts
systematic conservatization; B predicts approximately no endogenous
drift. Reality's vote is the observed direction distribution.

Interpretation registered before running:
  A materially better  -> the drift was useful endogenous inheritance.
  B materially better  -> A conflated aging with cohort transmission.
  Neither              -> the 7y window is too short to discriminate;
                          escalate to real cohort-level WVS data.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

POP = int(os.environ.get("AB_POP", "50000"))
YEARS = float(os.environ.get("AB_YEARS", "7.0"))
SEED = 42


def run_arm(basis: str) -> dict:
    os.environ["EARTH1_INHERITANCE_BASIS"] = basis
    # import inside the arm so nothing caches across settings
    from earth1.g5 import g5_temporal
    r = g5_temporal(pop=POP, seed=SEED, years=YEARS, progress=False)
    per_q = r.per_question
    return {
        "basis": basis,
        "n_pairs": r.n_pairs,
        "mae_engine": r.mae_engine,
        "mae_nochange": r.mae_nochange,
        "sign_accuracy": r.sign_accuracy,
        "sign_p": r.sign_p,
        "per_question": per_q,
    }


def _merge() -> None:
    a = json.load(open("data/inheritance_ab_current.json"))
    b = json.load(open("data/inheritance_ab_entry.json"))
    out = {
        "pop": POP, "years": YEARS, "seed": SEED,
        "arms": {"current": a, "entry": b},
        "delta_mae_A_minus_B": a["mae_engine"] - b["mae_engine"],
        "delta_sign_A_minus_B": a["sign_accuracy"] - b["sign_accuracy"],
    }
    with open("data/inheritance_ab.json", "w") as f:
        json.dump(out, f, indent=1, default=str)
    better = ("A(current)" if a["mae_engine"] < b["mae_engine"]
              else "B(entry)")
    print(f"INHERITANCE-AB-VERDICT: MAE A {a['mae_engine']:.4f} "
          f"B {b['mae_engine']:.4f} | sign A {a['sign_accuracy']:.3f} "
          f"B {b['sign_accuracy']:.3f} | lower-MAE arm: {better}",
          flush=True)


def main() -> None:
    """Modes: 'current' | 'entry' — run ONE arm as its own process
    (parallel wall-clock, supervisor-relaunchable) and write
    data/inheritance_ab_<arm>.json; 'merge' — combine both arm files
    into data/inheritance_ab.json + verdict; 'both' (default) — serial
    legacy mode."""
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    if mode == "merge":
        _merge()
        return
    arms = ("current", "entry") if mode == "both" else (mode,)
    results = {}
    for basis in arms:
        print(f"arm {basis}: pop {POP}, {YEARS:.0f}y ...", flush=True)
        results[basis] = run_arm(basis)
        a = results[basis]
        print(f"  mae_engine {a['mae_engine']:.4f} "
              f"vs nochange {a['mae_nochange']:.4f} | "
              f"sign {a['sign_accuracy']:.3f} (p={a['sign_p']:.3f})",
              flush=True)
        with open(f"data/inheritance_ab_{basis}.json", "w") as f:
            json.dump(results[basis], f, indent=1, default=str)
        print(f"ARM-DONE: {basis}", flush=True)
    if mode == "both":
        _merge()


if __name__ == "__main__":
    main()
