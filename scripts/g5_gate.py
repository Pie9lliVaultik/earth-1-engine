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
    from earth1.g5 import (
        run_g5_gate, print_g5_report, g5_temporal_replay,
        g5_event_reaction, g5_demography,
    )

    history_path = ROOT / "data" / "gdelt_history.json"
    use_replay = history_path.exists() and not args.fast

    if args.fast:
        print("[fast] smoke run — this is NOT a gate result\n")
        report = run_g5_gate(pop=10_000, seed=args.seed,
                             temporal_years=2.0, demography_years=2.0,
                             progress=True)
        replay = None
    elif use_replay:
        # amendment A2: temporal leg runs with historical replay +
        # inline shuffled-geography control
        from earth1.replay import load_history
        history = load_history(history_path)
        print(f"G5 leg 1/3: temporal with GDELT replay "
              f"({len(history)} countries, A2)...")
        replay = g5_temporal_replay(history, pop=args.pop, seed=args.seed,
                                    progress=True)
        print("G5 leg 2/3: event reaction...")
        event = g5_event_reaction(pop=args.pop, seed=args.seed)
        print("G5 leg 3/3: demography...")
        demography = g5_demography(pop=args.pop, seed=args.seed)

        from earth1.g5 import G5Report
        report = G5Report(
            temporal=replay.real, event=event, demography=demography,
            all_pass=replay.passes and event.passes and demography.passes,
        )
    else:
        report = run_g5_gate(pop=args.pop, seed=args.seed, progress=True)
        replay = None

    print()
    print(print_g5_report(report))
    if replay is not None:
        r, s, e = replay.real, replay.shuffled, replay.endogenous
        print(
            f"\nA2 replay detail ({'PASS' if replay.passes else 'FAIL'}):\n"
            f"  real      MAE {r.mae_engine:.4f}  sign {r.sign_accuracy:.1%} (p={r.sign_p:.4f})\n"
            f"  shuffled  MAE {s.mae_engine:.4f}  sign {s.sign_accuracy:.1%}\n"
            f"  endogen.  MAE {e.mae_engine:.4f}  sign {e.sign_accuracy:.1%}\n"
            f"  no-change MAE {r.mae_nochange:.4f}"
        )

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
    if replay is not None:
        entry["temporal_replay"] = {
            "passes": replay.passes,
            "endogenous": asdict(replay.endogenous),
            "real": asdict(replay.real),
            "shuffled": asdict(replay.shuffled),
        }
    history = json.loads(RESULTS.read_text()) if RESULTS.exists() else []
    history.append(entry)
    RESULTS.write_text(json.dumps(history, indent=2))
    print(f"\nRecorded run #{len(history)} -> {RESULTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
