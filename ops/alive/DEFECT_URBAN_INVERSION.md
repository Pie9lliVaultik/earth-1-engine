# DEFECT-URBAN-INVERSION (found 2026-09-08, registered, NOT patched)

## The defect
In the C2+ substrate, `civ.urban == True` means **RURAL**. Measured against the
census marginals at 60k agents:

| country | model `urban==True` | census urban | 1 − model |
|---|---|---|---|
| JP | 0.075 | 0.920 | 0.925 |
| US | 0.152 | 0.833 | 0.848 |
| IN | 0.645 | 0.364 | 0.355 |
| NG | 0.456 | 0.543 | 0.544 |

Every case is exactly `1 − census`. **Source:** `build_tables.py` sets
`m_urb = [urban%, 1 − urban%]`, so joint axis index 0 carries the URBAN mass;
`popsynth.draw_c2plus` then stores `urb = u.astype(bool)`, making the urban
population `civ.urban == False`. The legacy (non-C2+) genesis path is correct
(`urban = rng.random(n) < urban_rate`), so the inversion arrived with C2+ — which
is the freeze-0.9 substrate.

## Consumers, by severity
**Physics (real effect, wrong population):**
- `contagion.py:168` — `dens *= np.where(civ.urban, 1.6, 0.5)`: the urban density
  multiplier is applied to rural agents and the rural discount to urban ones.
- `flourishing.py:113` — `air = ... + 0.05 * civ.urban`: urban air pollution is
  assigned to rural agents.

**Readout (labels swapped, no physics effect):**
- `answer_living.py:87-88` — the `urban`/`rural` cohort masks are exchanged.
- `cohort_features.py:40` — the urban feature fed to the readout is inverted.

**Harmless (symmetric partition bit):**
- `alive.py`, `consequences.py`, `contagion.py`, `fabric.py` locality keys — urban
  is only a grouping bit there; inverting it relabels localities without changing
  their membership structure.

## Why it is NOT patched here
Physics is frozen at 0.9. Correcting the inversion changes contagion density and
air quality for every agent, which is a physics change requiring its own XI.A.2
cycle and a full anchor-board retest. Silently flipping it now would invalidate
every board on the current tag.

## Registered as
**v1.1 mechanism cycle, first tier** — alongside the chronicle-consolidation cycle.
Gates: anchor board must hold (poverty/mortality/median unchanged within seed noise,
since neither contagion density nor air quality feeds them directly); disease-death
share and the flourishing air channel are the observables expected to move, and
their movement is the test that the fix did something.

## Not affected
`earth1/cohorts.py` (the population frame) operates on the JOINT AXIS, not the
boolean, and is therefore correct: axis index 0 = urban, as the tables define it.
The `/models/:ref/population-frame` endpoint's urban and rural cohorts are right.
