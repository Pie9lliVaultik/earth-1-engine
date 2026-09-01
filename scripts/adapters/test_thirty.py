"""Founder order 2026-09-01 item 5: 30 heterogeneous questions through
the one door. 10 opinion, 10 forecast (>=6 classes incl 3 unseen),
10 conditional. Report door/class/tier and result shape; any refusal or
untyped number is a defect.

usage: test_thirty.py <shard> <nshards>   (verdicts -> $THIRTY_OUT)
       test_thirty.py report
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = os.environ.get("THIRTY_OUT", "/opt/earth1-data/thirty")
BASE = "/opt/earth1-data/sign_b/base.pkl"

Q = [
    # 10 opinion
    ("o1", "Do people trust the press in their country?", None, None),
    ("o2", "Should the government redistribute wealth from rich to poor?", None, None),
    ("o3", "Do people feel safe walking alone at night?", None, None),
    ("o4", "Is immigration good for the economy?", None, "DE"),
    ("o5", "Do people approve of their national government?", None, "BR"),
    ("o6", "Should religion play a larger role in politics?", None, "US"),
    ("o7", "Do people believe climate change threatens their way of life?", None, None),
    ("o8", "Is it acceptable for couples to live together unmarried?", None, None),
    ("o9", "Do people trust banks?", None, None),
    ("o10", "How do people feel about artificial intelligence?", None, None),
    # 10 forecast — >=6 classes, 3 unseen (papal succession, earnings, sports)
    ("f1", "Will the Fed cut interest rates at the October 2026 meeting?", "rate_decision", "US"),
    ("f2", "Will Tarcisio de Freitas win the 2026 Brazilian presidential election?", "election", "BR"),
    ("f3", "Will the Israel-Iran ceasefire hold through October 2026?", "conflict", None),
    ("f4", "Will a mass protest wave occur in France before December 2026?", "protest", "FR"),
    ("f5", "Will the S&P 500 fall 10% from its peak before year end?", "market_cascade", None),
    ("f6", "Will the EU adopt the AI liability directive in 2026?", "policy", "DE"),
    ("f7", "Will a new pope be elected before March 2027?", "papal_succession", None),
    ("f8", "Will Apple report record quarterly earnings in Q4 2026?", "corporate_earnings", "US"),
    ("f9", "Will Brazil win the 2026 FIFA World Cup?", "sports_final", "BR"),
    ("f10", "Will Germany hold snap federal elections before mid-2027?", "election", "DE"),
    # 10 conditional
    ("c1", "What happens if the ceasefire collapses?", "conflict", None),
    ("c2", "What happens if the Fed surprises with a 50bps hike?", "rate_decision", "US"),
    ("c3", "What would happen if Brazil elected a far-right president?", "election", "BR"),
    ("c4", "What happens if a major European bank fails?", "market_cascade", "DE"),
    ("c5", "What happens if fuel prices double in six months?", None, None),
    ("c6", "What would change if universal basic income were adopted nationally?", "policy", "US"),
    ("c7", "What happens if a new pandemic emerges next year?", None, None),
    ("c8", "What happens if mass protests erupt in Iran?", "protest", "IR"),
    ("c9", "What would happen if the EU fragmented?", None, "DE"),
    ("c10", "What happens if AI displaces a quarter of service jobs?", None, None),
]


def run(shard, nshards):
    from earth1 import persistence
    from earth1.adapters import multiverse as mv
    os.makedirs(OUT, exist_ok=True)
    w, _, _ = persistence.load_world(BASE)
    for i, (qid, text, cls, country) in enumerate(Q):
        if i % nshards != shard:
            continue
        p = os.path.join(OUT, f"{qid}.json")
        if os.path.exists(p):
            continue
        try:
            payload = mv.ask({"question_id": f"thirty:{qid}", "text": text,
                              "class": cls, "country": country},
                             w, seed=9000 + i, horizon_days=45)
        except Exception as e:
            payload = {"question_id": qid, "DEFECT": f"raised: {e!r}"}
        json.dump(payload, open(p, "w"), indent=1, default=str)
        print("DONE", qid, payload.get("door"), payload.get("class"),
              payload.get("calibration_tier", "?"), flush=True)


def report():
    rows = []
    for qid, text, cls, country in Q:
        p = os.path.join(OUT, f"{qid}.json")
        d = json.load(open(p)) if os.path.exists(p) else {"DEFECT": "missing"}
        shape = ("DEFECT" if "DEFECT" in d else
                 "dist+stance" if d["door"] == "opinion" else
                 "forks" if d["door"] == "conditional" else
                 ("p_model" if d.get("p_model") is not None else "abstain"))
        res = (d.get("stance_share") if d.get("door") == "opinion"
               else d.get("p_model") if d.get("door") == "forecast"
               else (len(d.get("forks") or [])))
        rows.append((qid, d.get("door", "?"), d.get("class", "?"),
                     d.get("calibration_tier", "?"), shape, res,
                     (d.get("DEFECT") or d.get("abstain_reason") or "")[:45]))
    print(f"{'q':4s} {'door':12s} {'class':22s} {'tier':13s} {'shape':11s} {'result':>8s}  note")
    for r in rows:
        v = r[5]
        vs = f"{v:.3f}" if isinstance(v, float) else str(v)
        print(f"{r[0]:4s} {r[1]:12s} {str(r[2])[:22]:22s} {r[3]:13s} {r[4]:11s} {vs:>8s}  {r[6]}")
    defects = [r for r in rows if r[4] == "DEFECT"]
    print(f"\n{len(rows)} questions, {len(defects)} defects, "
          f"{sum(1 for r in rows if r[4]=='abstain')} typed abstentions")


if __name__ == "__main__":
    if sys.argv[1] == "report":
        report()
    else:
        run(int(sys.argv[1]), int(sys.argv[2]))
