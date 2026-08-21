"""IT10 exact-semantics KA checks (KA2, KA2', KA3-step) — numerical
requirements, not empirical arms."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.alive import birth_world
from earth1.life import life_force_target

LAM = 0.1072
w = birth_world(20_000, 8902)
civ, life = w.civ, w.life
T = life_force_target(civ, life)
out = {}

# KA2: F = T  =>  db == 0 exactly
civ.forces = T.copy()
T2 = life_force_target(civ, life)
db = LAM * (civ.forces - T2)
out["KA2_stationary_max_db"] = float(np.abs(db).max())
out["KA2_pass"] = bool(np.abs(db).max() == 0.0)

# KA2': F = T, b != T — accepted law adapts nothing; planted (F-b)
# law must move b and be detected
b = life.force_baseline
assert not np.allclose(b, T)
db_accept = LAM * (civ.forces - T2)
db_reject = LAM * (civ.forces - b)
out["KA2p_accepted_max_db"] = float(np.abs(db_accept).max())
out["KA2p_rejected_max_db"] = float(np.abs(db_reject).max())
out["KA2p_pass"] = bool(np.abs(db_accept).max() == 0.0
                        and np.abs(db_reject).max() > 1e-3)

# KA3: one-step linearity at an interior state (no clipping)
rng = np.random.default_rng(5)
civ.forces = np.clip(T + rng.normal(0, 0.05, T.shape), 0.2, 0.8)
T3 = life_force_target(civ, life)
d1 = LAM * (civ.forces - T3)
d10 = 10 * LAM * (civ.forces - T3)
ratio = d10[np.abs(d1) > 1e-9] / d1[np.abs(d1) > 1e-9]
out["KA3_step_ratio_mean"] = float(ratio.mean())
out["KA3_pass"] = bool(np.allclose(ratio, 10.0, rtol=1e-9))

print(json.dumps(out, indent=1))
Path(ROOT / "data" / "it10_semantic_checks.json").write_text(
    json.dumps(out, indent=1))
sys.exit(0 if all(out[k] for k in ("KA2_pass", "KA2p_pass",
                                   "KA3_pass")) else 1)
