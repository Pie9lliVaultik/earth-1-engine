"""EXPERIENCE LOOP v0 (ops/alive/EXPERIENCE_LOOP_V0_PREREG.md).

Stages:
  plant                seal 12 hidden truths (8 WS + 4 MIS), print sha
  truth <seed>         simulate one truth stream (720d, window obs only)
  run <seed> <arm>     arm in {exp, placebo, frozen}
  score                gates G1-G7, curves, unseal for recovery
  replay <seed>        G6: rerun exp arm, diff model-hash sequence
"""
import copy
import hashlib
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from earth1.experience import Ledger, model_hash  # noqa: E402
from sbi.theta import CANONICAL, prior_ppf  # noqa: E402

V01 = os.environ.get("EXPLOOP_V01") == "1"
OUT = os.environ.get("EXPLOOP_OUT",
                     "/opt/earth1-data/exploop_v01" if V01
                     else "/opt/earth1-data/exploop")
SEALED = os.path.join(OUT, "sealed")
_SMOKE = os.environ.get("EXPLOOP_SMOKE") == "1"
_BASE = 9101 if V01 else 9001
SEEDS = list(range(_BASE, _BASE + 6)) if _SMOKE \
    else list(range(_BASE, _BASE + 12))
MIS = set(range(_BASE + 4, _BASE + 6)) if _SMOKE \
    else set(range(_BASE + 8, _BASE + 12))
POP, WINDOW, CYCLES, P, FROZEN_K = \
    (2_000, 5, 4, 8, 6) if _SMOKE else (20_000, 30, 24, 64, 20)
PROBE_DAYS = {10, 190, 370, 550}
SHOCK_DAYS = {240, 480} if V01 else set()
SHOCK_CYCLES = (8, 9, 16, 17)
ELIGIBLE = ("relax", "memory_press")
INFERENCE_VERSION = "smc-abc-v0/median-h/ess-half"


def _derange(seed):
    ws = [s for s in SEEDS if s not in MIS]
    ms = sorted(MIS)
    ring = ws if seed not in MIS else ms
    return ring[(ring.index(seed) + 1) % len(ring)]


def theta_from_u(u):
    th = dict(CANONICAL)
    th["relax"] = prior_ppf("relax", float(u[0]))
    th["memory_press"] = prior_ppf("memory_press", float(u[1]))
    return th


def _shock(w):
    """v0.1 registered known forcing u_t — identical in every world."""
    from earth1.memory import Memory
    from earth1.types import Force
    sig = np.zeros(8)
    sig[Force.ECONOMICS] = -0.12
    sig[Force.FEAR] = 0.12
    w.chronicle.events.append(Memory(
        id=f"shock_{int(w.day)}", label="shock", day=float(w.day),
        force_signature=sig, scope=w.health.alive.copy(),
        salience=1.0, half_life=60.0))


def _probe(w):
    from earth1.memory import Memory
    w.chronicle.events.append(Memory(
        id=f"obs_probe_{int(w.day)}", label="obs_probe", day=float(w.day),
        force_signature=np.full(8, 0.06),
        scope=w.health.alive.copy(), salience=0.8, half_life=180.0))


def window_obs(w, rng, kw, daily_keys=("employment_rate",
                                       "destitute_share")):
    """Step one 30-day window; return the frozen 38-value vector."""
    from earth1.alive import live_one_day
    civ = w.civ
    f0 = civ.forces[w.health.alive].mean(axis=0).copy()
    acc = {k: 0.0 for k in daily_keys}
    dep = 0.0
    for _ in range(WINDOW):
        if int(w.day) in PROBE_DAYS:
            _probe(w)
        if int(w.day) in SHOCK_DAYS:
            _shock(w)
        live_one_day(w, rng, **kw)
        alive = w.health.alive
        la = alive & w.life.in_lf
        acc["employment_rate"] += (float(w.life.employed[la].mean())
                                   if la.any() else 0.0)
        acc["destitute_share"] += float(
            (w.life.deprivation[alive] > 0.99).mean())
        dep += float(w.life.deprivation[alive].mean())
    alive = w.health.alive
    f = w.civ.forces[alive]
    v = ([acc["employment_rate"] / WINDOW, acc["destitute_share"] / WINDOW,
          dep / WINDOW]
         + list(f.mean(axis=0)) + list(f.std(axis=0))
         + list((f > 0.5).mean(axis=0))
         + list(f.mean(axis=0) - f0))
    return [float(x) for x in v]


