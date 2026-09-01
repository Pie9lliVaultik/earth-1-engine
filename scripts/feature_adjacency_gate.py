"""MANDATORY GATE — runs BEFORE any new genesis input is measured.

Origin (2026-08-18): religiosity was injected into genesis as
Q164 >= 6. Q164 IS a GOQA benchmark item. The injected feature
correlated +0.983 with its own target and >0.5 with 16 of 40 targets.
The resulting 10.59 -> 9.42pp "improvement" was the answer key, not
structure. Caught by an external reviewer AFTER it was committed —
this gate exists so the check happens BEFORE.

INSTRUMENT CHANGE (founder order 2026-09-01, B2-c1c): the ban
criterion is PROVENANCE — a candidate is BANNED iff its source shares
respondents, instrument, or derivation with any judged estate.
Correlation with targets is a WARNING, never a ban: an external
religiosity level SHOULD correlate with religion items — that is
signal; the 2026-08-18 fake gain was banned because the source WAS the
judged survey, which the provenance rule captures directly. Undeclared
provenance fails CLOSED (BANNED). The report records the exact file
(name + sha256) each verdict cleared; consumers must refuse a verdict
borrowed by a different file.

Rules:
  R1-PROV (BAN)   provenance in SHARED_WITH_JUDGED, or undeclared
  W2      (WARN)  |corr| with any single target > 0.50
  W3      (WARN)  count of targets with |corr| > 0.35 exceeds 4
Exit code 1 only on R1-PROV for a feature in the active EARTH1_INJECT
set. The full table is always written to data/feature_adjacency.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark_questions import ISO3_TO_ISO2

MAX_SINGLE = 0.50
MAX_BROAD = 4
BROAD_LEVEL = 0.35

# provenance classes that share respondents/instrument/derivation with
# a judged estate (WVS-7 estates, GOQA/Pew estates)
SHARED_WITH_JUDGED = {"wvs7-microdata", "goqa", "pew-gas"}

# candidate feature -> WVS source variable id (legacy R1 provenance note)
SOURCES = {
    "religiosity": "Q164",
    "marital": "Q273",
    "employed": "Q279",
    "ideology": "Q240",
    "social_class": "Q287",
    "household_size": "Q270",
    "children": "Q274",
    "town_size": "G_TOWNSIZE",
    "immigrant": "Q263",
    "income_scale": "Q288",
}

# legacy prior files carry no provenance declaration; their origin is
# documented in genesis.py: WVS-7 microdata
LEGACY_PROVENANCE = "wvs7-microdata"


def _file_provenance(path: str, data: dict) -> str:
    src = str(data.get("source", "")).lower()
    if "factbook" in src:
        return "external:cia-world-factbook"
    if "provenance" in data:
        return str(data["provenance"])
    if os.path.basename(path) in ("religiosity_priors.json",
                                  "joint_priors.json"):
        return LEGACY_PROVENANCE
    return "UNDECLARED"


def load_priors() -> dict:
    """feature -> (per-country prior dict, file path, provenance)."""
    out = {}
    rp = os.environ.get("EARTH1_RELIGIOSITY_FILE", "religiosity_priors.json")
    for cand in (os.path.join("data", rp),
                 os.path.join("data", "national_inputs", rp), rp):
        if os.path.exists(cand):
            d = json.load(open(cand))
            prov = _file_provenance(cand, d)
            out["religiosity"] = (d.get("countries", d), cand, prov)
            break
    p = "data/joint_priors.json"
    if os.path.exists(p):
        d = json.load(open(p))
        for feat, pri in d.items():
            out[feat] = (pri, p, _file_provenance(p, d))
    return out


def main() -> None:
    gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
    priors = load_priors()
    report, banned = {}, []
    for feat, (pri, path, prov) in priors.items():
        src = SOURCES.get(feat, "?")
        corrs = {}
        for q in gt:
            xs, ys = [], []
            for iso3, d in q["countries"].items():
                i2 = ISO3_TO_ISO2.get(iso3)
                if i2 and i2 in pri:
                    xs.append(pri[i2]["marginal"])
                    ys.append(d["yes"])
            if len(xs) >= 20:
                c = float(np.corrcoef(xs, ys)[0, 1])
                if np.isfinite(c):
                    corrs[q["id"]] = round(c, 3)
        vals = list(corrs.values())
        mx = max(vals, key=abs) if vals else 0.0
        broad = sum(1 for v in vals if abs(v) > BROAD_LEVEL)
        r1 = (prov in SHARED_WITH_JUDGED) or (prov == "UNDECLARED")
        w2 = abs(mx) > MAX_SINGLE
        w3 = broad > MAX_BROAD
        verdict = "BANNED" if r1 else "clean"
        if r1:
            banned.append(feat)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
        report[feat] = {"source_var": src, "provenance": prov,
                        "cleared_file": os.path.basename(path),
                        "cleared_sha256": sha,
                        "max_abs_corr": mx, "n_broad": broad,
                        "warnings": ([f"W2 max|corr| {abs(mx):.3f}>0.50"]
                                     if w2 else [])
                        + ([f"W3 broad {broad}>4"] if w3 else []),
                        "verdict": verdict, "corrs": corrs}
        print(f"  {feat:13s} prov {prov:28s} | max|corr| {abs(mx):.3f} "
              f"| >0.35: {broad:2d} | warn: {w2 or w3} -> {verdict}",
              flush=True)
    json.dump({"rules": {"criterion": "provenance (B2-c1c instrument change)",
                         "shared_with_judged": sorted(SHARED_WITH_JUDGED),
                         "warn_max_single": MAX_SINGLE,
                         "warn_broad_level": BROAD_LEVEL,
                         "warn_max_broad": MAX_BROAD},
               "features": report}, open("data/feature_adjacency.json", "w"),
              indent=1)
    active = [f.strip() for f in
              os.environ.get("EARTH1_INJECT", "").split(",") if f.strip()]
    blocked = [f for f in active if f in banned]
    print(f"ADJACENCY-GATE: banned {banned or 'none'} | active set {active} "
          f"| blocked {blocked or 'none'}")
    if blocked:
        sys.exit(1)


if __name__ == "__main__":
    main()
