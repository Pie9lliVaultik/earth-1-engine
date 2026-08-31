"""c-SHOCK summarizer: (dose - null) effects per mode, transmission ratio.

Reads CSHOCK_OUT probe files, pairs dose/null by (mode, pop, seed),
reports per-stage deltas and the cliff-vs-gradient transmission contrast.
Positive control (Standing Rule 2): cliff mode must transmit; if the
cliff (dose - null) onset effect at 200k is not positive the INSTRUMENT
is defective and no mechanism inference is admissible.
"""
import glob
import json
import os

OUT = os.environ.get("CSHOCK_OUT", "/opt/earth1-data/cshock")
KEYS = ("dep_mean", "dep_gt04", "fear_gt06", "coll_gt075", "surge_joint",
        "protest_risk_sum", "employed")

runs = {}
for p in glob.glob(os.path.join(OUT, "*_*_*_*.json")):
    d = json.load(open(p))
    if "mode" in d:
        runs[(d["mode"], d["arm"], d["pop"], d["seed"])] = d

summary = {"pairs": [], "positive_control": None}
for (mode, arm, pop, seed), d in sorted(runs.items()):
    if arm != "dose":
        continue
    n = runs.get((mode, "null", pop, seed))
    if not n:
        continue
    eff = {k: d["final"][k] - n["final"][k] for k in KEYS}
    eff["onsets"] = d["onsets_total"] - n["onsets_total"]
    summary["pairs"].append({"mode": mode, "pop": pop, "seed": seed,
                             "dose_onsets": d["onsets_total"],
                             "null_onsets": n["onsets_total"],
                             "effect": eff})

for pop in (20000, 200000):
    for k in list(KEYS) + ["onsets"]:
        by = {}
        for row in summary["pairs"]:
            if row["pop"] == pop:
                by.setdefault(row["mode"], []).append(row["effect"][k])
        if len(by) == 2:
            g = sum(by["gradient"]) / len(by["gradient"])
            c = sum(by["cliff"]) / len(by["cliff"])
            summary[f"contrast_{pop}_{k}"] = {
                "gradient_mean_effect": g, "cliff_mean_effect": c,
                "absorption": (c - g)}

pc = summary.get("contrast_200000_onsets")
if pc is not None:
    summary["positive_control"] = {
        "cliff_transmits": pc["cliff_mean_effect"] > 0,
        "note": "if false the instrument is defective (VOID-eligible), "
                "no mechanism inference"}

path = os.path.join(OUT, "summary.json")
json.dump(summary, open(path, "w"), indent=1)
print("CSHOCK SUMMARY ->", path)
for k, v in summary.items():
    if k.startswith("contrast_"):
        print(k, json.dumps(v))
print("positive_control", json.dumps(summary["positive_control"]))
