#!/usr/bin/env python3
"""Run the pre-registered G5 gate (bible v2 §21) and record the result.

Refuses to run without data/g5_preregistration.json — the protocol must
be committed before any results exist. Results land in
data/g5_results.json, appended, never overwritten: every run is part of
the record, including the failures.

Usage:
  python3 scripts/g5_gate.py [--pop 50000] [--seed 42] [--fast]
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PREREG = ROOT / "data" / "g5_preregistration.json"
RESULTS = ROOT / "data" / "g5_results.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=50_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--fast", action="store_true",
                    help="small smoke run (10k pop, 2y) — NOT a gate result")
    args = ap.parse_args()

    if not PREREG.exists():
        sys.exit("REFUSED: data/g5_preregistration.json missing — "
                 "the protocol must be registered before results run.")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(PREREG)],
        cwd=ROOT, capture_output=True).returncode == 0
    if not tracked:
        sys.exit("REFUSED: pre-registration exists but is not committed "
                 "to git — commit it first, then run the gate.")

    from dataclasses import asdict
    from earth1.g5 import run_g5_gate, print_g5_report

    if args.fast:
        print("[fast] smoke run — this is NOT a gate result\n")
        report = run_g5_gate(pop=10_000, seed=args.seed,
                             temporal_years=2.0, demography_years=2.0,
                             progress=True)
    else:
        report = run_g5_gate(pop=args.pop, seed=args.seed, progress=True)

    print()
    print(print_g5_report(report))

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pop": 10_000 if args.fast else args.pop,
        "seed": args.seed,
        "smoke_run": args.fast,
        "all_pass": report.all_pass,
        "temporal": asdict(report.temporal),
        "event": asdict(report.event),
        "demography": asdict(report.demography),
    }
    history = json.loads(RESULTS.read_text()) if RESULTS.exists() else []
    history.append(entry)
    RESULTS.write_text(json.dumps(history, indent=2))
    print(f"\nRecorded run #{len(history)} -> {RESULTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
