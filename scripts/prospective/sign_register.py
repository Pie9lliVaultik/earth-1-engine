"""Re-sign the prospective register through the multiverse adapter
(founder amendment item 5; tag prospective-2026-09-01b).

Modes:
  warm            birth 20k candidate world, warm 60d, save base.pkl
  floors          twin-null noise floors (global + US-scoped), write
                  into data/question_classes.json (freeze-once)
  sign <i> <n>    shard i of n: run adapter over all register questions,
                  write verdicts to $SIGN_OUT/verdict_<qid>.json
  assemble <tag>  chain-append re-signed entries to the register

Country detection is v1-minimal: US election/rate markets detected by
keyword; everything else runs global-scope (recorded per verdict).
"""
import glob
import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
OUT = os.environ.get("SIGN_OUT", "/opt/earth1-data/sign_b")
REG = os.path.join(ROOT, "ops/alive/PROSPECTIVE_REGISTER.jsonl")
BASE = os.path.join(OUT, "base.pkl")
US_RX = re.compile(r"\b(senate|governor|congress|house of representatives|"
                   r"fed|fomc|federal reserve|u\.?s\.?|america|presidential|"
                   r"midterm|new hampshire|maine|michigan|texas|california|"
                   r"virginia|georgia|arizona)\b", re.I)


def entries():
    return [json.loads(l) for l in open(REG)]


def warm():
    from earth1.alive import birth_world, live_one_day
    from earth1 import persistence
    os.makedirs(OUT, exist_ok=True)
    w = birth_world(20000, 424242, substrate="c2plus_v1")
    rng = np.random.default_rng(424242)
    for _ in range(60):
        live_one_day(w, rng)
    persistence.save_world(w, BASE, rng=rng)
    print("WARM SAVED", persistence.world_hash(w)[:16])


def floors():
    from earth1 import persistence
    from earth1.adapters import multiverse
    w, _, _ = persistence.load_world(BASE)
    fg = multiverse.measure_noise_floor(w, 1, 60, None, n_pairs=3)
    fus = multiverse.measure_noise_floor(w, 2, 60, "US", n_pairs=3)
    p = os.path.join(ROOT, "data/question_classes.json")
    d = json.load(open(p))
    for cls, tpl in d["classes"].items():
        scoped = tpl["injector"]["scope"] == "country"
        tpl["noise_floor"] = round(fus if scoped else fg, 5)
        tpl["noise_floor_basis"] = ("twin-null 2x mean, 20k/60d, "
                                    + ("US-scoped" if scoped else "global"))
    json.dump(d, open(p, "w"), indent=1, sort_keys=True)
    print("FLOORS global=%.4f us=%.4f -> question_classes.json" % (fg, fus))


def sign(shard, nshards):
    from earth1 import persistence
    from earth1.adapters import multiverse
    w, _, _ = persistence.load_world(BASE)
    rows = [e for e in entries() if e.get("p_model") is None]
    for i, e in enumerate(rows):
        if i % nshards != shard:
            continue
        qid = e["question_id"]
        vp = os.path.join(OUT, f"verdict_{re.sub('[^A-Za-z0-9_-]', '_', qid)}.json")
        if os.path.exists(vp):
            continue
        country = "US" if US_RX.search(e["question"]) else None
        spec = {"question_id": qid, "class": e["class"],
                "outcomes": ["YES", "NO"], "country": country}
        try:
            v = multiverse.answer(spec, w, seed=abs(hash(qid)) % 100000,
                                  horizon_days=60)
            out = v.__dict__
        except Exception as ex:
            out = {"question_id": qid, "p_model": None, "abstain": True,
                   "abstain_reason": f"adapter error: {ex!r}"}
        out["country_detected"] = country
        json.dump(out, open(vp, "w"), indent=1, default=str)
        print("SIGNED", qid, "abstain" if out.get("abstain")
              else round(out["p_model"], 3), flush=True)


def assemble(tag):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from append_register import sign as line_sign
    import subprocess
    verdicts = {}
    for p in glob.glob(os.path.join(OUT, "verdict_*.json")):
        d = json.load(open(p))
        verdicts[d["question_id"]] = d
    lines = entries()
    prev = lines[-1]["line_sha256"]
    tree = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True,
                          cwd=ROOT).stdout.strip()
    n_signed = n_abst = 0
    with open(REG, "a") as f:
        for e in lines:
            v = verdicts.get(e["question_id"])
            if v is None or e.get("p_model") is not None:
                continue
            if e.get("tag") == tag:
                continue
            entry = {k: e[k] for k in e if k not in
                     ("line_sha256", "prev_line_sha256", "tag")}
            entry.update({
                "abstain": bool(v.get("abstain")),
                "abstain_reason": v.get("abstain_reason"),
                "p_model": v.get("p_model"),
                "adapter": "multiverse_v1",
                "conviction_index": v.get("conviction_index"),
                "branch_hashes": v.get("branch_hashes"),
                "country": v.get("country_detected"),
                "tag": tag, "tree_hash": tree,
                "prev_line_sha256": prev,
            })
            entry["line_sha256"] = line_sign(entry)
            f.write(json.dumps(entry, sort_keys=True) + "\n")
            prev = entry["line_sha256"]
            n_abst += int(entry["abstain"])
            n_signed += 1
    print(f"ASSEMBLED {n_signed} re-signed entries ({n_abst} abstain) "
          f"tag {tag}; tail {prev[:12]}")
    seen = set()
    dup = [q for q in verdicts if q in seen or seen.add(q)]
    assert not dup


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "warm":
        warm()
    elif mode == "floors":
        floors()
    elif mode == "sign":
        sign(int(sys.argv[2]), int(sys.argv[3]))
    elif mode == "assemble":
        assemble(sys.argv[2])
