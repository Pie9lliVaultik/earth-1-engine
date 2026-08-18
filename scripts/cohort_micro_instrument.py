"""MICRO cohort instrument — first data point (registered program step 1).

Does the FROZEN engine know how age groups differ? Engine age-bucket
readouts vs OFFICIAL W7 cohort seeds (microdata, survey-weighted,
pooled cross-country). Registered prediction: it fails (within-country
structure is genesis-authored). Micro caveats: 20K pop, engine buckets
18-30/30-45/45-60/60+ vs seeds 18-29/30-44/45-59/60+ (1y boundary
slip, flagged); engine pooled unweighted vs seeds survey-weighted.
"""
from __future__ import annotations
import csv, json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from earth1.genesis import genesis
from earth1.engine import run_question
from earth1.calibration import calibrate_single
from earth1.types import Question

POP = int(os.environ.get("CMI_POP", "20000"))
AGE_COLS = ["target_age_18_29", "target_age_30_44",
            "target_age_45_59", "target_age_60_plus"]

civ = genesis(POP, 42)
gt = {q["id"]: q for q in json.load(open("data/benchmark/goqa_ground_truth.json"))}
rows = list(csv.DictReader(open("data/wvs_wave7_cohort_seeds_official.csv")))
out, maes, grad_hits, grad_n = [], [], 0, 0
for r in rows:
    m = re.search(r"wvs_code=(Q\d+)", r["notes"])
    if not m or m.group(1) not in gt:
        continue
    q = gt[m.group(1)]
    targets = [float(r[c]) for c in AGE_COLS if r[c]]
    if len(targets) < 4:
        continue
    ct = {cc: d["yes"] for cc, d in q["countries"].items()}
    # GOQA truth uses ISO3; calibrate_single expects engine codes — map via first 2? Use global baseline + fit on available codes
    from earth1.benchmark import ISO3_TO_ISO2
    ct2 = {ISO3_TO_ISO2[c]: v for c, v in ct.items() if c in ISO3_TO_ISO2}
    g = q["global_yes_popweighted"]
    w = calibrate_single(civ, g, ct2)
    if not np.any(w):
        continue
    res = run_question(Question(id=q["id"], text=q["text"],
                                domain="belief_causal", baseline=g,
                                weights=w, lens="wvs"), civ)
    s = res.settled_stances
    eng = [float(s[civ.age_bucket == 0].mean()),
           float(s[civ.age_bucket == 1].mean()),
           float(s[civ.age_bucket == 2].mean()),
           float(s[(civ.age_bucket == 3) | (civ.age_bucket == 4)].mean())]
    errs = [abs(e - t) for e, t in zip(eng, targets)]
    maes.extend(errs)
    # gradient direction: sign of (young - old)
    obs_grad = np.sign(targets[0] - targets[3])
    eng_grad = np.sign(eng[0] - eng[3])
    if obs_grad != 0:
        grad_n += 1
        grad_hits += int(obs_grad == eng_grad)
    out.append({"q": q["id"], "engine": [round(x, 3) for x in eng],
                "official": [round(t, 3) for t in targets],
                "mae": round(float(np.mean(errs)), 4),
                "grad_match": bool(obs_grad == eng_grad)})
    print(f"{q['id']:6s} engine {['%.2f' % x for x in eng]} vs "
          f"official {['%.2f' % t for t in targets]} "
          f"grad {'OK' if obs_grad == eng_grad else 'MISS'}", flush=True)
naive = []
for r in rows:  # naive: national-pooled mean for every bucket
    m = re.search(r"wvs_code=(Q\d+)", r["notes"])
    if not m or m.group(1) not in gt: continue
    targets = [float(r[c]) for c in AGE_COLS if r[c]]
    if len(targets) < 4: continue
    mean_t = float(np.mean(targets))
    naive.extend(abs(mean_t - t) for t in targets)
print(f"\nCOHORT-MICRO: {len(out)} questions | engine bucket-MAE "
      f"{np.mean(maes):.4f} vs flat-baseline {np.mean(naive):.4f} | "
      f"age-gradient direction {grad_hits}/{grad_n}", flush=True)
json.dump(out, open("data/cohort_micro_instrument.json", "w"), indent=1)
