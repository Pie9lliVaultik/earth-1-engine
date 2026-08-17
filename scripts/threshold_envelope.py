"""Threshold repair diagnosis: the DYNAMIC reachable envelope.

Static genesis envelope (data/threshold_reachability.json): max national
FEAR 0.602 vs trigger 0.7. Open question: can the strongest VALID
perturbation close the gap? Valid = the channels that actually write
state — events act read-only (Ring B), so civ.forces moves only via
feedback nudges and demographics.

Protocol: two identical worlds, 1 simulated year, WVS questions with
response profiles. FORCED world re-injects the largest LLM-perceived
shock on record (crisis_us_2008, max-country L1 1.11) into EVERY
country every 30 days — a year of continuous 2008-scale crisis,
extreme-but-valid. Measure max |national force mean| movement vs
control and the residual gap to every trigger.

Measurement only. Env: TE_POP (default 50000).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earth1.advance import advance_world
from earth1.event_log import EventLog, WorldEvent
from earth1.g5 import _load_case_perceived_shocks
from earth1.genesis import genesis, GENESIS_COUNTRIES
from earth1.calibration import calibrate_single
from earth1.tick import WorldState, _make_mutable
from earth1.types import Force, Question
from earth1.wvs_paired import WVS_PAIRED

POP = int(os.environ.get("TE_POP", "50000"))
SEED = 42
CASE = "crisis_us_2008"
STEPS, DT = 12, 30.0


def _national_means(civ):
    floor = min(50, max(10, POP // 200))  # scale with pop for smoke runs
    out = {}
    for c in range(len(GENESIS_COUNTRIES)):
        mask = civ.country == c
        if mask.sum() >= floor:
            out[c] = civ.forces[mask].mean(axis=0)
    return out


def _questions(civ):
    profiles = json.load(open("data/question_profiles.json"))
    qs = []
    for pq in WVS_PAIRED:
        baseline = float(np.mean(list(pq.wave6.values())))
        w = calibrate_single(civ, baseline, pq.wave6)
        if not np.any(w):
            continue
        prof = profiles.get(pq.id)
        qs.append(Question(
            id=pq.id, text=pq.text, domain="belief_causal",
            baseline=baseline, weights=w, lens="wvs",
            response_profile=np.array(prof) if prof else None))
    return qs


def _run(forced: bool):
    civ = _make_mutable(genesis(POP, SEED))
    qs = _questions(civ)
    shocks = _load_case_perceived_shocks(CASE)
    state = WorldState(civ=civ, event_log=EventLog(), t=0.0, tick_count=0,
                       question_history=[], coupling_matrix={},
                       last_fired={}, rng=np.random.default_rng(SEED))
    t0 = _national_means(civ)
    for step in range(STEPS):
        if forced:
            for cc, lst in shocks.items():
                for deltas, decay in lst:
                    state.event_log.append(WorldEvent.create(
                        timestamp=state.t, force_deltas=deltas,
                        region_pattern=f"{cc}-*", decay_half_life=decay,
                        source="envelope:forced"))
        advance_world(state, qs, days=1, dt=DT)
    return t0, _national_means(civ)


def main() -> None:
    t0, control = _run(False)
    _, forced = _run(True)
    common = sorted(set(control) & set(forced) & set(t0))
    dyn = np.array([forced[c] - control[c] for c in common])
    tot = np.array([forced[c] - t0[c] for c in common])
    fmax = np.array([forced[c] for c in common])

    per_force = {}
    for f in Force:
        i = int(f)
        per_force[f.name] = {
            "max_abs_forced_vs_control": float(np.abs(dyn[:, i]).max()),
            "max_abs_forced_vs_t0": float(np.abs(tot[:, i]).max()),
            "max_national_mean_reached": float(fmax[:, i].max()),
            "min_national_mean_reached": float(fmax[:, i].min()),
        }
    fear_gap = 0.7 - per_force["FEAR"]["max_national_mean_reached"]
    econ_gap = per_force["ECONOMICS"]["min_national_mean_reached"] - 0.3

    out = {"pop": POP, "seed": SEED, "case": CASE,
           "steps": STEPS, "dt_days": DT,
           "per_force": per_force,
           "gap_to_fear_trigger": float(fear_gap),
           "gap_to_econ_trigger": float(econ_gap)}
    with open("data/threshold_envelope.json", "w") as f:
        json.dump(out, f, indent=1)
    mv = max(v["max_abs_forced_vs_control"] for v in per_force.values())
    print(f"THRESHOLD-ENVELOPE: max forced-vs-control national move "
          f"{mv:.4f} | FEAR reaches "
          f"{per_force['FEAR']['max_national_mean_reached']:.3f} "
          f"(gap {fear_gap:+.3f} to 0.7) | ECON floor "
          f"{per_force['ECONOMICS']['min_national_mean_reached']:.3f} "
          f"(gap {econ_gap:+.3f} to 0.3)", flush=True)


if __name__ == "__main__":
    main()
