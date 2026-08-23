"""0.8 IT10 — high-dose two-timescale integration (frozen:
IT10_HIGH_DOSE_TWO_TIMESCALE.md). One scored candidate."""
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
S = 8902                       # fresh scored seed, never used before
LAM = 0.1072
BASE = D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
         k=3, mu=0.05, seed=S)
it6.ARMS = {
    "CAND":       D(**BASE, lam=LAM, rich=True),
    "KA0_cont":   D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045,
                    k=3, mu=0.05, lam=0.0),          # seed 8890 default
    "KA1_lam0":   D(**BASE, lam=0.0),
    "KA3_lam10":  D(**BASE, lam=1.072, rich=True),
    "KA_zero":    D(op="zero", cnv="dy", flr=True, cas=True,
                    relax=0.045, seed=S, lam=LAM),
    "KA_instant": D(op="instant", cnv="dy", flr=True, cas=True,
                    relax=0.045, seed=S, lam=LAM),
    "KA_pull":    D(**{**BASE, "relax": 0.60}, lam=LAM),
    "KA_frozen":  D(**{**BASE, "relax": 0.005}, lam=LAM),
    "KA_degtgt":  D(**BASE, lam=LAM, extra="degtgt"),
    "KA_fastmix": D(**BASE, lam=LAM, extra="fastmix"),
    "KA_ratchet": D(**{**BASE, "cnv": "inc"}, lam=LAM),
    "KAdis_soften": D(**BASE, lam=LAM, forced=-0.5),
    "KAdis_harden": D(**BASE, lam=LAM, forced=+0.5),
    "KAdis_mf":   D(**{**BASE, "cnv": "meanfield"}, lam=LAM,
                    forced=-0.5),
}
OUT = Path(os.environ.get("EARTH1_IT10_OUT",
                          str(ROOT / "data" / "it10")))


def _worker(name):
    import scripts.it10_integration  # noqa: F401
    import scripts.it6_dyadic as engine
    return engine.run_arm(name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    results = []
    ctx = mp.get_context("spawn")
    with ctx.Pool(processes=min(14, len(it6.ARMS))) as pool:
        for r in pool.imap_unordered(_worker, list(it6.ARMS)):
            results.append(r)
            p = r["panels"].get(str(it6.DAYS), {})
            t_ = r["tau"] or {}
            tr = r["transmission"] or {}
            print(f"  [{len(results):2d}/{len(it6.ARMS)}] "
                  f"{r['arm']:12s} tau {t_.get('half_life_d')} "
                  f"res {t_.get('resid_d30')} "
                  f"live {t_.get('live_resid_d30')} "
                  f"db {t_.get('baseline_shift_d30')} "
                  f"r1 {tr.get('ring1_d30')} r3 {tr.get('ring3_d30')} "
                  f"a {p.get('alpha_mean')} sat {p.get('sat_max')} "
                  f"sdr {p.get('sd_ratio_genesis')} "
                  f"rich {r.get('rich_forks')}", flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT10 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
