"""Official benchmark runner (one ontology). Loads the canonical world
from EARTH1_ALIVE_HOME (via api.deps.get_world) or births a dev world
(--birth N --seed S), runs earth1.benchmark_living, writes JSON with
provenance. UNCALIBRATED until Benchmark A (Phase 1)."""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--birth", type=int, default=0,
                    help="dev: birth a world of N instead of loading")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--days", type=int, default=0)
    ap.add_argument("--out", default=str(ROOT / "data" /
                                         "benchmark_living.json"))
    a = ap.parse_args()
    if a.birth:
        import numpy as np
        from earth1.alive import birth_world, live_one_day
        w = birth_world(a.birth, a.seed)
        rng = np.random.default_rng(a.seed)
        for _ in range(a.days):
            live_one_day(w, rng)
        source = f"birth_world({a.birth}, {a.seed}) + {a.days}d"
    else:
        from earth1.api.deps import get_world
        w, identity = get_world()
        source = identity.get("source")
    from earth1.benchmark_living import run
    rep = run(w)
    rep["world_source"] = source
    Path(a.out).write_text(json.dumps(rep, indent=1, default=str))
    print(f"benchmark_living: {rep['n_questions']} questions, "
          f"MAE(uncalibrated) {rep['mae_global_uncalibrated']:.4f}, "
          f"physics {rep['provenance']['physics_version']}, "
          f"world {rep['provenance']['world_hash'][:12]} -> {a.out}")


if __name__ == "__main__":
    main()
