#!/usr/bin/env python3
"""The daily heartbeat (bible §21) — one command, run every day.

  1. Load the living world (born once, persisted forever) — or birth it.
  2. Tick one day: force dynamics, feedback, coupling, thresholds,
     emergent events. The day's questions are a deterministic rotation
     through the calibrated corpus.
  3. Arm new market readings into the standing record (§20.2).
  4. Resolve any readings whose markets closed; update the Atlas.

Usage:
  python3 scripts/world_daily.py [--pop 200000] [--days 1]
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WORLD_PATH = ROOT / "data" / "living" / "earth1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pop", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--batch", type=int, default=8,
                    help="questions diffused per tick")
    ap.add_argument("--db", default=f"sqlite:///{ROOT}/data/standing_record.db")
    ap.add_argument("--skip-record", action="store_true",
                    help="tick only; do not touch the standing record")
    ap.add_argument("--enable-receiver", action="store_true",
                    help="activate grounding stack (§14 placebo gate enforced)")
    ap.add_argument("--skip-placebo", action="store_true",
                    help="skip placebo gate (trust cached passport)")
    ap.add_argument("--read-news", action="store_true",
                    help="the world reads today's headlines through the "
                         "validated perception channel (needs LLM key)")
    args = ap.parse_args()

    os.environ.setdefault("DATABASE_URL", args.db)

    import numpy as np
    from earth1.living import LivingWorld
    from earth1.corpus import QuestionCorpus
    from earth1.types import Question
    from earth1.receiver import ReceiverConfig

    # ── 1. the world ──
    if (WORLD_PATH / "world.json").exists():
        world = LivingWorld.load(WORLD_PATH)
        print(f"Living world loaded: {world.state.civ.n:,} agents, "
              f"day {world.state.tick_count}")
    else:
        print(f"Birthing the living world ({args.pop:,} agents, seed {args.seed})...")
        world = LivingWorld.create(WORLD_PATH, pop=args.pop, seed=args.seed)
        print(f"Born. Frozen anchor: {world.meta['frozen_pop_hash'][:12]}")

    # ── 2. the day's questions: deterministic rotation through the corpus ──
    corpus_path = ROOT / "data" / "corpus" / "goqa_seed"
    corpus = QuestionCorpus.load(corpus_path)
    day = world.state.tick_count
    idx = [(day * args.batch + i) % len(corpus) for i in range(args.batch)]
    questions = [
        Question(id=corpus.ids[i], text=corpus.texts[i], domain="belief_causal",
                 baseline=float(corpus.baselines[i]),
                 weights=corpus.weights[i], lens="wvs")
        for i in idx
    ]

    # ── 2b. §14 placebo gate for receiver activation ──
    receiver_active = False
    passport_path = WORLD_PATH / "placebo_passport.json"
    if args.enable_receiver:
        if world.state.receiver_config is None:
            world.state.receiver_config = ReceiverConfig.default()

        if not args.skip_placebo and not passport_path.exists():
            import json as _json
            from earth1.placebo import run_placebo_gate, print_passport
            from earth1.engine import build_genesis_civilization
            gate_civ = build_genesis_civilization(5000, seed=args.seed)
            gate_questions = questions[:min(3, len(questions))]
            passport = run_placebo_gate(gate_civ, gate_questions, n_perms=50)
            print(print_passport(passport))
            with open(passport_path, "w") as f:
                _json.dump({
                    "all_pass": passport.all_pass,
                    "sources": {sid: {"passes": r.passes, "p_value": r.p_value,
                                      "real_dispersion": r.real_dispersion}
                                for sid, r in passport.results.items()},
                }, f)
            if passport.all_pass:
                receiver_active = True
                validated = [sid for sid, r in passport.results.items() if r.passes]
                for src in world.state.receiver_config.sources:
                    src.enabled = src.source_id in validated
                print(f"Receiver activated: {validated}")
            else:
                failed = [sid for sid, r in passport.results.items() if not r.passes]
                print(f"Receiver BLOCKED — sources failed placebo: {failed}")
        elif passport_path.exists():
            import json as _json
            with open(passport_path) as f:
                cached = _json.load(f)
            if cached["all_pass"]:
                receiver_active = True
                validated = [s for s, d in cached["sources"].items() if d["passes"]]
                for src in world.state.receiver_config.sources:
                    src.enabled = src.source_id in validated
                print(f"Receiver activated (cached passport): {validated}")
            else:
                print("Receiver BLOCKED (cached passport)")
        else:
            receiver_active = True
            print("Receiver activated (placebo gate skipped)")

    # ── 2c. the world reads today's news (validated perception channel) ──
    if args.read_news:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("News read SKIPPED: no ANTHROPIC_API_KEY "
                  "(channel off, never silent)")
        else:
            from earth1.daily_news import read_todays_news
            print("The world reads today's news...")
            news_events = read_todays_news(
                day=world.state.tick_count,
                t=world.state.t,
                ledger_path=WORLD_PATH / "abstentions.jsonl",
            )
            for ev in news_events:
                world.state.event_log.append(ev)
            print(f"  {len(news_events)} perceived events entered the world")

    stats = world.tick(
        questions, days=args.days,
        use_force_dynamics=True, residue_rate=0.0005,
        enable_feedback=True, enable_coupling=True,
        enable_thresholds=True, enable_rewire=True,
        enable_event_generation=True,
        enable_generational=True,
        enable_receiver=receiver_active,
    )
    drift = world.drift_report()
    worst = max(drift.values(), key=lambda v: v["max_abs"])["max_abs"]
    fixed = world.re_anchor(tolerance=0.05)
    if fixed:
        world.save()
    print(f"Ticked {args.days} day(s) -> day {world.state.tick_count}. "
          f"Deaths/births: {stats['deaths']}. Worst census drift: {worst:.4f}"
          + (f" ({fixed} cells re-anchored)" if fixed else "")
          + (f" [receiver ON]" if receiver_active else ""))

    if args.skip_record:
        return

    # ── 3+4. the standing record ──
    from earth1.db import init_db, get_session
    from earth1.markets import fetch_open_markets
    from earth1.arming import arm_all
    from earth1.resolving import resolve_armed, atlas_report
    from earth1.db.models import Prediction

    init_db()
    session = get_session()

    markets = fetch_open_markets()
    existing = {p.question_text for p in
                session.query(Prediction).filter_by(armed=True).all()}
    fresh = [m for m in markets if m.question not in existing][:25]
    outcomes = arm_all(session, world.state.civ, fresh)
    armed = sum(1 for o in outcomes if o.status == "armed")
    print(f"Record: {len(markets)} live markets, {len(fresh)} new, "
          f"{armed} armed, {len(fresh) - armed} abstained (ledgered)")

    resolved = [o for o in resolve_armed(session) if o.status == "resolved"]
    if resolved:
        print(f"Resolved today: {len(resolved)}")
    report = atlas_report(session)
    if report["n_resolved"]:
        line = f"Atlas: n={report['n_resolved']} engine Brier {report['engine_brier']:.4f}"
        if report["market_brier"] is not None:
            line += f" vs market {report['market_brier']:.4f}"
        print(line)
    session.close()


if __name__ == "__main__":
    main()