def stage_plant():
    os.makedirs(SEALED, exist_ok=True)
    sf = os.path.join(SEALED, "exploop_truth_v0.json")
    if not os.path.exists(sf):
        seed = int.from_bytes(os.urandom(8), "big")
        rng = np.random.default_rng(seed)
        truths = {}
        for s in SEEDS:
            th = dict(CANONICAL)
            th["relax"] = prior_ppf("relax", float(rng.random()))
            th["memory_press"] = prior_ppf("memory_press",
                                           float(rng.random()))
            if s in MIS:
                th["hardship_mortality_gain"] = 2.0
                th["_beta"] = 3.0          # physics outside eligible set
            truths[str(s)] = th
        json.dump({"seed": seed, "truths": truths}, open(sf, "w"))
        os.chmod(sf, 0o400)
    print("SEALED_SHA256",
          hashlib.sha256(open(sf, "rb").read()).hexdigest())


def stage_truth(seed):
    from earth1.alive import birth_world
    from sbi.theta import apply_theta
    os.makedirs(os.path.join(OUT, "streams"), exist_ok=True)
    th = json.load(open(os.path.join(SEALED, "exploop_truth_v0.json")))[
        "truths"][str(seed)]
    beta = th.pop("_beta", None)
    kw = apply_theta(th)
    if beta is not None:
        kw["beta"] = beta
    w = birth_world(POP, seed)
    rng = np.random.default_rng(seed)
    rows = [window_obs(w, rng, kw) for _ in range(CYCLES)]
    json.dump({"seed": seed, "windows": rows},
              open(os.path.join(OUT, "streams", f"{seed}.json"), "w"))
    print("TRUTH STREAM", seed, flush=True)


def _causal_scale(revealed, dim):
    if len(revealed) < 3:
        return np.ones(dim)
    return np.maximum(np.std(np.array(revealed), axis=0), 1e-6)


def crps_ens(x, wgt, y):
    """Weighted-ensemble CRPS, averaged over observables (z-scored)."""
    t1 = (wgt[:, None] * np.abs(x - y[None, :])).sum(0)
    d = np.abs(x[:, None, :] - x[None, :, :])
    t2 = 0.5 * np.einsum("i,j,ijk->k", wgt, wgt, d)
    return float((t1 - t2).mean())


