"""0.8 IT9 — two-timescale persistence (frozen: IT9_TWO_TIMESCALE.md).
ARMS override on the IT6 engine (additive `lam` key). KA3-5 measured
via dedicated arms/forks; sustained-exposure fork handled here for
KA5 by a second scored quantity on the CAND arm's world."""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
import multiprocessing as mp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.it6_dyadic as it6  # noqa: E402

D = dict
S = 8901
BASE = D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
         k=3, mu=0.0167, seed=S)
it6.ARMS = {
    "CAND":        D(**BASE, lam=0.1072),
    "KA1_lam0":    D(**BASE, lam=0.0),
    "KA2_lam10x":  D(**BASE, lam=1.072),
    "KA_zero":     D(op="zero", cnv="dy", flr=True, cas=True,
                     relax=0.045, seed=S, lam=0.1072),
    "KA_instant":  D(op="instant", cnv="dy", flr=True, cas=True,
                     relax=0.045, seed=S, lam=0.1072),
    "KA_pull":     D(**{**BASE, "relax": 0.60}, lam=0.1072),
    "KA_frozen":   D(**{**BASE, "relax": 0.005}, lam=0.1072),
    "KA_degtgt":   D(**BASE, lam=0.1072, extra="degtgt"),
    "KA_fastmix":  D(**BASE, lam=0.1072, extra="fastmix"),
    "KA_ratchet":  D(**{**BASE, "cnv": "inc"}, lam=0.1072),
    "KAdis_soften": D(**BASE, lam=0.1072, forced=-0.5),
    "KAdis_harden": D(**BASE, lam=0.1072, forced=+0.5),
    "KAdis_mf":    D(**{**BASE, "cnv": "meanfield"}, lam=0.1072,
                     forced=-0.5),
}
OUT = Path(os.environ.get("EARTH1_IT9_OUT",
                          str(ROOT / "data" / "it9")))


def _worker(name):
    import scripts.it9_two_timescale  # noqa: F401
    import scripts.it6_dyadic as engine
    return engine.run_arm(name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(13, len(it6.ARMS))) as pool:
        for r in pool.imap_unordered(_worker, list(it6.ARMS)):
            results.append(r)
            p = r["panels"].get(str(it6.DAYS), {})
            t_ = r["tau"] or {}
            tr = r["transmission"] or {}
            print(f"  [{len(results):2d}/{len(it6.ARMS)}] "
                  f"{r['arm']:13s} tau {t_.get('half_life_d')} "
                  f"res {t_.get('resid_d30')} "
                  f"db {t_.get('baseline_shift_d30')} "
                  f"fb {t_.get('frac_carried_by_baseline')} "
                  f"r1 {tr.get('ring1_d30')} "
                  f"a {p.get('alpha_mean')} sat {p.get('sat_max')} "
                  f"sdr {p.get('sd_ratio_genesis')}", flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT9 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
