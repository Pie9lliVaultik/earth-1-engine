"""SBI inference battery (prereg A6-A9 + amendment A4.1).

Stages:
  worlds200          40-world training pool + y_obs worlds at 200k
  train <pop>        prior-draw training sims (3000 @20k, 600 @200k)
  plant              draw & seal M=5 theta* (OS entropy), run y_obs
                     (sealed mode: outputs carry NO theta)
  infer <pop>        fit ABC/NPE/NRE, SBC(200 held-out), exams
  score              unseal via dataroles(final_scoring), verdicts
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sbi.theta import CANONICAL, NAMES, THETA, prior_ppf, sample_prior  # noqa
from sbi.estimators import ABC, NPE, NRE, PRIOR_SD_U, to_u, zscore_fit  # noqa

OUT = os.environ.get("EARTH1_SBI_OUT", "/opt/earth1-data/sbi")
SEALED = os.path.join(OUT, "sealed")
DAYS = int(os.environ.get("EARTH1_SBI_DAYS", "90"))
SLOTS = int(os.environ.get("EARTH1_SBI_SLOTS", "30"))
N_TRAIN = {20_000: 3000,
           200_000: int(os.environ.get("EARTH1_SBI_NTRAIN200", "600"))}
N_SBC = 200
OBS_SEEDS = (601, 607, 613)
M_EXAMS = 5
WORKER = os.path.join(ROOT, "scripts/sbi/sim_worker.py")
PY = sys.executable


def _pool(jobs):
    procs = []
    for argv in jobs:
        while len([p for p in procs if p.poll() is None]) >= SLOTS:
            time.sleep(2)
        procs.append(subprocess.Popen(argv))
    for p in procs:
        p.wait()
    bad = [p for p in procs if p.returncode]
    print("pool done,", len(bad), "failures")
    if bad:
        sys.exit(1)


def stage_worlds200(lo=0, hi=99):
    from earth1 import persistence
    from earth1.alive import birth_world
    os.makedirs(os.path.join(OUT, "worlds"), exist_ok=True)
    for seed in (list(range(5100, 5140)) + list(OBS_SEEDS))[lo:hi]:
        p = os.path.join(OUT, "worlds", f"w200000_{seed}.pkl")
        if os.path.exists(p):
            continue
        w = birth_world(200_000, seed)
        persistence.save_world(w, p, rng=np.random.default_rng(seed))
        print("built", p, flush=True)


def stage_train(pop):
    d = os.path.join(OUT, "train", str(pop))
    os.makedirs(d, exist_ok=True)
    n = N_TRAIN[pop]
    rng = np.random.default_rng(314159 if pop == 20_000 else 271828)
    thetas = sample_prior(rng, n)
    json.dump(thetas, open(os.path.join(d, "thetas.json"), "w"))
    jobs = []
    for i, th in enumerate(thetas):
        out = os.path.join(d, f"sim_{i}.json")
        if os.path.exists(out):
            continue
        world = f"genesis:{3000+i}" if pop == 20_000 else \
            os.path.join(os.environ.get("EARTH1_SBI_WORLDS",
                                        os.path.join(OUT, "worlds")),
                         f"w200000_{5100 + i % 40}.pkl")
        jobs.append([PY, WORKER, json.dumps(th), str(pop), str(DAYS),
                     world, str((2000 if pop == 20_000 else 5000) + i), out])
    _pool(jobs)
    print("TRAIN COMPLETE", pop)


def stage_plant():
    os.makedirs(SEALED, exist_ok=True)
    sf = os.path.join(SEALED, "theta_star_v1.json")
    if not os.path.exists(sf):
        seed = int.from_bytes(os.urandom(8), "big")     # OS entropy (A6)
        rng = np.random.default_rng(seed)
        stars = sample_prior(rng, M_EXAMS)
        json.dump({"seed": seed, "stars": stars}, open(sf, "w"))
        os.chmod(sf, 0o400)
    h = hashlib.sha256(open(sf, "rb").read()).hexdigest()
    print("SEALED_SHA256", h)
    # y_obs sims, sealed mode (no theta in outputs)
    jobs = []
    for m in range(M_EXAMS):
        tf = os.path.join(SEALED, f"theta_star_m{m}.json")
        if not os.path.exists(tf):
            stars = json.load(open(sf))["stars"]
            json.dump(stars[m], open(tf, "w"))
    pops = tuple(int(x) for x in os.environ.get(
        "EARTH1_SBI_POPS", "20000,200000").split(","))
    for pop in pops:
        d = os.path.join(OUT, "yobs", str(pop))
        os.makedirs(d, exist_ok=True)
        for m in range(M_EXAMS):
            for s in OBS_SEEDS:
                out = os.path.join(d, f"exam{m}_obs{s}.json")
                if os.path.exists(out):
                    continue
                world = f"genesis:{s}" if pop == 20_000 else \
                    os.path.join(os.environ.get("EARTH1_SBI_WORLDS",
                                                os.path.join(OUT, "worlds")),
                                 f"w200000_{s}.pkl")
                jobs.append([PY, WORKER,
                             os.path.join(SEALED, f"theta_star_m{m}.json"),
                             str(pop), str(DAYS), world, str(s), out,
                             "sealed"])
    _pool(jobs)
    print("YOBS COMPLETE")


def _load_train(pop, keys):
    d = os.path.join(OUT, "train", str(pop))
    thetas = json.load(open(os.path.join(d, "thetas.json")))
    S, U_rows = [], []
    for i in range(N_TRAIN[pop]):
        j = json.load(open(os.path.join(d, f"sim_{i}.json")))
        S.append([j["summaries"][k] for k in keys])
        U_rows.append(thetas[i])
    return np.array(S), to_u(U_rows)


def stage_infer(pop):
    sets = json.load(open(os.path.join(OUT, "summary_sets_frozen.json")))
    keys = sets["S20"] if pop == 20_000 else sets["S200"]
    S, U = _load_train(pop, keys)
    n_fit = len(S) - N_SBC
    mu, sd = zscore_fit(S[:n_fit])
    methods = [ABC(), NPE(), NRE()]
    out = {"pop": pop, "keys": keys, "methods": {}}
    rng = np.random.default_rng(97)
    for meth in methods:
        t0 = time.time()
        meth.fit(S[:n_fit], U[:n_fit], mu, sd)
        # SBC + coverage on the held-out 200
        ranks = np.zeros((N_SBC, len(NAMES)), int)
        cover = np.zeros(len(NAMES))
        width = np.zeros(len(NAMES))
        for i in range(N_SBC):
            post = meth.posterior(S[n_fit + i], n=200, rng=rng)
            ranks[i] = (post < U[n_fit + i]).sum(0)
            lo, hi = np.percentile(post, [5, 95], axis=0)
            cover += (lo <= U[n_fit + i]) & (U[n_fit + i] <= hi)
            width += post.std(0)
        # KS uniformity of ranks/201
        from scipy.stats import kstest
        sbc_p = [float(kstest((ranks[:, j] + 0.5) / 201.0, "uniform").pvalue)
                 for j in range(len(NAMES))]
        # exams
        exams = {}
        for m in range(M_EXAMS):
            posts = []
            for s in OBS_SEEDS:
                y = json.load(open(os.path.join(
                    OUT, "yobs", str(pop), f"exam{m}_obs{s}.json")))
                s_obs = np.array([y["summaries"][k] for k in keys])
                posts.append(meth.posterior(s_obs, n=200, rng=rng))
            post = np.concatenate(posts)          # equal-mix over obs seeds
            exams[m] = {"mean_u": post.mean(0).tolist(),
                        "sd_u": post.std(0).tolist(),
                        "ci90_u": np.percentile(post, [5, 95], 0).tolist(),
                        "corr_hg_if": float(np.corrcoef(
                            post[:, 4], post[:, 5])[0, 1])}
        out["methods"][meth.name] = {
            "fit_seconds": round(time.time() - t0, 1),
            "sbc_ks_p": dict(zip(NAMES, np.round(sbc_p, 4))),
            "coverage90": dict(zip(NAMES, np.round(cover / N_SBC, 3))),
            "mean_post_sd_u": dict(zip(NAMES, np.round(width / N_SBC, 4))),
            "exams": exams}
        print("method done", meth.name, flush=True)
    json.dump(out, open(os.path.join(OUT, f"infer_{pop}.json"), "w"),
              indent=1)
    print("INFER COMPLETE", pop)


def stage_score():
    from earth1.dataroles import open_data
    with open_data(os.environ.get("EARTH1_SBI_SEALED_NAME",
                                  "sbi_theta_star_v1"),
                   "final_scoring") as f:
        stars = json.load(f)["stars"]
    U_star = to_u(stars)
    sens = json.load(open(os.path.join(OUT, "screen_report.json")))
    report = {"prereg": "THREE_TRACK_PREREG_v1 A9 + A4.1"}
    pops = tuple(int(x) for x in os.environ.get(
        "EARTH1_SBI_POPS", "20000,200000").split(","))
    for pop in pops:
        inf = json.load(open(os.path.join(OUT, f"infer_{pop}.json")))
        ptab = sens["pops"][str(pop)]
        res = {}
        for name_m, md in inf["methods"].items():
            per = {}
            for j, name in enumerate(NAMES):
                uninf = ptab[name]["OBSERVATION_UNINFORMATIVE"]
                hits = 0
                for m in range(M_EXAMS):
                    lo, hi = (md["exams"][str(m)]["ci90_u"][0][j],
                              md["exams"][str(m)]["ci90_u"][1][j])
                    hits += int(lo <= U_star[m, j] <= hi)
                sbc_ok = md["sbc_ks_p"][name] > 0.01
                cov_ok = 0.85 <= md["coverage90"][name] <= 0.95
                mean_sd = np.mean([md["exams"][str(m)]["sd_u"][j]
                                   for m in range(M_EXAMS)])
                false_conf = uninf and (mean_sd < 0.8 * PRIOR_SD_U)
                if uninf:
                    verdict = "OBSERVATION_DESIGN_FAILURE"
                elif hits >= 4 and sbc_ok and cov_ok:
                    verdict = "RECOVERED"
                else:
                    verdict = "ESTIMATOR_FAILURE"
                per[name] = {"exam_hits": f"{hits}/5", "sbc_ok": sbc_ok,
                             "cov": md["coverage90"][name],
                             "mean_post_sd_u": round(float(mean_sd), 3),
                             "false_confidence": bool(false_conf),
                             "verdict": verdict}
            res[name_m] = per
        report[str(pop)] = res
    json.dump(report, open(os.path.join(OUT, "battery_verdicts.json"), "w"),
              indent=1)
    print(json.dumps(report, indent=1)[:2000])


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "worlds200":
        stage_worlds200(*(int(x) for x in sys.argv[2:4])) \
            if len(sys.argv) > 2 else stage_worlds200()
    elif a == "train":
        stage_train(int(sys.argv[2]))
    elif a == "plant":
        stage_plant()
    elif a == "infer":
        stage_infer(int(sys.argv[2]))
    elif a == "score":
        stage_score()
