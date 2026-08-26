"""One SBI simulation in one process (patches stay process-local).

usage: sim_worker.py <theta_json> <pop> <days> <world_pkl> <rng_seed> <out_json>
theta_json may be a path or an inline JSON object string.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from sbi.theta import apply_theta, run_days, summarize  # noqa: E402


def main(theta_arg, pop, days, world_pkl, rng_seed, out):
    theta = json.loads(theta_arg) if theta_arg.strip().startswith("{") \
        else json.load(open(theta_arg))
    kw = apply_theta(theta)          # BEFORE any tick
    from earth1 import persistence
    w, _rs, _ = persistence.load_world(world_pkl)
    rng = np.random.default_rng(int(rng_seed))
    daily = run_days(w, rng, int(days), kw)
    json.dump({"theta": theta, "pop": int(pop), "days": int(days),
               "world_pkl": os.path.basename(world_pkl),
               "rng_seed": int(rng_seed),
               "summaries": summarize(daily),
               "daily_light": [{k: d[k] for k in
                                ("alive", "employment_rate",
                                 "destitute_share", "cum_deaths",
                                 "cum_cascades")} for d in daily]},
              open(out, "w"))
    print("SIM DONE", os.path.basename(out))


if __name__ == "__main__":
    main(*sys.argv[1:7])
