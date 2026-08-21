# STAGE A — 365-DAY ENDURANCE: FAIL → STOP AND DIAGNOSE

Scored mechanically against 334abf5. Valid instruments (no errors;
all census machinery behaved). Artifacts:
data/acceptance_0_8/stageA/endurance.json. Runtime 10.8 min, N=200k,
seeds 9001/9002/9003, candidate machine 1ae8740 lineage (@45564c1
instruments).

## Verdict per seed (frozen gates)

| gate | 9001 | 9002 | 9003 |
|---|---|---|---|
| sat_terminal < 0.20 | 0.126 ✓ | 0.163 ✓ | **0.334 ✗** |
| max_t sat < 0.20 | **0.212 ✗** | **0.226 ✗** | **0.358 ✗** |
| sdr ≥ 0.5 | ✓ (0.64) | ✓ | ✓ (0.68) |
| unanimity < 50% | ✓ | ✓ | ✓ |
| α interior | ✓ | ✓ | ✓ |
| no runaway (< 0.15) | ✓ 0.038 | ✓ 0.052 | ✓ 0.028 |

STAGE A: FAIL (3/3 seeds miss max_t; one also misses terminal).
The max_t gate — added prospectively from the seed-8905 lesson — is
what caught it; terminal-only scoring would have passed 2 of 3.

## Diagnosis (measured, complete)

THE PATHOLOGY IS ONE CHANNEL. COLLECTIVE carries every breach in
all three seeds; the other seven channels sit at 0.00–0.02 saturation
for the entire year.

MECHANISM: the COLLECTIVE stored mean is STATIONARY at ≈ 0.885
(0.862→0.883→0.885… all year; the runaway gate passes honestly).
The breaches are the HIGH-RAIL TAIL: with an equilibrium mean
0.065 below the 0.95 rail-line, ordinary distributional breathing
puts 10–36% of the population past 0.95 episodically (9001: one
spike 0.21 @d230, recovers; 9002: oscillates 0.17–0.23 through the
back half; 9003: surges to 0.36 after d300). Onset is always after
day ~150 — the 120-day development horizon never sampled it
(recorded IT6-ALL sat 0.16 @d120 was true and insufficient).

EXCLUDED CAUSES (measured): cascade feedback (open-loop; cascades
write nothing to stored state — PF-DECAY-2 receipts); diversity
collapse (sdr rises 0.55→0.68); mean drift (stationary); clip
dependence (at-bound occupancy ≤ 0.05%, overlay clip ≤ 0.06% —
the D1 clamp answer is clean); population/material instability
(alive −1.4%/yr, employment 0.90 stable); memory effects (0
standing memories in the no-news world, as designed).

## The falsified frozen proposition, stated precisely

"The frozen candidate holds every stored channel's rail-tail under
20% for 365 days in a no-news world." False — specifically and only
for COLLECTIVE, whose calibrated equilibrium geometry (genesis/
target mean ≈ 0.885) sits within one breathing amplitude of the
0.95 rail-line. This is a property of the frozen channel geometry
meeting the frozen tail gate at the year horizon; it is not caused
by any 0.8-repaired mechanism (all of which are exonerated by the
exclusions above).

## Ledger notes

- Effective-view (unscored, characterized as registered): sat_eff
  max_t 0.69–0.76 — the Stage C census question stands as filed.
- Seeds 9001–9003 are now burned development evidence.
- Per frozen discipline: no tuning, no gate relitigation, no Stage
  B execution — the chain is STOPPED pending founder ruling. The
  decision that is the founder's to make: whether Stage A falsifies
  the candidate's COLLECTIVE channel geometry (reopening that ONE
  named element by explicit ruling), or the gate's construct
  validity for near-rail channels (which would itself require a
  registered, independently justified gate revision), or something
  else the diagnosis has not surfaced.
