"""Fit the POLAR operator on TRAIN countries, score on HELD-OUT.

Prereg: data/polar_interaction_prereg.json (registered before this
file existed). Baseline to beat: W1 0.3499 (no interaction), extreme
mass 0.036 vs reality 0.647.

Split: countries hashed into 2/3 train, 1/3 held out (seeded, fixed).
Every reported number is held-out. Train-vs-heldout gap is reported as
the overfit guard.
Env: PF_POP (default 50000), PF_ROUNDS.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.benchmark_questions import ISO3_TO_ISO2
from earth1.calibration import calibrate_single, _get_country_index
from earth1.engine import run_question
from earth1.genesis import genesis
from earth1.polar import polar_settle
from earth1.types import Question

POP = int(os.environ.get("PF_POP", "50000"))
ROUNDS = int(os.environ.get("PF_ROUNDS", "20"))
MIN_AGENTS = 40
EDGES = np.linspace(0.0, 1.0, 11)

GRID = [
    # (hub_fraction, fire_rate, attraction, repulsion_threshold, repulsion_strength)
    (0.20, 0.01, 0.10, 0.60, 0.05),
    (0.20, 0.05, 0.20, 0.60, 0.05),
    (0.20, 0.10, 0.30, 0.50, 0.10),
    (0.20, 0.20, 0.40, 0.50, 0.15),
    (0.10, 0.20, 0.50, 0.40, 0.20),
    (0.20, 0.30, 0.60, 0.40, 0.25),
    (0.30, 0.30, 0.70, 0.35, 0.30),
    (0.20, 0.50, 0.80, 0.30, 0.35),
]


def w1(p, q):
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum() / (len(p) - 1))


def hist_from(v):
    h, _ = np.histogram(np.clip(v, 0, 1), bins=EDGES)
    t = h.sum()
    return h / t if t > 0 else np.full(10, 0.1)


def is_train(cc: str) -> bool:
    h = hashlib.sha256(f"polar-split-2026-08-18|{cc}".encode()).hexdigest()
    return int(h[:8], 16) % 3 != 0


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    gt = {q["id"]: q for q in
          json.load(open("data/benchmark/goqa_ground_truth.json"))}
    dens = json.load(open("data/cell_densities.json"))

    # projections once (calibration must not see the operator)
    base = {}
    for qcode in dens:
        if qcode not in gt:
            continue
        q = gt[qcode]
        ct = {ISO3_TO_ISO2[c]: d["yes"] for c, d in q["countries"].items()
              if c in ISO3_TO_ISO2}
        g = q["global_yes_popweighted"]
        w = calibrate_single(civ, g, ct)
        if np.any(w):
            base[qcode] = run_question(
                Question(id=qcode, text=q["text"], domain="belief_causal",
                         baseline=g, weights=w, lens="wvs"),
                civ, layers=0).settled_stances

    cells = []
    for qcode, cs in dens.items():
        if qcode not in base:
            continue
        for key, cell in cs.items():
            cc, a, e = key.split("|")
            if cc not in c2i:
                continue
            a, e = int(a), int(e)
            m = ((civ.country == c2i[cc]) & (civ.education == e)
                 & ((civ.age_bucket == a) if a < 3 else (civ.age_bucket >= 3)))
            if m.sum() >= MIN_AGENTS:
                cells.append((qcode, cc, m, np.array(cell["hist"])))
    print(f"scoring {len(cells)} cells "
          f"({sum(1 for c in cells if is_train(c[1]))} train)", flush=True)

    def score(stances_by_q, train: bool):
        errs, exts = [], []
        for qcode, cc, m, obs in cells:
            if is_train(cc) != train:
                continue
            hp = hist_from(stances_by_q[qcode][m])
            errs.append(w1(hp, obs))
            exts.append(hp[0] + hp[-1])
        return float(np.mean(errs)), float(np.mean(exts))

    rows = []
    b_tr, b_ext_tr = score(base, True)
    b_ho, b_ext_ho = score(base, False)
    print(f"  BASELINE (no interaction): train W1 {b_tr:.4f} | held-out "
          f"{b_ho:.4f} | extreme {b_ext_ho:.3f}", flush=True)
    for hub, fire, att, rth, rst in GRID:
        st = {q: polar_settle(s, civ.adj, seed=42, rounds=ROUNDS,
                              hub_fraction=hub, fire_rate=fire,
                              attraction=att, repulsion_threshold=rth,
                              repulsion_strength=rst)
              for q, s in base.items()}
        tr, ext_tr = score(st, True)
        ho, ext_ho = score(st, False)
        rows.append({"hub": hub, "fire": fire, "att": att, "rth": rth,
                     "rst": rst, "train_w1": tr, "heldout_w1": ho,
                     "heldout_extreme": ext_ho})
        print(f"  hub {hub:.2f} fire {fire:.2f} att {att:.2f} "
              f"rep {rth:.2f}/{rst:.2f} | train {tr:.4f} | HELD-OUT "
              f"{ho:.4f} | extreme {ext_ho:.3f}", flush=True)

    best = min(rows, key=lambda r: r["train_w1"])   # selected on TRAIN only
    out = {"pop": POP, "rounds": ROUNDS,
           "baseline_heldout_w1": b_ho, "baseline_extreme": b_ext_ho,
           "observed_extreme": float(np.mean([c[3][0] + c[3][-1]
                                              for c in cells])),
           "selected_on_train": best, "grid": rows,
           "overfit_gap": best["heldout_w1"] - best["train_w1"]}
    json.dump(out, open("data/polar_fit.json", "w"), indent=1)
    print(f"POLAR-VERDICT: held-out W1 {best['heldout_w1']:.4f} vs baseline "
          f"{b_ho:.4f} ({100*(b_ho-best['heldout_w1']):+.2f}pp) | extreme "
          f"mass {best['heldout_extreme']:.3f} vs baseline "
          f"{b_ext_ho:.3f} vs observed {out['observed_extreme']:.3f} | "
          f"overfit gap {out['overfit_gap']:+.4f}", flush=True)


if __name__ == "__main__":
    main()
