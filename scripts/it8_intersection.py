"""0.8 IT8 — dose/pull intersection test (frozen:
IT8_DOSE_PULL_INTERSECTION.md). Thin ARMS override on the IT6 engine.
Fresh evaluation seed 8901 for scored candidates and KAs; REF at the
original 8890 for continuity."""
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
EVAL_SEED = 8901
it6.ARMS = {
    "A_k1mu05":  D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01,
                   k=1, mu=0.05, seed=EVAL_SEED),
    "B_k3mu017": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01,
                   k=3, mu=0.0167, seed=EVAL_SEED),
    "REF_r045":  D(op="dy", cnv="dy", flr=True, cas=True, relax=0.045),
    "KA_zero":   D(op="zero", cnv="dy", flr=True, cas=True, relax=0.01,
                   seed=EVAL_SEED),
    "KA_instant": D(op="instant", cnv="dy", flr=True, cas=True,
                    relax=0.01, seed=EVAL_SEED),
    "KA_pull":   D(op="dy", cnv="dy", flr=True, cas=True, relax=0.60,
                   k=1, mu=0.05, seed=EVAL_SEED),
    "KA_frozen": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.005,
                   k=3, mu=0.05, seed=EVAL_SEED),
    "KA_degtgt": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01,
                   k=1, mu=0.05, seed=EVAL_SEED, extra="degtgt"),
    "KA_fastmix": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01,
                    k=1, mu=0.05, seed=EVAL_SEED, extra="fastmix"),
    "KA_ratchet": D(op="dy", cnv="inc", flr=True, cas=True, relax=0.01,
                    k=1, mu=0.05, seed=EVAL_SEED),
    "KAdis_soften": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01,
                      k=1, mu=0.05, seed=EVAL_SEED, forced=-0.5),
    "KAdis_harden": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01,
                      k=1, mu=0.05, seed=EVAL_SEED, forced=+0.5),
    "KAdis_mf":   D(op="dy", cnv="meanfield", flr=True, cas=True,
                    relax=0.01, k=1, mu=0.05, seed=EVAL_SEED,
                    forced=-0.5),
}
OUT = Path(os.environ.get("EARTH1_IT8_OUT",
                          str(ROOT / "data" / "it8")))


def _worker(name):
    import scripts.it8_intersection  # noqa: F401
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
                  f"r1 {tr.get('ring1_d30')} r3 {tr.get('ring3_d30')} "
                  f"a {p.get('alpha_mean')} sat {p.get('sat_max')} "
                  f"sdr {p.get('sd_ratio_genesis')} "
                  f"dose {r.get('realized_dose')}", flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT8 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
