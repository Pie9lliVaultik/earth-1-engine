# IT5-A REPORT — target-map census + force-writer attribution

Instrument: scripts/target_census.py (static census on production/
genesis/synthetic arms + 60-day η=0 writer attribution). Artifacts:
data/target_census_0_8/census.json. No repairs performed.

## Part 1 — the map itself is largely healthy

life_force_target's per-channel target distributions on genesis and
production are interior and heterogeneous (IDENTITY target mean 0.33,
COLLECTIVE 0.76, all channels with real spread; identical-target
fraction small). Synthetic known-answer arms classified correctly:
the constant lived-state collapses target diversity (detected), the
heterogeneous arm is healthy, the pole-biased arm rails targets
(detected). Sensitivities match the documented couplings. VERDICT:
the target MAP is not the railing author. (Its formulas remain
uncalibrated-hypothesis class — magnitudes never fit to evidence —
but they are not degenerate.)

## Part 2 — the railing authors, measured then read

η=0 world, day 60: per-channel non-relax residuals (force units/day)
with equilibrium displacement = residual / relax matching observed
railing exactly:

| channel | target | force | residual/day | author (code-read) |
|---|---|---|---|---|
| IDENTITY | 0.332 | 0.069 | −0.066 | **feed** pole-alignment: pole share 0.24 ⇒ 76% of agents pulled toward pole 0, daily, on the echo-chamber graph |
| TEMPERAMENT | 0.478 | 0.205 | −0.068 | feed (pole 0.44) + feedback trait couplings |
| CULTURE | 0.548 | 0.817 | +0.067 | **flourishing**: `CULTURE += 0.20·meaning` — strictly non-negative daily increment |
| COLLECTIVE | 0.759 | 0.918 | +0.040 | **flourishing**: `COLLECTIVE += 0.20·belonging` — strictly non-negative daily increment (+ crowd impulses) |
| DESIRE | 0.522 | 0.632 | +0.027 | flourishing hope/curiosity increments |
| EXPERIENCE | 0.358 | 0.454 | +0.024 | flourishing curiosity increment |
| FEAR | 0.701 | 0.644 | −0.016 | flourishing need/hope (net −ve in a fed, hopeful fresh world) |
| ECONOMICS | 0.524 | 0.525 | +0.000 | none — the clean channel proves the instrument |

## The architectural finding

Earth-1's force field is written daily by FOUR stacked operators
beyond the pull:
1. `propagate` — patched in IT3/IT4 experiments;
2. **`feed`** — a second certainty-weighted pole operator that ran
   UNPATCHED in every IT3/IT4 arm (why sat_max stayed 1.000 and KA2
   still railed);
3. **`contagion:210`** — a third daily averaging operator (reversion
   to country mean, every channel);
4. **`flourishing`** — five unconditional daily increments, two of
   them strictly non-negative (guaranteed railing, resisted only by
   relax).

The prior iterations attacked one of four writers. The field cannot
be healthy until the operator FAMILY is governed as a whole.

## Classifications (founder rule: only bug/contradiction authorize
repair)

- flourishing's five daily increments: **CONTRADICTION** — life.py's
  couple_life_to_forces documents the architecture's own law ("LEVEL
  MAP, NOT ACCUMULATION"), adopted after a recorded incident where
  incremental writes railed 99% of agents; flourishing violates it
  with two strictly-monotone terms. Repair-eligible.
- feed's pole-alignment form: **same structural class as propagate's
  pole expansion** (the defect family IT5-C exists to adjudicate) —
  classified CONTRADICTION-by-extension pending IT5-C's operator
  ruling: it must be governed by whatever operator law wins, not
  left running the incumbent pathology alongside a repaired
  propagate.
- contagion:210 country-mean reversion: **uncalibrated architecture**
  in the same consensus-operator family — IT5-C scope.
- Event-gated impulses (war, weather, crowd, national events,
  memory): **defensible architecture** — bounded, event-driven,
  causally meaningful; magnitudes uncalibrated but structure sound.
- life_force_target formulas: **uncalibrated hypothesis** — healthy
  structure, unfit magnitudes; calibration belongs to the benchmark
  program, not this repair cycle.

## Consequence for IT5-C's design

The operator experiment must patch the OPERATOR FAMILY consistently:
propagate + feed + contagion-smoothing under the same candidate law
(with feed's echo-chamber graph and arousal weights retained as
structure — it is the LAW of influence, not the existence of media,
under test). Flourishing's increments must be converted to the
documented level-map form (a target-shaping term inside
life_force_target) as a CONTRADICTION repair — with a registered
ablation arm (increments off vs converted) to preserve attribution.
