#!/usr/bin/env python3
"""G5 run #10 — the FULL gate on the FROZEN architecture (commit 4147de4).

The first measurement-era run: all three legs, canonical heartbeat,
One Law physics (E1-0.4), on the exact binary the API serves. Event-leg
distribution metrics (per-country MAE vs uniform-shift, variance ratio,
rank correlation) computed from the recorded per-country pairs.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.g5 import run_g5_gate, print_g5_report
from earth1.forces import PHYSICS_VERSION

report = run_g5_gate(pop=50_000, seed=42, progress=True)
print(print_g5_report(report))

# distribution metrics from the event leg's per-country record
pc = report.event.per_country
sim = np.array([r["simulated"] for r in pc])
meas = np.array([r["measured"] for r in pc])
uniform = np.full_like(meas, meas.mean())
dist = {
    "per_country_mae_engine": round(float(np.mean(np.abs(sim - meas))), 5),
    "per_country_mae_uniform_shift": round(float(np.mean(np.abs(uniform - meas))), 5),
    "variance_ratio_sim_over_real": round(float(sim.std() / meas.std()), 4) if meas.std() > 0 else None,
    "rank_correlation": round(float(sp_stats.spearmanr(sim, meas).statistic), 4) if len(pc) > 2 else None,
}
print("\nEVENT DISTRIBUTION METRICS (heterogeneity):")
for k, v in dist.items():
    print(f"  {k}: {v}")

results = json.loads((ROOT / "data/g5_results.json").read_text())
results.append({
    "run": 10,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "pop": 50_000, "seed": 42,
    "physics_version": PHYSICS_VERSION,
    "frozen_commit": "4147de4",
    "note": "First measurement-era run: full gate on the frozen architecture, canonical heartbeat, served binary, on the Hetzner server.",
    "temporal": {"mae_engine": report.temporal.mae_engine,
                  "mae_nochange": report.temporal.mae_nochange,
                  "sign_accuracy": report.temporal.sign_accuracy,
                  "sign_p": report.temporal.sign_p,
                  "passes": report.temporal.passes},
    "event": {"ratio": report.event.magnitude_ratio,
               "sign_match": report.event.sign_match,
               "passes": report.event.passes,
               "distribution": dist},
    "demography": {"le_tracking": report.demography.le_tracking,
                    "cdr": report.demography.world_adult_cdr,
                    "passes": report.demography.passes},
    "all_pass": report.all_pass,
})
(ROOT / "data/g5_results.json").write_text(json.dumps(results, indent=2))
print("\nrun #10 appended to data/g5_results.json")
