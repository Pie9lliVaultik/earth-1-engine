"""0.8-A1 — force-field state census. No simulation; pure reading.

    python3 scripts/force_census.py <snapshot_dir|GENESIS> [label]

GENESIS births a fresh 200k world (seed 8801) for the contrast column.
Output: data/force_census_<label>.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def census(w) -> dict:
    from earth1.types import Force
    civ = w.civ
    alive = w.health.alive
    f = civ.forces[alive].astype(np.float64)
    out = {"day": int(w.day), "alive": int(alive.sum()), "channels": {}}
    for ch in Force:
        x = f[:, ch]
        out["channels"][ch.name] = {
            "mean": round(float(x.mean()), 5),
            "sd": round(float(x.std()), 5),
            "deciles": [round(float(v), 4) for v in
                        np.percentile(x, range(10, 100, 10))],
            "pole_share": round(float((x > 0.5).mean()), 5),
            "sat_hi": round(float((x > 0.95).mean()), 5),
            "sat_lo": round(float((x < 0.05).mean()), 5),
        }
    a = civ.alpha[alive].astype(np.float64)
    out["alpha"] = {
        "mean": round(float(a.mean()), 5),
        "sd": round(float(a.std()), 5),
        "frac_gt_0.9": round(float((a > 0.9).mean()), 5),
        "frac_gt_0.99": round(float((a > 0.99).mean()), 5),
        "deciles": [round(float(v), 4) for v in
                    np.percentile(a, range(10, 100, 10))],
    }
    for t in ("openness", "doubt", "desire_intensity"):
        arr = getattr(civ, t, None)
        if arr is not None:
            x = arr[alive].astype(np.float64)
            out[t] = {"mean": round(float(x.mean()), 5),
                      "sd": round(float(x.std()), 5),
                      "sat_hi": round(float((x > 0.95).mean()), 5),
                      "sat_lo": round(float((x < 0.05).mean()), 5)}
    return out


def main():
    src, label = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2
                               else "snapshot")
    if src == "GENESIS":
        from earth1.alive import birth_world
        w = birth_world(200_000, 8801)
    else:
        from earth1 import persistence
        d = Path(src)
        adj = d / "adj.npz"
        w, _r, _i = persistence.load_world(
            d / "world.pkl", adj_path=(adj if adj.exists() else None))
    out = census(w)
    out["source"] = src
    path = ROOT / "data" / f"force_census_{label}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("day", "alive")}, indent=None))
    for name, c in out["channels"].items():
        print(f"  {name:12s} mean {c['mean']:.4f} sd {c['sd']:.4f} "
              f"pole {c['pole_share']:.3f} sat_hi {c['sat_hi']:.3f} "
              f"sat_lo {c['sat_lo']:.3f}")
    print(f"  {'ALPHA':12s} mean {out['alpha']['mean']:.4f} "
          f">0.9: {out['alpha']['frac_gt_0.9']:.3f} "
          f">0.99: {out['alpha']['frac_gt_0.99']:.3f}")
    print(f"-> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
