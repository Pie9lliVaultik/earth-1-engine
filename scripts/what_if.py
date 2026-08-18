"""WHAT IF — read the world's reaction to a future that hasn't happened.

This is the product, stated plainly: take the living population as it
stands today, hold a question in front of it, then run that same
population through several possible futures and report how it moves.

Not "what is the number". What CHANGES, who changes, how far the world
would have to bend for each future to be the one it is already shaped
like.

  PRESENT   the world as it is now, at its current tick
  BRANCH    the same world after a possible event lands on it
  MOVE      how far opinion travels, in points
  DOMINANT  which of the eight forces carries the branch
  CONTORT   how much the world must deform to reach that future
  WEIGHT    plausibility, from contortion scaled by the present's
            fragility — a fragile present makes distant futures live

The READING is the future the present is already leaning toward: the
lowest-contortion branch. That is the claim — not a probability, a
SHAPE. The world is already bent some way, and this says which way.

Usage:
  python3 scripts/what_if.py --question "..." --futures war_outbreak,peace_deal
  python3 scripts/what_if.py --list-futures
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.multiverse import rehearse
from earth1.scenarios import EVENT_CATALOG, ScenarioBranch
from earth1.types import Force, Question

WORLD_PATH = ROOT / "data" / "living" / "earth1"
FORCE_NAME = [f.name.lower() for f in Force]


def load_world(pop: int, seed: int):
    """The LIVING world if it exists on disk, else a fresh genesis."""
    if (WORLD_PATH / "civ.npz").exists():
        from earth1.living import LivingWorld
        w = LivingWorld.load(WORLD_PATH)
        return w.state.civ, w.state, f"living world, day {w.state.tick_count}"
    from earth1.genesis import genesis
    return genesis(pop, seed), None, f"fresh genesis ({pop:,})"


def pick_question(text: str | None):
    """Use a calibrated corpus question when the text matches one."""
    from earth1.corpus import QuestionCorpus
    corp_path = ROOT / "data" / "corpus.json"
    if text and corp_path.exists():
        try:
            c = QuestionCorpus()
            c.load(str(corp_path))
            hit = c.nearest(text, k=1)
            if hit:
                i = c.ids.index(hit[0]["id"]) if isinstance(hit[0], dict) \
                    else 0
                return Question(id=c.ids[i], text=c.texts[i],
                                domain=c.domains[i], baseline=c.baselines[i],
                                weights=c.weights[i]), "corpus-calibrated"
        except Exception:
            pass
    # uncalibrated probe: uniform sensitivity, so the BRANCH DELTA is
    # the signal and the absolute level is explicitly not a claim
    w = np.full(len(Force), 0.25)
    return Question(id="probe", text=text or "probe", domain="belief_causal",
                    baseline=0.5, weights=w), "uncalibrated probe"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", default="Should the government do more "
                                          "to protect people like me?")
    ap.add_argument("--futures", default="war_outbreak,financial_crisis,"
                                         "pandemic_onset,social_movement,"
                                         "peace_deal")
    ap.add_argument("--pop", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--list-futures", action="store_true")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    if args.list_futures:
        for eid, e in EVENT_CATALOG.items():
            print(f"  {eid:22s} {e.label}")
        return

    civ, state, origin = load_world(args.pop, args.seed)
    q, qkind = pick_question(args.question)

    ids = [s.strip() for s in args.futures.split(",") if s.strip()]
    unknown = [i for i in ids if i not in EVENT_CATALOG]
    if unknown:
        print(f"unknown futures: {unknown} (try --list-futures)")
        return

    branches = [ScenarioBranch(id="status_quo", label="Nothing happens",
                               steps=[])]
    branches += [ScenarioBranch.from_event_ids(i, EVENT_CATALOG[i].label,
                                               [(0, i)]) for i in ids]

    reh = rehearse(q, civ, branches,
                   event_log=state.event_log if state else None,
                   t=state.t if state else 0.0)

    present = reh.present
    print(f"\n  WORLD    {origin}, {civ.n:,} agents")
    print(f"  QUESTION {q.text}")
    print(f"           ({qkind})")
    print(f"  PRESENT  {present.yes_pct * 100:.1f}% yes  |  "
          f"fragility {present.fragility:.3f}\n")
    print(f"  {'FUTURE':30s} {'YES':>7s} {'MOVE':>8s} "
          f"{'DOMINANT':>12s} {'CONTORT':>8s} {'WEIGHT':>7s}")
    rows = []
    for b in reh.branches:
        move = (b.yes_pct - present.yes_pct) * 100
        w = reh.fragility_weights.get(b.id, 0.0)
        star = " <- READING" if b.id == reh.reading.id else ""
        print(f"  {b.label[:30]:30s} {b.yes_pct * 100:6.1f}% "
              f"{move:+7.2f}pp {FORCE_NAME[b.dominant.value]:>12s} "
              f"{b.contortion:8.3f} {w:6.1%}{star}")
        rows.append({"id": b.id, "label": b.label,
                     "yes_pct": round(float(b.yes_pct), 5),
                     "move_pp": round(float(move), 3),
                     "dominant": FORCE_NAME[b.dominant.value],
                     "contortion": round(float(b.contortion), 4),
                     "weight": round(float(w), 4),
                     "is_reading": b.id == reh.reading.id})

    spread = max(r["move_pp"] for r in rows) - min(r["move_pp"] for r in rows)
    print(f"\n  READING  {reh.reading.label} — the future this world is "
          f"already shaped like")
    print(f"  SPREAD   {spread:.2f}pp between the most and least "
          f"favourable future")
    if spread < 0.5:
        print("  NOTE     the futures barely separate: on this question "
              "the world is not listening")

    if args.json:
        json.dump({"origin": origin, "question": q.text, "kind": qkind,
                   "n_agents": int(civ.n),
                   "present_yes": round(float(present.yes_pct), 5),
                   "fragility": round(float(present.fragility), 5),
                   "reading": reh.reading.id, "spread_pp": round(spread, 3),
                   "branches": rows},
                  open(args.json, "w"), indent=1)
        print(f"  wrote {args.json}")


if __name__ == "__main__":
    main()
