#!/usr/bin/env python3
"""G5 run #7 — event leg under amendment A3 (temporal response law).

Perceived shocks (cached, blind) + question response profile (cached,
blind) + RESPONSE_GAIN=3.1 (leave-COVID-out). Engine propagation and
pass criteria identical to the original registration.
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from datetime import datetime, timezone
from earth1.g5 import COVID_RALLY, _predict_country_anchored, _country_index_map
from earth1.genesis import genesis
from earth1.calibration import calibrate_single
from earth1.tick import WorldState, world_tick, _make_mutable
from earth1.event_log import EventLog, WorldEvent
from earth1.generational import generational_tick
from earth1.types import Question, Force, NUM_FORCES

cache = json.loads((ROOT / "data/perceived_cases.json").read_text())
profile = np.array(json.loads((ROOT / "data/question_profiles.json").read_text())
                   ["covid_rally_2020"])
force_names = [f.name.lower() for f in Force]

# per-country perceived shocks from the cached case headlines
shocks = {}
for key, p in cache.items():
    if not key.startswith("covid_rally_2020|") or p is None:
        continue
    cc = key.split("|")[1]
    v = np.zeros(NUM_FORCES)
    for k, d in p["deltas"].items():
        v[int(k)] = d
    shocks.setdefault(cc, []).append((v, p["decay"]))

case = COVID_RALLY
civ = _make_mutable(genesis(50_000, 42))
cmap = _country_index_map()
baseline = float(np.mean(list(case.pre.values())))
weights = calibrate_single(civ, baseline, case.pre)
t0_means = civ.means.copy()
countries = [c for c in case.pre if c in cmap and c in shocks and c in case.post]
t0 = {c: _predict_country_anchored(civ, baseline, weights, cmap[c], t0_means)
      for c in countries}

state = WorldState(civ=civ, event_log=EventLog(), t=0.0, tick_count=0,
                   question_history=[], coupling_matrix={}, last_fired={},
                   rng=np.random.default_rng(42))
for c in countries:
    for v, decay in shocks[c]:
        state.event_log.append(WorldEvent.create(
            timestamp=0.0,
            force_deltas={force_names[i]: float(x) for i, x in enumerate(v)
                          if abs(x) > 1e-6},
            region_pattern=f"{c}-*", decay_half_life=decay,
            source="perception:llm"))

q = Question(id="covid_a3", text=case.question_text, domain="belief_causal",
             baseline=baseline, weights=weights, lens="eb",
             response_profile=profile)
for _ in range(3):
    world_tick(state, questions=[q], dt=30.0, enable_event_generation=False)
    generational_tick(state.civ, state.rng, dt_days=30.0)

deltas = state.event_log.effective_deltas_vectorized(state.t, state.civ)
per_country, sims, meas = [], [], []
for c in countries:
    if t0[c] is None:
        continue
    p1 = _predict_country_anchored(state.civ, baseline, weights, cmap[c],
                                   t0_means, extra_shift=deltas,
                                   response_profile=profile)
    sims.append(p1 - t0[c]); meas.append(case.post[c] - case.pre[c])
    per_country.append({"country": c, "simulated": round(sims[-1], 4),
                        "measured": round(meas[-1], 4)})
    print(f"  {c}: sim {sims[-1]:+.4f}  meas {meas[-1]:+.4f}")

sim, ms = float(np.mean(sims)), float(np.mean(meas))
ratio = sim / ms if ms else 0.0
passes = bool(np.sign(sim) == np.sign(ms) and 0.25 <= ratio <= 4.0)
print(f"\nRUN #7 EVENT LEG (A3): sim {sim:+.4f} vs meas {ms:+.4f} "
      f"ratio {ratio:.2f} -> {'PASS' if passes else 'FAIL'}")

results = json.loads((ROOT / "data/g5_results.json").read_text())
results.append({
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "run": 7, "amendment": "A3", "leg": "event_reaction_only",
    "pop": 50_000, "seed": 42, "response_gain": 3.1,
    "simulated_mean_shift": round(sim, 5), "measured_mean_shift": round(ms, 5),
    "magnitude_ratio": round(ratio, 4), "passes": passes,
    "per_country": per_country,
})
(ROOT / "data/g5_results.json").write_text(json.dumps(results, indent=2))
print("Recorded run #7 -> data/g5_results.json")
