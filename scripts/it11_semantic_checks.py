"""IT11 KA3 (analytic decay) + KA5 (restart) exact checks."""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1 import persistence
from earth1.alive import birth_world
from earth1.memory import Memory
from earth1.types import Force

out = {}
w = birth_world(2000, 8903)
sig = np.zeros(8)
sig[Force.FEAR] = 0.5
scope = np.zeros(2000, dtype=bool)
scope[:100] = True
m = Memory(id="ka3", label="ka3", day=0.0, force_signature=sig,
           scope=scope, half_life=720.0)
w.chronicle.events = [m]

# KA3: one-step and N-step decay exactness (rehearsal/spread not
# invoked: tick only)
s0 = m.salience
w.chronicle.tick(w.civ, 1.0)
ratio = m.salience / s0
out["KA3_one_step_ratio"] = float(ratio)
out["KA3_expected"] = float(0.5 ** (1 / 720.0))
out["KA3_pass"] = bool(abs(ratio - 0.5 ** (1 / 720.0)) < 1e-12)
for _ in range(9):
    w.chronicle.tick(w.civ, 1.0)
out["KA3_10step_pass"] = bool(
    abs(m.salience - 0.5 ** (10 / 720.0)) < 1e-10)

# KA5: restart mid-decay -> identical continuation
with tempfile.TemporaryDirectory() as td:
    persistence.save_world(w, Path(td) / "w.pkl",
                           np.random.default_rng(1))
    w2, _r, _i = persistence.load_world(Path(td) / "w.pkl")
m2 = w2.chronicle.events[0]
out["KA5_salience_preserved"] = bool(m2.salience == m.salience)
w.chronicle.tick(w.civ, 1.0)
w2.chronicle.tick(w2.civ, 1.0)
out["KA5_continuation_identical"] = bool(
    w2.chronicle.events[0].salience == w.chronicle.events[0].salience)
out["KA5_pass"] = out["KA5_salience_preserved"] and \
    out["KA5_continuation_identical"]

print(json.dumps(out, indent=1))
Path(ROOT / "data" / "it11_semantic_checks.json").write_text(
    json.dumps(out, indent=1))
sys.exit(0 if out["KA3_pass"] and out["KA3_10step_pass"]
         and out["KA5_pass"] else 1)
