"""40-question grounding-first test (founder ruling item 4).
usage: test_forty.py  (runs the 10 new grounding questions + reruns the
30 through the router; prints resolved_at/scope/answer/source)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEN = [
    ("g1", "Is an asteroid hitting Earth today?"),
    ("g2", "Will gold drop below $1 today?"),
    ("g3", "Will it rain in Milan tomorrow?"),
    ("g4", "Who wins the Champions League final?"),
    ("g5", "Will Apple beat earnings this quarter?"),
    ("g6", "Is Pedro Sánchez still the Prime Minister of Spain?"),
    ("g7", "Did the Fed cut rates in July?"),
    ("g8", "Will the euro fall below 0.5 USD this month?"),
    ("g9", "Will there be a magnitude-9 earthquake in Tokyo this year?"),
    ("g10", "Will Bitcoin hit $1,000,000 by Friday?"),
]


def main(mode="all", shard=0, nshards=1):
    from earth1 import persistence
    from earth1.adapters import router as rt
    from test_thirty import Q
    w, _, _ = persistence.load_world("/opt/earth1-data/sign_b/base.pkl")
    shrugs, rows = 0, []
    if mode in ("all", "ten"):
        for qid, text in TEN:
            p = rt.answer_any({"question_id": f"forty:{qid}", "text": text},
                              w, seed=4000, horizon_days=45,
                              include_reaction=False)
            rows.append((qid, p))
    if mode in ("all", "thirty"):
        for i, (qid, text, cls, country) in enumerate(Q):
            if i % nshards != shard:
                continue
            p = rt.answer_any({"question_id": f"forty:{qid}", "text": text,
                               "class": cls, "country": country},
                              w, seed=4000, horizon_days=45,
                              include_reaction=False)
            rows.append((qid, p))
            import json as _j, os as _o
            _o.makedirs("/opt/earth1-data/forty", exist_ok=True)
            _j.dump(p, open(f"/opt/earth1-data/forty/{qid}.json", "w"),
                    default=str)
    for qid, p in rows:
        ans = p.get("answer", "")
        src = p.get("source", "") or p.get("calibration_tier", "")
        ok = bool(ans and ans.strip())
        if not ok:
            shrugs += 1
        print(f"{qid:4s} {p.get('resolved_at','?'):11s} "
              f"{p.get('scope','?'):13s} | {ans[:110]}")
        if src:
            print(f"     src/tier: {str(src)[:100]}")
    ten_rows = rows[:10] if mode != "thirty" else []
    bad = [q for q, p in ten_rows
           if p.get("resolved_at") not in ("premise", "grounding")]
    print(f"\n40 questions | shrugs: {shrugs} (must be 0) | "
          f"ten-new not at premise/grounding: {bad or 'none'}")
    uncal_primary = [q for q, p in ten_rows
                     if "UNCALIBRATED" in str(p.get("answer", ""))]
    print("ten-new with UNCALIBRATED as primary answer:",
          uncal_primary or "none")


if __name__ == "__main__":
    import sys as _s
    a = _s.argv[1:] or ["all"]
    main(a[0], int(a[1]) if len(a) > 2 else 0,
         int(a[2]) if len(a) > 2 else 1)
