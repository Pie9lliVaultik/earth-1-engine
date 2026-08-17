#!/usr/bin/env python3
"""Scale ladder rung 1M — the evidence package (frozen physics E1-0.4).

Each rung earns the next (Pietro's rule). This runs at 1,000,000 agents:
  1. Genesis determinism: same seed twice -> identical population hash
  2. G5 demography leg (registered protocol, 1M standing population CDR)
  3. G5 event leg (COVID rally under A3)
  4. GOQA benchmark (engine vs naive, LOO-country CV)
Recorded to data/rung_1m.json. Pass = rung earned; 10M is next.
"""
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.genesis import genesis
from earth1.living import pop_hash_full
from earth1.forces import PHYSICS_VERSION

import os
POP = int(os.environ.get("RUNG_POP", "1000000"))
RUNG_NAME = os.environ.get("RUNG_NAME", "1M")
out = {"rung": RUNG_NAME, "pop": POP, "physics": PHYSICS_VERSION,
       "started": datetime.now(timezone.utc).isoformat()}

print(f"[1/4] genesis determinism at {POP:,}...")
t0 = time.time()
h1 = pop_hash_full(genesis(POP, seed=42))
h2 = pop_hash_full(genesis(POP, seed=42))
out["genesis_seconds"] = round(time.time() - t0, 1)
out["deterministic"] = h1 == h2
print(f"  {out['genesis_seconds']}s, deterministic: {out['deterministic']}")

print("[2/4] demography leg at 1M...")
from earth1.g5 import g5_demography
d = g5_demography(pop=POP, seed=42)
out["demography"] = {"le_tracking": d.le_tracking, "cdr": d.world_adult_cdr,
                     "passes": d.passes}
print(f"  LE {d.le_tracking:.0%}, CDR {d.world_adult_cdr}, passes={d.passes}")

print("[3/4] event leg at 1M...")
from earth1.g5 import g5_event_reaction
e = g5_event_reaction(pop=POP, seed=42)
out["event"] = {"ratio": e.magnitude_ratio, "sign": e.sign_match,
                "passes": e.passes}
print(f"  ratio {e.magnitude_ratio:.3f}, passes={e.passes}")

print("[4/4] GOQA at 1M...")
from earth1.benchmark import run_goqa_benchmark
goqa_data = json.loads((ROOT / "data/benchmark/goqa_ground_truth.json").read_text())
civ = genesis(POP, seed=42)
r = run_goqa_benchmark(civ, goqa_data)
out["goqa"] = {"engine_cv_mae": r.engine_cv_mae, "naive_cv_mae": r.naive_cv_mae,
               "engine_wins": r.engine_wins, "n_questions": r.n_questions}
print(f"  engine CV {r.engine_cv_mae:.4f} vs naive {r.naive_cv_mae:.4f}, "
      f"wins {r.engine_wins}/{r.n_questions}")

out["finished"] = datetime.now(timezone.utc).isoformat()
out["rung_earned"] = (out["deterministic"] and out["demography"]["passes"]
                      and out["event"]["passes"]
                      and out["goqa"]["engine_cv_mae"] < out["goqa"]["naive_cv_mae"])
(ROOT / f"data/rung_{RUNG_NAME.lower()}.json").write_text(json.dumps(out, indent=2))
print(f"\nRUNG {RUNG_NAME} EARNED: {out['rung_earned']}")
