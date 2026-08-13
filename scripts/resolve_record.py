#!/usr/bin/env python3
"""Daily resolution run for the standing record (bible §20.2).

Checks every armed, open reading against its live market. Resolved
readings are scored into the Force-Outcome Atlas; cancelled markets are
voided; hash mismatches are flagged as tampered and never scored.
Prints the running G4 scoreboard.

Usage:
  python3 scripts/resolve_record.py [--db sqlite:///data/standing_record.db]

Run daily alongside arm_record.py.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=f"sqlite:///{ROOT}/data/standing_record.db")
    args = ap.parse_args()

    os.environ.setdefault("DATABASE_URL", args.db)

    from earth1.db import init_db, get_session
    from earth1.resolving import resolve_armed, atlas_report

    init_db()
    session = get_session()
    if session is None:
        print("FATAL: no database session"); sys.exit(1)

    outcomes = resolve_armed(session)

    resolved = [o for o in outcomes if o.status == "resolved"]
    voided = [o for o in outcomes if o.status == "voided"]
    tampered = [o for o in outcomes if o.status == "tampered"]
    still_open = [o for o in outcomes if o.status == "open"]

    print("=" * 76)
    print("STANDING RECORD — resolution run")
    print("=" * 76)
    for o in resolved:
        print(f"  RESOLVED  {o.question[:48]:<50s} "
              f"engine={o.engine_yes_pct:.2f} price={o.price_at_arming or 0:.2f} "
              f"actual={o.actual:.0f} frag={o.fragility or 0:.2f}")
    for o in tampered:
        print(f"  TAMPERED  {o.question[:60]} — hash mismatch, NOT scored")
    print(f"\n  Resolved: {len(resolved)}  Voided: {len(voided)}  "
          f"Tampered: {len(tampered)}  Still open: {len(still_open)}")

    report = atlas_report(session)
    print()
    print("  FORCE-OUTCOME ATLAS — G4 scoreboard")
    print("  " + "-" * 50)
    if report["n_resolved"] == 0:
        print("  No resolutions yet. The record accumulates.")
    else:
        print(f"  Resolved tuples:  {report['n_resolved']}")
        print(f"  Engine Brier:     {report['engine_brier']:.4f}")
        if report["market_brier"] is not None:
            print(f"  Market Brier:     {report['market_brier']:.4f}")
            verdict = "ENGINE BEATS PRICE" if report["engine_beats_price"] \
                else "price ahead"
            print(f"  → {verdict}")
        fs = report.get("fragility_split")
        if fs:
            print(f"  Fragility split:  high-frag err {fs['high_fragility_mean_error']:.3f} "
                  f"vs low-frag err {fs['low_fragility_mean_error']:.3f} "
                  f"({'predicts collapse' if fs['fragility_predicts_error'] else 'no signal yet'})")
    session.close()


if __name__ == "__main__":
    main()
