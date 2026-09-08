"""v1.1 factorial runner — REHOME_CLAMP_PREREG.md is normative.

Modes:
  python3 scripts/cycles/run_v11_factorial.py worker ARM SEED   (one run)
  python3 scripts/cycles/run_v11_factorial.py orchestrate       (all 16)

Arms: base (no fix flags), urban (U), clamp (C), both (U+C) — each on
top of the freeze-0.9 base flags. Worker runs in a FRESH process with
its arm's env so import-bound physics is correct (configstamp M02a).
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

SEEDS = [4242, 5151, 6363, 7777]
ARMS = {"base": {}, "urban": {"EARTH1_URBAN_AXIS_FIX": "on"},
        "clamp": {"EARTH1_REHOME_LOCAL_CLAMP": "1"},
        "both": {"EARTH1_URBAN_AXIS_FIX": "on",
                 "EARTH1_REHOME_LOCAL_CLAMP": "1"}}
SNAP_DAYS = {30, 60, 90, 120, 150, 180}
HORIZON = 180
POP = 200_000
OUT = os.path.join(ROOT, "data", "cycles", "v11")
TYPES = ("household", "neighbours", "colleagues", "friends", "weak", "media")


def _freeze_env():
    env = {}
    for line in open(os.path.join(ROOT, "scripts", "env", "freeze09.env")):
        line = line.strip()
        if line.startswith("export ") and "=" in line:
            k, v = line[len("export "):].split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _tie_stats(w):
    import numpy as np
    out = {}
    for name in TYPES:
        m = w.fabric.by_type.get(name)
        if m is None:
            continue
        d = m.data[m.data > 0]
        if d.size == 0:
            out[name] = {"edges": 0}
            continue
        deg = np.diff(m.indptr)
        out[name] = {
            "edges": int(m.nnz), "w_mean": float(d.mean()),
            "w_p10": float(np.percentile(d, 10)),
            "w_p50": float(np.percentile(d, 50)),
            "w_p90": float(np.percentile(d, 90)),
            "w_p99": float(np.percentile(d, 99)),
            "deg_mean": float(deg.mean()),
            "deg_p90": float(np.percentile(deg, 90))}
    return out


def _neighbour_force_corr(w, n_edges=20000, seed=0):
    """Mean Pearson r over sampled live edges, per force channel."""
    import numpy as np
    m = w.fabric.adj.tocoo()
    alive = w.health.alive
    ok = alive[m.row] & alive[m.col] & (m.row < m.col)
    rows, cols = m.row[ok], m.col[ok]
    if rows.size == 0:
        return None
    rng = np.random.default_rng(seed)
    idx = rng.choice(rows.size, size=min(n_edges, rows.size), replace=False)
    f = w.civ.forces
    out = {}
    for ch in range(f.shape[1]):
        a, b = f[rows[idx], ch], f[cols[idx], ch]
        sa, sb = a.std(), b.std()
        out[str(ch)] = (float(np.corrcoef(a, b)[0, 1])
                        if sa > 1e-9 and sb > 1e-9 else None)
    return out


def _board(w, watch):
    import numpy as np
    from earth1.genesis import census_weights
    from earth1.poverty import poverty_profile
    cw = census_weights(w.civ)
    alive = w.health.alive
    p = poverty_profile(w)
    life = w.life
    lf = life.in_lf & alive
    unemp = float((cw * (~life.employed & lf)).sum() / max((cw * lf).sum(), 1e-9))
    age_y = 18.0 + 72.0 * w.civ.age
    a65 = float((cw * (alive & (age_y >= 65))).sum() / max((cw * alive).sum(), 1e-9))
    # wealth concentration (weighted percentiles, alive only)
    wl = np.asarray(life.wealth, dtype=float)[alive]
    cwa = cw[alive]
    srt = np.argsort(wl)
    cum = np.cumsum(cwa[srt]) / cwa.sum()
    p50 = wl[srt][np.searchsorted(cum, 0.50)]
    p99 = wl[srt][np.searchsorted(cum, 0.99)]
    top1 = float(wl[srt][cum >= 0.99].sum() / max(wl[srt].sum(), 1e-9)) \
        if wl.sum() > 0 else None
    return {"pov_830": p.get("poverty_830_2021ppp_headcount"),
            "pov_300": p.get("poverty_300_2021ppp_headcount"),
            "median_income": p.get("median_income_day"),
            "unemployment": round(unemp, 5),
            "adult_65plus": round(a65, 5),
            "deaths_cumulative": watch.n,
            "mean_age_at_death": watch.mean_age_at_death,
            "by_cause_n": {str(k): len(v) for k, v in watch.by_cause.items()},
            "wealth_p99_over_p50": (round(float(p99 / p50), 3)
                                    if p50 and p50 > 0 else None),
            "wealth_top1_share": (round(top1, 4) if top1 is not None else None)}


def _urban_margins(w):
    """Model urban share vs table axis mass, per country (worst 10)."""
    import numpy as np
    from earth1.cohorts import tables
    from earth1.genesis import GENESIS_COUNTRY_CODES
    T = tables()
    gaps = []
    for ci, iso in enumerate(GENESIS_COUNTRY_CODES):
        tab = np.asarray(T["tables"].get(iso, []), dtype=float)
        if tab.size == 0 or tab.sum() <= 0:
            continue
        expected = float(tab[:, :, :, :, 0].sum() / tab.sum())  # axis idx 0 = urban
        m = w.civ.country == ci
        if m.sum() < 30:
            continue
        got = float(np.mean(w.civ.urban[m]))
        gaps.append((abs(got - expected), iso, round(got, 3), round(expected, 3)))
    gaps.sort(reverse=True)
    within = sum(1 for g, *_ in gaps if g <= 0.02)
    return {"countries": len(gaps), "within_2pp": within,
            "worst10": [{"iso": i, "model": g_, "census": e, "gap": round(g, 3)}
                        for g, i, g_, e in gaps[:10]]}


def worker(arm, seed):
    import numpy as np
    from earth1.alive import birth_world, live_one_day
    from earth1.configstamp import stamp
    from earth1.consequences import snapshot
    from earth1.deathwatch import DeathWatch
    from earth1.persistence import world_hash
    t0 = time.time()
    w = birth_world(POP, seed, substrate="c2plus_v1")
    watch = DeathWatch(w)
    rng = np.random.default_rng(seed * 7 + 1)
    rec = {"arm": arm, "seed": seed, "pop": POP, "horizon": HORIZON,
           "env": {k: v for k, v in os.environ.items()
                   if k.startswith("EARTH1_")},
           "stamp": stamp(), "day0_hash": world_hash(w),
           "git_head": subprocess.run(
               ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
               capture_output=True, text=True).stdout.strip(),
           "snapshots": {}}
    prev_weak_p90 = None
    collapse_sig = []
    for d in range(1, HORIZON + 1):
        live_one_day(w, rng)
        watch.observe(w)
        if d % 7 == 0 or d in SNAP_DAYS:      # weekly weak-tie watch
            ts = _tie_stats(w)
            wp90 = ts.get("weak", {}).get("w_p90")
            if prev_weak_p90 is not None and wp90 is not None:
                collapse_sig.append({"day": d,
                                     "weak_p90_drop": round(prev_weak_p90 - wp90, 5)})
            prev_weak_p90 = wp90
        if d in SNAP_DAYS:
            rec["snapshots"][str(d)] = {
                "board": _board(w, watch),
                "ties": _tie_stats(w),
                "nfc": _neighbour_force_corr(w, seed=seed),
                "sys": {k: snapshot(w).get(k) for k in
                        ("employed", "unemployed", "hungry")},
            }
    rec["urban_margins"] = _urban_margins(w)
    rec["weak_p90_weekly_drops"] = collapse_sig
    rec["migrations_note"] = "weekly rewires occur on the tick path; drops tracked above"
    rec["wall_seconds"] = round(time.time() - t0, 1)
    out = os.path.join(OUT, f"{arm}_{seed}.json")
    json.dump(rec, open(out, "w"), indent=1)
    print(f"[v11] {arm} seed {seed} done in {rec['wall_seconds']}s -> {out}",
          flush=True)


def orchestrate(concurrency=3):
    os.makedirs(OUT, exist_ok=True)
    jobs = [(a, s) for a in ARMS for s in SEEDS]
    running = []
    base_env = {k: v for k, v in os.environ.items()
                if not k.startswith("EARTH1_")}
    freeze = _freeze_env()
    while jobs or running:
        while jobs and len(running) < concurrency:
            arm, seed = jobs.pop(0)
            env = dict(base_env); env.update(freeze); env.update(ARMS[arm])
            env["PYTHONPATH"] = ROOT
            p = subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "worker",
                 arm, str(seed)], env=env, cwd=ROOT)
            running.append((p, arm, seed))
            print(f"[v11] launched {arm}/{seed} "
                  f"({len(jobs)} queued)", flush=True)
        for p, arm, seed in list(running):
            if p.poll() is not None:
                running.remove((p, arm, seed))
                status = "OK" if p.returncode == 0 else f"RC={p.returncode}"
                print(f"[v11] finished {arm}/{seed} {status}", flush=True)
        time.sleep(5)
    print("[v11] FACTORIAL COMPLETE", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "worker":
        worker(sys.argv[2], int(sys.argv[3]))
    else:
        orchestrate(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
