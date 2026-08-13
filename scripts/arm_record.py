#!/usr/bin/env python3
"""Daily arming run for the standing record (bible §20.2).

Fetch live belief-causal markets, perceive each (corpus-first, LLM at
the novelty frontier if a key is present), rehearse the multiverse, and
pre-commit the reading: timestamped, hashed, insert-only. Abstentions
are ledgered and never scored.

Usage:
  python3 scripts/arm_record.py [--limit N] [--db sqlite:///data/standing_record.db]

Run daily (cron/launchd). The record's value is calendar time — it
cannot be backdated.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25,
                    help="max markets to arm this run")
    ap.add_argument("--db", default=f"sqlite:///{ROOT}/data/standing_record.db")
    ap.add_argument("--agents", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    os.environ.setdefault("DATABASE_URL", args.db)

    from earth1.db import init_db, get_session
    from earth1.engine import build_genesis_civilization
    from earth1.corpus import QuestionCorpus
    from earth1.markets import fetch_open_markets
    from earth1.arming import arm_all

    init_db()
    session = get_session()
    if session is None:
        print("FATAL: no database session"); sys.exit(1)

    civ = build_genesis_civilization(args.agents, seed=args.seed)
    corpus_path = ROOT / "data" / "corpus" / "goqa_seed"
    corpus = QuestionCorpus.load(corpus_path) if corpus_path.with_suffix(".npz").exists() else None

    markets = fetch_open_markets()
    print(f"Live belief-causal markets fetched: {len(markets)}")
    if not markets:
        print("No reachable market source — nothing to arm today.")
        return

    # already-armed questions are not re-armed (pre-commitment is once)
    from earth1.db.models import Prediction
    existing = {p.question_text for p in
                session.query(Prediction).filter_by(armed=True).all()}
    fresh = [m for m in markets if m.question not in existing][:args.limit]
    print(f"New (not yet armed): {len(fresh)}")

    outcomes = arm_all(session, civ, fresh, corpus=corpus)

    armed = [o for o in outcomes if o.status == "armed"]
    abstained = [o for o in outcomes if o.status == "abstained"]

    print()
    print("=" * 76)
    print(f"STANDING RECORD — arming run")
    print("=" * 76)
    for o in armed:
        print(f"  ARMED  {o.market.question[:52]:<54s} "
              f"engine={o.engine_yes_pct:.2f} price={o.price_at_arming:.2f} "
              f"frag={o.fragility:.2f} hash={o.prediction_hash[:10]}")
    print(f"\n  Armed: {len(armed)}   Abstained (ledgered): {len(abstained)}")
    if abstained and not armed:
        print("  All abstained — no honest loading source. "
              "Set ANTHROPIC_API_KEY to enable LLM perception at the "
              "novelty frontier, or grow the corpus.")
    session.close()


if __name__ == "__main__":
    main()
