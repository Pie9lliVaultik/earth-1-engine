"""Sensitivity pre-screen on INDEPENDENT design worlds (prereg A4/A5).

theta* does not exist yet; nothing here touches or creates it.
Stages:
  worlds <pop>   build design worlds (CRN seeds 101,103,107 + noise 111..120)
  run <pop>      49 sims: 13 OAT configs x 3 CRN seeds + canonical x 10 noise
  score          sensitivity per A4, fidelity classification per A5,
                 hard KA-2 assertions for critical_fraction & memory_press
                 at 200k (HARNESS BROKEN => exit 2, screen VOID)
"""
import itertools
import json
import os
import subprocess
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sbi.theta import CANONICAL, NAMES, prior_ppf  # noqa: E402

OUT = "/opt/earth1-data/sbi"
CRN_SEEDS = (101, 103, 107)
NOISE_SEEDS = tuple(range(111, 121))
DAYS = 90
SLOTS = 30
POPS = (20_000, 200_000)


def configs():
    yield "canonical", dict(CANONICAL)
    for name in NAMES:
        for tag, q in (("p10", 0.1), ("p90", 0.9)):
            th = dict(CANONICAL)
            th[name] = prior_ppf(name, q)
            yield f"{name}_{tag}", th


def world_path(pop, seed):
    return os.path.join(OUT, "worlds", f"w{pop}_{seed}.pkl")


def stage_worlds(pop):
    os.makedirs(os.path.join(OUT, "worlds"), exist_ok=True)
    from earth1 import persistence
    from earth1.alive import birth_world
    for seed in CRN_SEEDS + NOISE_SEEDS:
        p = world_path(pop, seed)
        if os.path.exists(p):
            print("exists", p); continue
        t0 = time.time()
        w = birth_world(pop, seed)
        persistence.save_world(w, p, rng=np.random.default_rng(seed))
        print("built", p, f"{time.time()-t0:.0f}s", flush=True)


def stage_run(pop):
    d = os.path.join(OUT, "screen", str(pop))
    os.makedirs(d, exist_ok=True)
    jobs = []
    for cfg, th in configs():
        for seed in CRN_SEEDS:
            jobs.append((cfg, th, seed))
    for seed in NOISE_SEEDS:
        jobs.append(("canonical", dict(CANONICAL), seed))
    procs = []
    for cfg, th, seed in jobs:
        out = os.path.join(d, f"{cfg}_{seed}.json")
        if os.path.exists(out):
            continue
        while len([p for p in procs if p.poll() is None]) >= SLOTS:
            time.sleep(2)
        procs.append(subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "scripts/sbi/sim_worker.py"),
             json.dumps(th), str(pop), str(DAYS),
             world_path(pop, seed), str(seed), out]))
    for p in procs:
        p.wait()
    bad = [p.returncode for p in procs if p.returncode]
    print("RUN COMPLETE", pop, "failures:", len(bad))
    if bad:
        sys.exit(1)


def _load(pop):
    d = os.path.join(OUT, "screen", str(pop))
    runs = {}
    for f in os.listdir(d):
        if f.endswith(".json"):
            j = json.load(open(os.path.join(d, f)))
            cfg, seed = f[:-5].rsplit("_", 1)
            runs[(cfg, int(seed))] = j["summaries"]
    return runs


def stage_score():
    report = {"registered": "THREE_TRACK_PREREG_v1 A4/A5", "pops": {}}
    sens = {}   # (pop, name, summary) -> standardized effect (median pairedD / sd)
    skeys = None
    for pop in POPS:
        runs = _load(pop)
        skeys = sorted(next(iter(runs.values())).keys())
        canon = {s: np.array([runs[("canonical", seed)][s]
                              for seed in CRN_SEEDS + NOISE_SEEDS])
                 for s in skeys}
        sd = {s: max(float(canon[s].std(ddof=1)), 1e-12) for s in skeys}
        ptab = {}
        for name in NAMES:
            row = {}
            for s in skeys:
                best = 0.0
                for tag in ("p10", "p90"):
                    deltas = [runs[(f"{name}_{tag}", seed)][s]
                              - runs[("canonical", seed)][s]
                              for seed in CRN_SEEDS]
                    z = float(np.median(deltas)) / sd[s]
                    if abs(z) > abs(best):
                        best = z
                row[s] = round(best, 3)
                sens[(pop, name, s)] = best
            sensitive = {s: z for s, z in row.items() if abs(z) > 2.0}
            ptab[name] = {"n_sensitive": len(sensitive),
                          "top": dict(sorted(sensitive.items(),
                                             key=lambda kv: -abs(kv[1]))[:8]),
                          "OBSERVATION_UNINFORMATIVE": not sensitive}
        report["pops"][str(pop)] = ptab
    # A5 fidelity classification per summary
    cls = {}
    for s in skeys:
        verdict = "TRANSFER_SAFE_AT_20K"
        reasons = []
        for name in NAMES:
            z200 = sens[(200_000, name, s)]
            z20 = sens[(20_000, name, s)]
            if abs(z200) > 2.0:
                if abs(z20) <= 2.0:
                    verdict = "REQUIRES_200K"; reasons.append(f"{name}: 20k insensitive")
                elif np.sign(z20) != np.sign(z200):
                    verdict = "REQUIRES_200K"; reasons.append(f"{name}: sign flip")
                elif not (1/3 <= abs(z20)/abs(z200) <= 3):
                    verdict = "REQUIRES_200K"; reasons.append(f"{name}: ratio {abs(z20)/abs(z200):.2f}")
        if s == "cum_cascades" and verdict == "TRANSFER_SAFE_AT_20K":
            # default REQUIRES_200K unless the paired test proved it (it did if we got here)
            reasons.append("cascade summary: paired test passed, default overridden by evidence")
        cls[s] = {"class": verdict, "reasons": reasons}
    report["fidelity"] = cls
    # HARD KA-2 (Standing Rule 2): the two scale-gated thetas must move
    # something at 200k, else the harness cannot be trusted.
    for name in ("critical_fraction", "memory_press"):
        if report["pops"]["200000"][name]["OBSERVATION_UNINFORMATIVE"]:
            print(f"HARNESS BROKEN OR OBSERVATION DESIGN DEAD: {name} moved "
                  f"nothing at 200k. SCREEN VOID pending diagnosis.")
            json.dump(report, open(os.path.join(OUT, "screen_VOID.json"), "w"), indent=1)
            sys.exit(2)
    json.dump(report, open(os.path.join(OUT, "screen_report.json"), "w"), indent=1)
    s20 = [s for s, v in cls.items() if v["class"] == "TRANSFER_SAFE_AT_20K"]
    s200 = [s for s in skeys
            if any(abs(sens[(200_000, n, s)]) > 2.0 for n in NAMES)]
    json.dump({"S20": sorted(set(s20) & set(s200)), "S200": sorted(s200)},
              open(os.path.join(OUT, "summary_sets_frozen.json"), "w"), indent=1)
    print("SCORED. S20:", len(set(s20) & set(s200)), "S200:", len(s200))


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "worlds":
        stage_worlds(int(sys.argv[2]))
    elif stage == "run":
        stage_run(int(sys.argv[2]))
    elif stage == "score":
        stage_score()
