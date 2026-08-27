"""c006 fit — age row of the demo→force gradient, linear-response
calibration on DEV. Conditions (founder ruling): general term (age row
only populated); signs pre-committed (c006_signs_precommit.json,
committed before this script existed); fit on FIT-half countries
(split by sha of iso2), out-of-country r reported on the other half.
Steps: (1) probe world measures per-force persistence k_f of a genesis
β through 180d of dynamics; (2) WVS logit age-gradients g_i per item
(FIT countries); (3) readout force-weights w_if from the cycle ridge on
FIT cells; (4) weighted LS solve g_i = Σ_f w_if·k_f·β_f; (5) sign
concordance vs the pre-commitment; (6) registered FITTED artifact.
"""
import hashlib
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

XBAND = {"a18-29": (23.5 - 18) / 72 - 0.5, "a30-49": (39.5 - 18) / 72 - 0.5,
         "a50+": (60.0 - 18) / 72 - 0.5}
PROBE_BETA = 0.15
FORCES = ["FEAR", "DESIRE", "ECONOMICS", "COLLECTIVE", "IDENTITY",
          "CULTURE", "EXPERIENCE", "TEMPERAMENT"]


def _fit_half(iso2):
    return int(hashlib.sha256(iso2.encode()).hexdigest(), 16) % 2 == 0


def world_cells(flag_beta=None):
    if flag_beta is not None:
        json.dump({"axes": {"age": {"beta": flag_beta}}},
                  open(os.path.join(ROOT, "data/demo_force_gradient.v1.json"), "w"))
        os.environ["EARTH1_DEMO_FORCE_GRADIENT"] = "v1"
    else:
        os.environ.pop("EARTH1_DEMO_FORCE_GRADIENT", None)
    for m in [k for k in list(sys.modules) if k.startswith("earth1")]:
        del sys.modules[m]
    from earth1.alive import birth_world, live_one_day
    from earth1.calibration import living_features
    from earth1.genesis import GENESIS_COUNTRY_CODES
    w = birth_world(20_000, 4242, substrate="c2plus_v1")
    rng = np.random.default_rng(4242)
    for _ in range(180):
        live_one_day(w, rng)
    X = living_features(w)
    civ, alive = w.civ, w.health.alive
    yrs = 18.0 + np.asarray(civ.age) * 72.0
    band = np.where(yrs < 30, "a18-29", np.where(yrs < 50, "a30-49", "a50+"))
    feats = {}
    for ci in np.unique(civ.country[alive]):
        cm = alive & (civ.country == ci)
        for b in np.unique(band[cm]):
            m = cm & (band == b)
            if m.sum() >= 25:
                feats[(GENESIS_COUNTRY_CODES[ci], b)] = X[m].mean(0)
    return feats


def force_slope(feats):
    """Per-force regression slope of cell force-mean on band x."""
    out = np.zeros(8)
    for f in range(8):
        xs = np.array([XBAND[b] for (_, b) in feats])
        ys = np.array([v[f] for v in feats.values()])
        out[f] = np.polyfit(xs, ys, 1)[0]
    return out


def main():
    ax = json.load(open(os.path.join(
        ROOT, "data/benchmark_a/axis_targets_v1.json")))["axes"]["age"]
    base = world_cells(None)
    k_probe = world_cells([PROBE_BETA] * 8)
    k = (force_slope(k_probe) - force_slope(base)) / PROBE_BETA
    print("persistence k_f:", np.round(k, 3))
    # readout weights + WVS gradients on FIT countries
    fit_items_w, fit_items_g, wts = [], [], []
    for item, cc in ax.items():
        cells = [(c2, b, d["yes"], d["n"]) for c2, cs in cc.items()
                 for b, d in cs.items() if (c2, b) in base and _fit_half(c2)]
        if len({c[0] for c in cells}) < 8:
            continue
        Xa = np.array([base[(c2, b)] for c2, b, _, _ in cells])
        ya = np.array([y for _, _, y, _ in cells]).clip(1e-3, 1 - 1e-3)
        na = np.array([n for _, _, _, n in cells], float)
        la = np.log(ya / (1 - ya))
        mu, sd = Xa.mean(0), np.maximum(Xa.std(0), 1e-9)
        Z = (Xa - mu) / sd
        A_ = Z.T @ Z + 1.0 * np.eye(Z.shape[1])
        b_ = np.linalg.solve(A_, Z.T @ (la - la.mean()))
        w_force = b_[:8] / sd[:8]              # unstandardized force weights
        xs = np.array([XBAND[b] for _, b, _, _ in cells])
        g = np.polyfit(xs, la, 1, w=np.sqrt(na))[0]   # WVS logit age-gradient
        fit_items_w.append(w_force)
        fit_items_g.append(g)
        wts.append(na.sum())
    W = np.array(fit_items_w) * k[None, :]      # design: g ≈ W @ beta
    g = np.array(fit_items_g)
    sw = np.sqrt(np.array(wts))
    beta, *_ = np.linalg.lstsq(W * sw[:, None], g * sw, rcond=None)
    beta = np.clip(beta, -0.35, 0.35)
    signs = json.load(open(os.path.join(
        ROOT, "data/cycles/c006_signs_precommit.json")))["expected_signs"]
    concord = {}
    for i, f in enumerate(FORCES):
        want = signs[f]
        got = "+" if beta[i] > 0.01 else ("-" if beta[i] < -0.01 else "0")
        concord[f] = {"beta": round(float(beta[i]), 4), "expected": want,
                      "agrees": bool(want == got or want == "0")}
    art = {"axes": {"age": {"beta": [round(float(b), 4) for b in beta]}},
           "status": "FITTED",
           "fit": {"persistence_k": [round(float(x), 4) for x in k],
                   "n_items": len(g),
                   "split": "sha256(iso2) % 2 == 0 -> FIT",
                   "targets_sha": hashlib.sha256(open(os.path.join(
                       ROOT, "data/benchmark_a/axis_targets_v1.json"),
                       "rb").read()).hexdigest()[:10],
                   "signs_sha": hashlib.sha256(open(os.path.join(
                       ROOT, "data/cycles/c006_signs_precommit.json"),
                       "rb").read()).hexdigest()[:10]},
           "sign_concordance": concord}
    json.dump(art, open(os.path.join(
        ROOT, "data/demo_force_gradient.v1.json"), "w"), indent=1)
    print(json.dumps(concord, indent=1))


if __name__ == "__main__":
    main()
