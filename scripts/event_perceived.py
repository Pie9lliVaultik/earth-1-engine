#!/usr/bin/env python3
"""G5 event leg, perception-authored: the March 2020 shock as READ news.

Same measured-reaction harness as the gate's event leg, but the force
shocks are authored by LLM perception from real documented headlines —
zero hand-tuning. Curated-representative headlines (verifiable events),
flagged as such in the record.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from earth1.news_perception import NewsItem, perceive_item
from earth1.g5 import (COVID_RALLY, _predict_country_anchored,
                       _country_index_map)
from earth1.genesis import genesis
from earth1.calibration import calibrate_single
from earth1.tick import WorldState, world_tick, _make_mutable
from earth1.event_log import EventLog, WorldEvent
from earth1.generational import generational_tick
from earth1.types import Question, Force

HEADLINES = [
    NewsItem("Italy imposes nationwide lockdown as coronavirus deaths surge", "IT", "2020-03-09"),
    NewsItem("Spain declares state of emergency over coronavirus outbreak", "ES", "2020-03-14"),
    NewsItem("Germany closes borders with five countries to slow coronavirus", "DE", "2020-03-16"),
    NewsItem("France orders nationwide lockdown; Macron says 'we are at war'", "FR", "2020-03-17"),
    NewsItem("Netherlands announces 'intelligent lockdown' as cases climb", "NL", "2020-03-23"),
    NewsItem("Portugal declares state of emergency for first time in democracy's history", "PT", "2020-03-18"),
    NewsItem("Austria bans gatherings, closes shops in sweeping coronavirus measures", "AT", "2020-03-16"),
    NewsItem("Finland invokes Emergency Powers Act over coronavirus", "FI", "2020-03-17"),
    NewsItem("Sweden defies lockdown trend as deaths mount", "SE", "2020-03-30"),
    NewsItem("Poland closes borders and schools in coronavirus clampdown", "PL", "2020-03-15"),
]

def main():
    print("Perceiving 10 documented March-2020 headlines...")
    force_names = [f.name.lower() for f in Force]
    perceived = {}
    for item in HEADLINES:
        ev = perceive_item(item)
        if ev is None:
            print(f"  [abstained] {item.country}")
            continue
        perceived[item.country] = ev
        top = sorted(ev.force_deltas.items(), key=lambda kv: -abs(kv[1]))[:3]
        print(f"  {item.country}: " + ", ".join(
            f"{force_names[k]}{v:+.2f}" for k, v in top)
            + f"  (conf {ev.confidence:.2f}, decay {ev.decay_half_life:.0f}d)")

    case = COVID_RALLY
    civ = _make_mutable(genesis(50_000, 42))
    cmap = _country_index_map()
    baseline = float(np.mean(list(case.pre.values())))
    weights = calibrate_single(civ, baseline, case.pre)
    t0_means = civ.means.copy()
    countries = [c for c in case.pre if c in cmap and c in perceived]
    t0_pred = {c: _predict_country_anchored(civ, baseline, weights,
                                            cmap[c], t0_means)
               for c in countries}

    q = Question(id="covid_perceived", text=case.question_text,
                 domain="belief_causal", baseline=baseline,
                 weights=weights, lens="eb")
    state = WorldState(civ=civ, event_log=EventLog(), t=0.0, tick_count=0,
                       question_history=[], coupling_matrix={},
                       last_fired={}, rng=np.random.default_rng(42))
    for c in countries:
        ev = perceived[c]
        state.event_log.append(WorldEvent.create(
            timestamp=0.0,
            force_deltas={force_names[k]: v for k, v in ev.force_deltas.items()},
            region_pattern=f"{c}-*",
            decay_half_life=ev.decay_half_life,
            source="perception:llm"))

    for _ in range(3):  # 90-day window, 30-day steps (registered protocol)
        world_tick(state, questions=[q], dt=30.0,
                   enable_event_generation=False)
        generational_tick(state.civ, state.rng, dt_days=30.0)

    event_deltas = state.event_log.effective_deltas_vectorized(state.t, state.civ)
    sims, meas = [], []
    for c in countries:
        if t0_pred[c] is None:
            continue
        p1 = _predict_country_anchored(state.civ, baseline, weights,
                                       cmap[c], t0_means,
                                       extra_shift=event_deltas)
        sims.append(p1 - t0_pred[c])
        meas.append(case.post[c] - case.pre[c])

    sim, ms = float(np.mean(sims)), float(np.mean(meas))
    print(f"\nPERCEIVED-SHOCK EVENT TEST ({len(sims)} countries):")
    print(f"  simulated mean shift {sim:+.4f}  vs measured {ms:+.4f}")
    print(f"  ratio {sim/ms:.3f}  (hand-authored run #6 ratio: 0.02)")

if __name__ == "__main__":
    main()
