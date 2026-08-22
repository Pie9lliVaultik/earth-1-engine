"""F1/F2 decision artifact: production ridge vs estimator B (restored
sim_solver objective, lam=0.01) at 200K on PINNED folds x 3 seeds."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["EARTH1_PINNED_FOLDS"] = "data/cv_folds.json"
from earth1.genesis import genesis
from earth1.legacy_benchmark import run_goqa_benchmark

gt = json.load(open("data/benchmark/goqa_ground_truth.json"))
civ = genesis(200000, 42)
out = {}
for name, env, lam in (("production", "", 0.1), ("estimatorB", "aggregated", 0.01)):
    os.environ["EARTH1_ESTIMATOR"] = env
    rows = []
    for s in (42, 7, 13):
        r = run_goqa_benchmark(civ, gt, ridge_alpha=lam, cv_seed=s)
        rows.append({"cv_seed": s, "cv_mae": r.engine_cv_mae,
                     "naive": r.naive_cv_mae, "wins": r.engine_wins})
        print(f"{name} seed {s}: {r.engine_cv_mae:.4f} ({r.engine_wins}/40)", flush=True)
    maes = [x["cv_mae"] for x in rows]
    out[name] = {"rows": rows, "mean": sum(maes)/3,
                 "spread": max(maes)-min(maes), "lam": lam}
json.dump(out, open("data/estimator_comparison.json", "w"), indent=1)
d = (out["production"]["mean"] - out["estimatorB"]["mean"]) * 100
print(f"ESTIMATOR-VERDICT: production {out['production']['mean']:.4f} vs "
      f"B {out['estimatorB']['mean']:.4f} | B better by {d:+.2f}pp "
      f"(mean over 3 pinned fold seeds)", flush=True)