def stage_run(seed, arm):
    from earth1.alive import birth_world
    from sbi.theta import apply_theta
    os.makedirs(os.path.join(OUT, "arms"), exist_ok=True)
    own = json.load(open(os.path.join(OUT, "streams", f"{seed}.json")))[
        "windows"]
    upd_stream = own if arm != "placebo" else json.load(open(
        os.path.join(OUT, "streams", f"{_derange(seed)}.json")))["windows"]
    rng = np.random.default_rng([seed, {"exp": 1, "placebo": 2,
                                        "frozen": 3}[arm]])
    K = FROZEN_K if arm == "frozen" else P
    U = rng.random((K, 2))
    base = birth_world(POP, seed)
    worlds = [copy.deepcopy(base) for _ in range(K)]
    del base
    rngs = [np.random.default_rng([seed, 100 + i]) for i in range(K)]
    wgt = np.full(K, 1.0 / K)
    led = Ledger(os.path.join(OUT, "arms", f"{seed}_{arm}.ledger.jsonl"))
    out = {"seed": seed, "arm": arm, "crps": [], "cover90": [],
           "post_mean_u": [], "post_sd_u": [], "model_hashes": [],
           "ess": []}
    revealed = []
    resid_sq = None          # v0.1: causal obs-noise from forecast residuals
    n_resid = 0
    for c in range(CYCLES):
        vecs = np.array([window_obs(worlds[i], rngs[i],
                                    apply_theta(theta_from_u(U[i])))
                         for i in range(K)])
        y = np.array(own[c])
        V = len(y)
        scale = _causal_scale(revealed, V)
        xz, yz = vecs / scale, y / scale
        if V01:
            sig_o = (np.sqrt(resid_sq / max(n_resid, 1))
                     if resid_sq is not None and n_resid >= 2
                     else np.zeros(V))
            offs = np.array([-1.28, -0.52, 0.0, 0.52, 1.28])
            aug = (vecs[None, :, :]
                   + offs[:, None, None] * sig_o[None, None, :]
                   ).reshape(-1, V)
            aug_w = np.tile(wgt, 5) / 5.0
            score = crps_ens(aug / scale, aug_w, yz)
            vq, wq_arr = aug, aug_w
        else:
            score = crps_ens(xz, wgt, yz)
            vq, wq_arr = vecs, wgt
        def wq(col, q):
            o = np.argsort(col)
            cw = np.cumsum(wq_arr[o])
            return float(col[o][np.searchsorted(cw, q, side="left").clip(0, len(col) - 1)])
        qlo = np.array([wq(vq[:, j], 0.05) for j in range(V)])
        qhi = np.array([wq(vq[:, j], 0.95) for j in range(V)])
        cover = float(((qlo <= y) & (y <= qhi)).mean())
        prior_summary = {"mean_u": U.T.dot(wgt).tolist(),
                         "sd_u": np.sqrt(((U - U.T.dot(wgt))**2).T.dot(wgt)).tolist()}
        diff = {"updated": False}
        if arm in ("exp", "placebo"):
            yu = np.array(upd_stream[c]) / scale
            d = np.linalg.norm(xz - yu[None, :], axis=1) / np.sqrt(V)
            h = max(float(np.median(d)), 1e-6)
            if V01:
                # bandwidth FLOOR at the particle NN-distance noise
                # proxy: when systematic misfit dominates, weights
                # flatten and the posterior stays honest (prereg v0.1 #4)
                dd = np.linalg.norm(xz[:, None, :] - xz[None, :, :],
                                    axis=2) / np.sqrt(V)
                np.fill_diagonal(dd, np.inf)
                h = max(h, float(np.median(dd.min(axis=1))))
            wgt = wgt * np.exp(-d**2 / (2 * h**2))
            wgt = wgt / wgt.sum()
            ess = float(1.0 / (wgt**2).sum())
            diff = {"updated": True, "bandwidth": h, "ess": ess,
                    "resampled": False}
            if ess < K / 2:
                idx = np.searchsorted(np.cumsum(wgt),
                                      (rng.random() + np.arange(K)) / K)
                U = U[idx].copy()
                worlds = [copy.deepcopy(worlds[i]) for i in idx]
                wgt = np.full(K, 1.0 / K)
                diff["resampled"] = True
                diff["parents"] = np.asarray(idx).tolist()
                if V01:
                    # rejuvenation: reflected u-jitter, worlds keep state
                    U = U + rng.normal(0.0, 0.02, U.shape)
                    U = np.where(U < 0, -U, U)
                    U = np.where(U > 1, 2 - U, U)
                    U = U.clip(1e-6, 1 - 1e-6)
            out["ess"].append(ess)
        mh = model_hash(U, wgt)
        led.append({
            "experience_id": f"{seed}/{arm}/{c}",
            "forecast_emitted_at": c, "forecast_world_hash":
                hashlib.sha256(vecs.tobytes()).hexdigest()[:16],
            "model_version": c, "inference_version": INFERENCE_VERSION,
            "observation_cutoff": c * WINDOW,
            "predicted_distribution":
                {"q05": qlo.tolist(), "q95": qhi.tolist(),
                 "mean": vecs.T.dot(wgt).tolist()},
            "uncertainty": prior_summary["sd_u"],
            "resolution_rule": f"truth window {c} of stream {seed}",
            "resolution": y.tolist(),
            "resolution_source": ("own" if arm != "placebo"
                                  else f"deranged:{_derange(seed)}"),
            "score": score,
            "prior_posterior": prior_summary,
            "eligible_update_evidence": ("window summaries"
                                         if diff["updated"] else "none"),
            "posterior": {"mean_u": U.T.dot(wgt).tolist(),
                          "sd_u": np.sqrt(((U - U.T.dot(wgt))**2).T
                                          .dot(wgt)).tolist()},
            "update_diff": diff, "next_model_hash": mh})
        out["crps"].append(score)
        out["cover90"].append(cover)
        out["post_mean_u"].append(U.T.dot(wgt).tolist())
        out["post_sd_u"].append(np.sqrt(((U - U.T.dot(wgt))**2).T
                                        .dot(wgt)).tolist())
        out["model_hashes"].append(mh)
        if V01:
            r = vecs.T.dot(wgt) - y
            resid_sq = r * r if resid_sq is None else resid_sq + r * r
            n_resid += 1
        revealed.append(own[c])
        print(f"cycle {c} {seed}/{arm} crps={score:.4f}", flush=True)
    json.dump(out, open(os.path.join(OUT, "arms",
                                     f"{seed}_{arm}.json"), "w"))
    print("ARM DONE", seed, arm, flush=True)


