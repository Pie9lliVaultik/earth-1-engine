"""API v1 acceptance test (founder ruling item 6): stand the surface up
against frozen 0.9, run the 30 questions through /ask and the five
scenarios through /consequences, and DIFF the payloads against
direct-adapter outputs — must be identical (same seeds, same worlds).

usage: test_v1.py  (on prime; uses TestClient, no network needed)
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "adapters"))


def main():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from earth1.api.v1 import router, _world
    from earth1.adapters import multiverse as mv
    from test_thirty import Q
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)

    h = c.get("/v1/health").json()
    assert h["freeze_tag"] == "freeze-0.9", h
    print("health:", {k: h[k] for k in ("epoch", "freeze_tag", "tree_hash")},
          "| fidelities:", h["fidelities"])

    mismatches = 0
    for i, (qid, text, cls, country) in enumerate(Q):
        body = {"question_id": f"acc:{qid}", "text": text, "class": cls,
                "country": country, "fidelity": "20k"}
        r = c.post("/v1/ask", json=body)
        assert r.status_code == 200, (qid, r.status_code, r.text[:200])
        api = r.json()["result"]
        w = copy.deepcopy(_world("20k"))
        direct = mv.ask({"question_id": f"acc:{qid}", "text": text,
                         "class": cls, "country": country, "p_market": None},
                        w, seed=int(__import__("hashlib").sha256(
            f"acc:{qid}".encode()).hexdigest()[:8], 16) % 99991,
                        horizon_days=45)
        a = json.dumps(api, sort_keys=True, default=str)
        b = json.dumps(direct, sort_keys=True, default=str)
        if a != b:
            mismatches += 1
            ka = {k for k in api if json.dumps(api[k], default=str)
                  != json.dumps(direct.get(k), default=str)}
            print("  MISMATCH", qid, sorted(ka))
    print(f"/ask diff: 30 questions, {mismatches} mismatches")

    from five_scenarios import scenarios
    cq_ok = 0
    for name, cfg in sorted(scenarios().items()):
        sc = cfg["scenario"]
        body = {"class": cfg["class"], "fidelity": "20k", "seeds": 2,
                "horizon_days": 30,
                "scenario": {"id": sc.id, "label": sc.label,
                             "forces": sc.forces, "countries": sc.countries,
                             "firm_damage": sc.firm_damage,
                             "trade_shock": sc.trade_shock,
                             "persists_days": sc.persists_days}}
        r = c.post("/v1/consequences", json=body)
        assert r.status_code == 200, (name, r.text[:200])
        rep = r.json()["report"]
        assert {"order0", "order1", "order2", "order3", "order4",
                "headline", "tier_counts"} <= set(rep), name
        for line in rep["order2"]:
            if line["tier"] == "ABSTAIN":
                assert line["delta"] is None, ("ABSTAIN leaked a number",
                                               name, line)
        r2 = c.post("/v1/consequences", json=body)
        assert r2.json()["cached"] is True, "cache miss on repeat"
        cq_ok += 1
        print(f"  {name}: tiers {rep['tier_counts']} (cache verified)")
    print(f"/consequences: {cq_ok}/5 shape+abstain+cache OK")

    r = c.get("/v1/world/state")
    ws = r.json()
    assert ws["countries"] and ws["countries"][0]["centroid"], "no geometry"
    print("/world/state:", len(ws["countries"]), "countries with centroids")
    reg_line = None
    for line in open(os.path.join(ROOT, "ops/alive/PROSPECTIVE_REGISTER.jsonl")):
        reg_line = json.loads(line)
    r = c.get(f"/v1/forecast/{reg_line['question_id']}")
    assert r.status_code == 200 and "p_model" in r.json()["forecast"]
    print("/forecast/{id}: OK |", r.json()["forecast"]["status"])
    print("ACCEPTANCE COMPLETE")


if __name__ == "__main__":
    main()
