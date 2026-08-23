# effective_forces() CONSUMER AUDIT (pre-freeze, per founder ruling)

Performed after PF-DECAY-2 PASS, before the freeze is confirmed.
Question: where is the overlay visible, and is there any hidden path
from the effective view back into canonical state?

## Complete consumer census (repo-wide, at f718b0f+)

| consumer | class | verdict |
|---|---|---|
| scripts/pf_decay_ka.py (KA2'/KA6/KA8/KA11 instruments) | B readout | measurement-only; never writes back |
| scripts/it6_dyadic.py:274 (eff_sat panel probe) | B readout | measurement-only; reported separately from stored gates |
| — engine physics — | | **ZERO consumers** |

Class-A verification (all read stored civ.forces directly, never the
overlay): transition detection (alive.py:341), propagate/influence
(:252), relax (:282), conviction (:283), openness feedback (:385),
contagion (contagion.py), feed (feed.py), chronicle press
(memory.py), life/material (life.py), target computation. The daily
loop contains no effective_forces call.

## Hazard found and closed

The no-residue branch returned `civ.forces` ITSELF — an alias of
canonical state. A class-B consumer writing through the returned
array would have silently mutated stored psychology: the exact
"feedback loop hidden behind another API" the ruling STOPs on.
Closed: effective_forces() now returns an IMMUTABLE view in every
branch (write attempts raise ValueError); verified in both branches;
affected KAs re-run green.

## Canonical ontology (permanent, per ruling)

cascade_residue is NOT stored psychological state. It is a derived,
decaying expression/readout overlay:

    F_stored(t)     — evolves; the only psychological state
    F_effective(t)  = F_stored(t) + C(t)   — derived, immutable
    C(t)            — explicitly attributable cascade overlay

Never describe F_effective as the person's stored force. Four
distinct ways history matters, never to be collapsed:
material history → persistent material state; informational history
→ Chronicle; current lived conditions → stored force expression;
transition/cascade residue → temporary derived expression overlay.

## Scientific limitation (standing language)

The overlay changes reported/expressed psychology only. No
executable pathway currently consumes it into behavior,
relationships, transmission, or subsequent stored psychology — so no
claim "the cascade caused Earthlings to BEHAVE differently" is
permitted unless and until an explicit, separately calibrated
mechanism consumes the effective view. This applies verbatim to the
investor Observatory: computed expression is not computed behavioral
consequence, and no LLM may bridge that gap. (The Observatory demo
runs incumbent physics with candidate flags OFF; no leakage today.)

## Wiring status (disclosed)

Production readout paths (observer.ask, question projection, API
routes) currently read STORED forces; wiring them to the effective
view under the frozen readout contract is mechanical
instrumentation work for the acceptance battery, class B by
construction, and must import effective_forces() rather than
reimplementing it.

## Verdict

    NO HIDDEN PATH FROM EFFECTIVE VIEW INTO CANONICAL STATE.
    AUDIT CLEAN → the freeze may be confirmed.