def _naive_core(own, forced=False):
    """Holt smoothing per observable; Gaussian CRPS on cycles."""
    from math import erf, exp, pi, sqrt
    own = np.array(own)
    n, K = own.shape
    crps = []
    lvl, tr = own[0].copy(), np.zeros(K)
    resid = [[] for _ in range(K)]
    shock_resid = {}
    for c in range(1, n):
        mu = lvl + tr
        if forced and c in (16, 17) and (c - 8) in shock_resid:
            mu = mu + shock_resid[c - 8]
        scale = _causal_scale([list(r) for r in own[:c]], K)
        tot = 0.0
        for j in range(K):
            sd = (np.std(resid[j]) if len(resid[j]) >= 3
                  else max(abs(tr[j]), 1e-3)) or 1e-3
            z = (own[c, j] - mu[j]) / sd
            phi = exp(-z * z / 2) / sqrt(2 * pi)
            Phi = 0.5 * (1 + erf(z / sqrt(2)))
            tot += sd * (z * (2 * Phi - 1) + 2 * phi - 1 / sqrt(pi)) \
                / scale[j]
        crps.append(tot / K)
        for j in range(K):
            resid[j].append(own[c, j] - mu[j])
        if forced and c in (8, 9):
            shock_resid[c] = own[c] - mu
        newl = 0.5 * own[c] + 0.5 * (lvl + tr)
        tr = 0.3 * (newl - lvl) + 0.7 * tr
        lvl = newl
    return [crps[0]] + crps          # pad cycle0 with cycle1 value


def _naive(own):
    return _naive_core(own, forced=False)


def _naive_forced(own):
    return _naive_core(own, forced=True)


