"""THE DYNAMICS TEST — engine movement vs PERSISTENCE.

Prereg: data/dynamics_test_prereg.json (registered first, including
the truth-provenance statement and the aggregate-ratio direction).

The composition creates this benchmark: MrsP owns levels and has no
'next', so the honest null is PERSISTENCE — the level stays put. The
engine must earn its existence by predicting MOVEMENT.

Arms per historical reaction case (leave-one-case-out for any fitted
quantity; each case's own data never touches its own prediction):
  PERSISTENCE   predicted post = observed pre (no movement)
  ENGINE        response operator from the genesis-anchored state
  SEEDED        response operator from the MrsP/pre-anchored state
                (levels re-anchored to the observed pre-value, which
                is the composition's starting point)

Reported: movement MAE per arm, sign accuracy, and the AGGREGATE
MAGNITUDE RATIO for each arm (registered expectation: seeding LOWERS
it from 0.97 toward 0.80-0.95).

TRUTH PROVENANCE: these six cases grade against AUTHORED pre/post
values. Any win here is SUGGESTIVE, not defensible; the defensible
version needs verified deltas.
Env: DP_POP (default 50000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.calibration import calibrate_single, _get_country_index
from earth1.engine import run_question
from earth1.g5 import _load_case_perceived_shocks, _load_case_response_profile
from earth1.genesis import genesis
from earth1.mrsp_seed import reanchor
from earth1.reaction_cases import REACTION_CASES
from earth1.rng import logit, sigmoid
from earth1.types import Question
from earth1.forces import RESPONSE_GAIN

POP = int(os.environ.get("DP_POP", "50000"))


def main() -> None:
    civ = genesis(POP, 42)
    c2i, _ = _get_country_index(civ)
    rows = []
    for case in REACTION_CASES:
        prof = _load_case_response_profile(case.id)
        shocks = _load_case_perceived_shocks(case.id)
        if prof is None or not shocks:
            continue
        countries = [c for c in case.pre if c in case.post and c in c2i]
        if len(countries) < 3:
            continue
        base = float(np.mean(list(case.pre.values())))
        w = calibrate_single(civ, base, case.pre)
        if not np.any(w):
            continue
        s0 = run_question(Question(id=case.id, text=case.question_text,
                                   domain="belief_causal", baseline=base,
                                   weights=w, lens="eb"), civ).settled_stances
        for cc in countries:
            m = civ.country == c2i[cc]
            if m.sum() < 30:
                continue
            pre, post = case.pre[cc], case.post[cc]
            obs_move = post - pre
            sh = shocks.get(cc)
            if not sh:
                continue
            delta = np.zeros(8)
            for deltas, _decay in sh:
                for k, v in deltas.items():
                    delta[int(k)] += float(v)
            dz = RESPONSE_GAIN * float(delta @ np.array(prof))
            # ENGINE: shift from the genesis-anchored country level
            eng_pre = float(s0[m].mean())
            eng_post = float(sigmoid(logit(np.clip(s0[m], 1e-4, 1 - 1e-4))
                                     + dz).mean())
            eng_move = eng_post - eng_pre
            # SEEDED: same shift, but from the observed pre level
            s_seeded = reanchor(s0, m, pre)
            seed_post = float(sigmoid(
                logit(np.clip(s_seeded[m], 1e-4, 1 - 1e-4)) + dz).mean())
            seed_move = seed_post - pre
            rows.append({"case": case.id, "cc": cc, "obs": obs_move,
                         "engine": eng_move, "seeded": seed_move})

    if not rows:
        print("DYNAMICS: no scorable cases", flush=True)
        return
    obs = np.array([r["obs"] for r in rows])
    out = {"pop": POP, "n": len(rows),
           "truth_provenance": "AUTHORED pre/post values — suggestive only"}
    for arm in ("engine", "seeded"):
        p = np.array([r[arm] for r in rows])
        out[arm] = {
            "movement_mae": float(np.abs(p - obs).mean()),
            "sign_acc": float(np.mean(np.sign(p) == np.sign(obs))),
            "aggregate_ratio": float(np.abs(p).mean() / max(
                np.abs(obs).mean(), 1e-9)),
            "rank_corr": float(np.corrcoef(p, obs)[0, 1])
            if len(rows) > 3 else float("nan")}
    out["persistence"] = {"movement_mae": float(np.abs(obs).mean()),
                          "sign_acc": None, "aggregate_ratio": 0.0}
    json.dump(out, open("data/dynamics_vs_persistence.json", "w"), indent=1)
    for arm in ("persistence", "engine", "seeded"):
        a = out[arm]
        print(f"  {arm:11s} movement-MAE {a['movement_mae']:.4f}"
              + (f" | sign {a['sign_acc']:.2f} | agg ratio "
                 f"{a['aggregate_ratio']:.3f} | corr {a['rank_corr']:+.3f}"
                 if arm != "persistence" else ""), flush=True)
    be = 100 * (out["persistence"]["movement_mae"]
                - out["engine"]["movement_mae"])
    bs = 100 * (out["persistence"]["movement_mae"]
                - out["seeded"]["movement_mae"])
    print(f"DYNAMICS-VERDICT: engine vs persistence {be:+.2f}pp | seeded vs "
          f"persistence {bs:+.2f}pp | n={len(rows)} (AUTHORED truth — "
          f"suggestive only)", flush=True)


if __name__ == "__main__":
    main()
