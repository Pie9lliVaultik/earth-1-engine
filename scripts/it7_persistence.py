"""0.8 IT7 — single-factor persistence confirmation (frozen:
IT7_PERSISTENCE_CONFIRMATION.md). Thin arm-table override on the IT6
engine; the engine gained an additive `forced` config key for the
designed-disagreement KA cohorts (IT6's frozen arms unaffected).
"""
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
it6.ARMS = {
    "ALL_r02":      D(op="dy", cnv="dy", flr=True, cas=True, relax=0.02),
    "ALL_r01":      D(op="dy", cnv="dy", flr=True, cas=True, relax=0.01),
    "REF_r045":     D(op="dy", cnv="dy", flr=True, cas=True,
                      relax=0.045),
    "KA_zero":      D(op="zero", cnv="dy", flr=True, cas=True,
                      relax=0.02),
    "KA_instant":   D(op="instant", cnv="dy", flr=True, cas=True,
                      relax=0.02),
    "KA_pull":      D(op="dy", cnv="dy", flr=True, cas=True, relax=0.60),
    "KA_frozen":    D(op="dy", cnv="dy", flr=True, cas=True,
                      relax=0.005),
    "KA_degtgt":    D(op="dy", cnv="dy", flr=True, cas=True, relax=0.02,
                      extra="degtgt"),
    "KA_fastmix":   D(op="dy", cnv="dy", flr=True, cas=True, relax=0.02,
                      extra="fastmix"),
    "KA_ratchet":   D(op="dy", cnv="inc", flr=True, cas=True,
                      relax=0.02),
    "KAdis_soften": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.02,
                      forced=-0.5),
    "KAdis_harden": D(op="dy", cnv="dy", flr=True, cas=True, relax=0.02,
                      forced=+0.5),
    "KAdis_mf":     D(op="dy", cnv="meanfield", flr=True, cas=True,
                      relax=0.02, forced=-0.5),
}
OUT = Path(os.environ.get("EARTH1_IT7_OUT",
                          str(ROOT / "data" / "it7")))


def _worker(name):
    import scripts.it7_persistence  # noqa: F401 (installs ARMS)
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
                  f"coh_da {r.get('cohort_dalpha')}", flush=True)
    (OUT / "arms.json").write_text(json.dumps(results, indent=1))
    print(f"\nIT7 COMPLETE {round((time.monotonic()-t0)/60, 1)} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