def stage_score():
    import scipy.stats as st
    ws = [s for s in SEEDS if s not in MIS]
    res = {a: {s: json.load(open(os.path.join(OUT, "arms",
                                              f"{s}_{a}.json")))
               for s in SEEDS} for a in ("frozen", "exp", "placebo")}
    streams = {s: json.load(open(os.path.join(
        OUT, "streams", f"{s}.json")))["windows"] for s in SEEDS}
    naive = {s: _naive(streams[s]) for s in SEEDS}
    naive_f = {s: _naive_forced(streams[s]) for s in SEEDS}
    late = slice(CYCLES // 2, CYCLES)

    def paired(a_hi, a_lo, seeds, cyc=None):
        cyc = late if cyc is None else cyc
        if V01:
            d = [np.mean(np.log(np.maximum(np.array(a_hi[s])[cyc], 1e-12))
                         - np.log(np.maximum(np.array(a_lo[s])[cyc],
                                             1e-12))) for s in seeds]
            wt = st.wilcoxon(d) if np.any(d) else None
            lo, hi = st.t.interval(0.95, len(d) - 1, loc=np.mean(d),
                                   scale=st.sem(d))
            return {"mean_log": float(np.mean(d)),
                    "mean": float(np.mean(d)),
                    "ci": [float(lo), float(hi)],
                    "p_wilcoxon": float(wt.pvalue) if wt else 1.0}
        d = [np.mean(np.array(a_hi[s])[cyc])
             - np.mean(np.array(a_lo[s])[cyc]) for s in seeds]
        t = st.ttest_1samp(d, 0)
        lo, hi = st.t.interval(0.95, len(d) - 1, loc=np.mean(d),
                               scale=st.sem(d))
        return {"mean": float(np.mean(d)), "ci": [float(lo), float(hi)],
                "p": float(t.pvalue)}

    crps = {a: {s: res[a][s]["crps"] for s in SEEDS}
            for a in ("frozen", "exp", "placebo")}
    g1 = paired(crps["frozen"], crps["exp"], ws)
    g1b = paired(naive, crps["exp"], ws)
    g1bf = paired(naive_f, crps["exp"], ws)
    _g8c = [c for c in SHOCK_CYCLES if c < CYCLES]
    g8 = paired(naive, crps["exp"], ws, cyc=_g8c) \
        if (V01 and _g8c) else None
    g7 = paired(crps["frozen"], crps["placebo"], ws)
    cover = float(np.mean([np.array(res["exp"][s]["cover90"])[late]
                           for s in ws]))
    tr = json.load(open(os.path.join(SEALED, "exploop_truth_v0.json")))[
        "truths"]

    def u_true(s):
        th = tr[str(s)]
        lo, hi = 0.015, 0.135
        u0 = (th["relax"] - lo) / (hi - lo)
        u1 = ((np.log(th["memory_press"]) - np.log(0.005))
              / (np.log(0.08) - np.log(0.005)))
        return np.array([u0, u1])

    rec_err, rec_cov_mis = [], []
    for s in ws:
        rec_err.append(np.abs(np.array(res["exp"][s]["post_mean_u"][-1])
                              - u_true(s)))
    for s in sorted(MIS):
        m = np.array(res["exp"][s]["post_mean_u"][-1])
        sd = np.array(res["exp"][s]["post_sd_u"][-1])
        rec_cov_mis.append(bool(np.all(np.abs(m - u_true(s))
                                       <= 1.645 * sd + 1e-9)))
    prior_sd = 1 / np.sqrt(12)
    g3 = {"mean_abs_u_err": np.mean(rec_err, axis=0).tolist(),
          "pass": bool(np.all(np.mean(rec_err, axis=0)
                              < 0.5 * prior_sd))}
    g4 = {"mis_coverage": rec_cov_mis,
          "pass": sum(rec_cov_mis) >= int(np.ceil(0.75 * len(MIS)))}
    curves = {a: np.mean([crps[a][s] for s in ws], axis=0).tolist()
              for a in ("frozen", "exp", "placebo")}
    curves["naive"] = np.mean([naive[s] for s in ws], axis=0).tolist()
    curves["naive_forced"] = np.mean([naive_f[s] for s in ws],
                                     axis=0).tolist()
    curves_mis = {a: np.mean([crps[a][s] for s in sorted(MIS)],
                             axis=0).tolist()
                  for a in ("frozen", "exp", "placebo")}
    verdict = (g1["mean"] > 0 and g1["ci"][0] > 0
               and g1b["mean"] > 0 and g1b["ci"][0] > 0
               and not (g7["mean"] > 0 and g7["ci"][0] > 0)
               and 0.80 <= cover <= 0.97)
    if V01 and g8 is not None:
        verdict = verdict and g8["mean"] > 0 and g8["ci"][0] > 0
    rep = {"G1_frozen_minus_exp": g1, "G1b_naive_minus_exp": g1b,
           "G1b_stretch_naiveforced_minus_exp": g1bf,
           "G8_shock_cycles_naive_minus_exp": g8,
           "G7_frozen_minus_placebo": g7, "G2_cover90_late": cover,
           "G3_recovery": g3, "G4_no_false_learning_mis": g4,
           "curves_ws": curves, "curves_mis": curves_mis,
           "EXPERIENTIAL_LEARNING_DEMONSTRATED": bool(verdict)}
    json.dump(rep, open(os.path.join(OUT, "v0_report.json"), "w"),
              indent=1)
    print(json.dumps({k: rep[k] for k in list(rep)[:6]}, indent=1))
    print("VERDICT:", verdict)


def stage_replay(seed):
    ref = json.load(open(os.path.join(OUT, "arms", f"{seed}_exp.json")))
    os.rename(os.path.join(OUT, "arms", f"{seed}_exp.json"),
              os.path.join(OUT, "arms", f"{seed}_exp.orig.json"))
    os.rename(os.path.join(OUT, "arms", f"{seed}_exp.ledger.jsonl"),
              os.path.join(OUT, "arms", f"{seed}_exp.ledger.orig.jsonl"))
    stage_run(seed, "exp")
    new = json.load(open(os.path.join(OUT, "arms", f"{seed}_exp.json")))
    same = ref["model_hashes"] == new["model_hashes"]
    print("G6 REPLAY", seed, "IDENTICAL" if same else "DIVERGED")
    json.dump({"seed": seed, "replay_identical": same},
              open(os.path.join(OUT, f"replay_{seed}.json"), "w"))


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "plant":
        stage_plant()
    elif a == "truth":
        stage_truth(int(sys.argv[2]))
    elif a == "run":
        stage_run(int(sys.argv[2]), sys.argv[3])
    elif a == "score":
        stage_score()
    elif a == "replay":
        stage_replay(int(sys.argv[2]))
