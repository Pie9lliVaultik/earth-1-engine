"""0.8 IT12 — Chronicle persistence calibration (frozen:
IT12_CHRONICLE_CALIBRATION.md). ARMS override on the IT11 runner."""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.it11_carrier as it11  # noqa: E402

D = dict
SCHED = (1, 2, 4, 7, 11)
it11.ARMS = {
    "COMPOSITE":  D(event=True, half_life=10.0, followups=SCHED,
                    spread=False, seed=8904),
    "INTRINSIC":  D(event=True, half_life=10.0, spread=False,
                    seed=8904),
    "REF720":     D(event=True, half_life=720.0, spread=False,
                    seed=8904),
    "KA0_cont":   D(event=False, seed=8890),
    "KA1_delete": D(event=True, half_life=10.0, delete_after=1,
                    spread=False, seed=8904),
    "KA2_nodecay": D(event=True, half_life=float("inf"),
                     spread=False, seed=8904),
    "KA6_neg":    D(event=True, half_life=10.0, sign=-1.0,
                    spread=False, seed=8904),
}
OUT = Path(os.environ.get("EARTH1_IT12_OUT",
                          str(ROOT / "data" / "it12")))


def _worker(name):
    import scripts.it12_calibration  # noqa: F401
    import scripts.it11_carrier as engine
    return engine.run_arm(name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=len(it11.ARMS)) as pool:
        for r in pool.imap_unordered(_worker, list(it11.ARMS)):
            results.append(r)
            print(f"  [{len(results)}/{len(it11.ARMS)}] {r['arm']:10s} "
                  f"peak5 {r['peak_d5']} d30 {r['d30']} "
                  f"resid {r['resid_vs_peak']} "
                  f"carrier_sum {r.get('carrier_sum_d30')} "
                  f"sat {r['sat_check']}", flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT12 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
