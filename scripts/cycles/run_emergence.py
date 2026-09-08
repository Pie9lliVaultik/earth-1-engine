"""Social-emergence experiment runner — EMERGENCE_PREREG.md is normative.

Modes:
  ... worker CONFIG SHOCK SEED    one run (config: intact|notrans|rewired;
                                  shock: warm|cold)
  ... orchestrate [concurrency]   all 24 runs
  ... score                       registered scoring, only after all runs

The judge (real protest events after 2010-12-16) is the already-opened
DEV artifact of the scored battery row; see the prereg's estate
declaration.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

T = "2010-12-16"
SEEDS = [4242, 5151, 6363, 7777]
CONFIGS = ["intact", "notrans", "rewired"]
POP = 200_000
WARM = 90
OUT = os.path.join(ROOT, "data", "cycles", "emergence")


def _freeze_env():
    env = {}
    for line in open(os.path.join(ROOT, "scripts", "env", "freeze09.env")):
        line = line.strip()
        if line.startswith("export ") and "=" in line:
            k, v = line[len("export "):].split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _post_birth(config, seed):
    if config != "rewired":
        return None
    def hook(w):
        from scripts.emergence.rewire_graph import rewire_world_graph
        rewire_world_graph(w, seed)
    return hook


def _fields(w):
    import numpy as np
    from earth1.consequences import snapshot
    from earth1.genesis import census_weights
    from earth1.poverty import poverty_profile
    s = snapshot(w)
    cw = census_weights(w.civ)
    alive = w.health.alive
    life = w.life
    lf = life.in_lf & alive
    p = poverty_profile(w)
    return {
        "hungry_by_country": s.get("hungry_by_country"),
        "fear_by_country": s.get("fear_by_country"),
        # registered negative control: the material board
        "pov_830": p.get("poverty_830_2021ppp_headcount"),
        "median_income": p.get("median_income_day"),
        "unemployment": float((cw * (~life.employed & lf)).sum()
                              / max((cw * lf).sum(), 1e-9)),
    }


def _nfc(w, seed):
    import numpy as np
    m = w.fabric.adj.tocoo()
    alive = w.health.alive
    ok = alive[m.row] & alive[m.col] & (m.row < m.col)
    rows, cols = m.row[ok], m.col[ok]
    if rows.size == 0:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.choice(rows.size, size=min(20000, rows.size), replace=False)
    f = w.civ.forces
    out = {}
    for ch in range(f.shape[1]):
        a, b = f[rows[idx], ch], f[cols[idx], ch]
        out[str(ch)] = (float(np.corrcoef(a, b)[0, 1])
                        if a.std() > 1e-9 and b.std() > 1e-9 else None)
    return out


def worker(config, shock, seed):
    import numpy as np
    from earth1.configstamp import stamp
    from earth1.persistence import world_hash
    t0 = time.time()
    hook = _post_birth(config, seed)
    if shock == "warm":
        from earth1.historical import birth_at
        w, vintage = birth_at(T, POP, seed, warm_days=WARM, post_birth=hook)
    else:
        from earth1.alive import birth_world, live_one_day
        w = birth_world(POP, seed, substrate="c2plus_v1")
        if hook:
            hook(w)
        rng = np.random.default_rng(seed)
        for _ in range(WARM):
            live_one_day(w, rng)
        vintage = {"cold_control": True}
    rec = {"config": config, "shock": shock, "seed": seed, "T": T,
           "pop": POP, "warm_days": WARM,
           "env": {k: v for k, v in os.environ.items()
                   if k.startswith("EARTH1_")},
           "stamp": stamp(), "day_end_hash": world_hash(w),
           "vintage": vintage, "fields": _fields(w),
           "nfc": _nfc(w, seed),
           "wall_seconds": round(time.time() - t0, 1)}
    out = os.path.join(OUT, f"{config}_{shock}_{seed}.json")
    json.dump(rec, open(out, "w"), indent=1)
    print(f"[emg] {config}/{shock}/{seed} done in {rec['wall_seconds']}s",
          flush=True)


def orchestrate(concurrency=3):
    os.makedirs(OUT, exist_ok=True)
    jobs = [(c, sh, s) for c in CONFIGS for sh in ("warm", "cold")
            for s in SEEDS]
    base_env = {k: v for k, v in os.environ.items()
                if not k.startswith("EARTH1_")}
    freeze = _freeze_env()
    running = []
    while jobs or running:
        while jobs and len(running) < concurrency:
            c, sh, s = jobs.pop(0)
            env = dict(base_env); env.update(freeze)
            if os.environ.get("EARTH1_GDELT_DIR"):
                env["EARTH1_GDELT_DIR"] = os.environ["EARTH1_GDELT_DIR"]
            if c == "notrans":
                env["EARTH1_SOCIAL_TRANSMISSION"] = "off"
            env["PYTHONPATH"] = ROOT
            p = subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "worker",
                 c, sh, str(s)], env=env, cwd=ROOT)
            running.append((p, c, sh, s))
            print(f"[emg] launched {c}/{sh}/{s} ({len(jobs)} queued)",
                  flush=True)
        for p, c, sh, s in list(running):
            if p.poll() is not None:
                running.remove((p, c, sh, s))
                st = "OK" if p.returncode == 0 else f"RC={p.returncode}"
                print(f"[emg] finished {c}/{sh}/{s} {st}", flush=True)
        time.sleep(5)
    print("[emg] EMERGENCE RUNS COMPLETE", flush=True)


def score():
    """Registered scoring — EMERGENCE_PREREG.md 'Registered outcomes'."""
    import numpy as np
    from scipy.stats import spearmanr
    judge = json.load(open(os.path.join(
        ROOT, "ops", "alive", "historical", "arab_spring_scored.json")))
    runs = {}
    for fn in os.listdir(OUT):
        if fn.endswith(".json"):
            r = json.load(open(os.path.join(OUT, fn)))
            runs[(r["config"], r["shock"], r["seed"])] = r
    missing = [(c, sh, s) for c in CONFIGS for sh in ("warm", "cold")
               for s in SEEDS if (c, sh, s) not in runs]
    if missing:
        print("REFUSING TO SCORE — missing runs:", missing)
        return
    # judge: normalized protest events per country (forward-only rule)
    ev = judge.get("events_by_country_normalized") or \
        judge.get("events_by_country") or {}
    from earth1.genesis import GENESIS_COUNTRY_CODES
    iso_order = list(GENESIS_COUNTRY_CODES)
    y = np.array([ev.get(i, np.nan) for i in iso_order], dtype=float)
    res = {"prereg": "ops/alive/cycles/EMERGENCE_PREREG.md",
           "judge_keys": len(ev), "per_config": {}, "paired": {}}
    rhos = {}
    for c in CONFIGS:
        per_seed = {"delta_hunger": [], "raw_hunger": [], "delta_fear": []}
        for s in SEEDS:
            warm, cold = runs[(c, "warm", s)], runs[(c, "cold", s)]
            for field, key in (("hungry_by_country", "hunger"),
                               ("fear_by_country", "fear")):
                fw = np.array(warm["fields"][field], dtype=float)
                fc = np.array(cold["fields"][field], dtype=float)
                d = fw - fc
                ok = ~np.isnan(y) & ~np.isnan(d)
                per_seed[f"delta_{key}"].append(
                    float(spearmanr(d[ok], y[ok]).statistic))
                if key == "hunger":
                    okr = ~np.isnan(y) & ~np.isnan(fw)
                    per_seed["raw_hunger"].append(
                        float(spearmanr(fw[okr], y[okr]).statistic))
        rhos[c] = per_seed
        res["per_config"][c] = {k: {"per_seed": v,
                                    "mean": float(np.mean(v)),
                                    "se": float(np.std(v, ddof=1)
                                                / np.sqrt(len(v)))}
                                for k, v in per_seed.items()}
    for name, a, b in (("H1_intact_vs_notrans", "intact", "notrans"),
                       ("H2_intact_vs_rewired", "intact", "rewired")):
        da = np.array(rhos[a]["delta_hunger"])
        db = np.array(rhos[b]["delta_hunger"])
        diff = da - db
        res["paired"][name] = {
            "per_seed_diff": diff.tolist(),
            "mean_diff": float(diff.mean()),
            "se": float(diff.std(ddof=1) / np.sqrt(len(diff))),
            "wins": int((diff > 0).sum()),
            "pass": bool((diff > 0).sum() >= 3
                         and diff.mean() > diff.std(ddof=1)
                         / np.sqrt(len(diff)))}
    # registered negative control
    nc = {}
    for k in ("pov_830", "unemployment", "median_income"):
        vals = {c: [runs[(c, "warm", s)]["fields"][k] for s in SEEDS]
                for c in ("intact", "notrans")}
        di = np.array(vals["intact"]) - np.array(vals["notrans"])
        sd = np.std(np.array(vals["intact"]), ddof=1)
        nc[k] = {"mean_diff": float(di.mean()),
                 "intact_seed_sd": float(sd),
                 "within_2sigma": bool(abs(di.mean()) <= 2 * max(sd, 1e-12))}
    res["negative_control"] = nc
    out = os.path.join(OUT, "EMERGENCE_SCORED.json")
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("paired", "negative_control")},
                     indent=1))
    print("scored ->", out)


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "worker":
        worker(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    elif m == "score":
        score()
    else:
        orchestrate(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
