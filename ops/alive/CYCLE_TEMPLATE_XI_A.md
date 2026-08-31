# CYCLE cNNN — <one named change>
_Emitted for every cycle with `change != none`. Sections are mandatory;
STATUS=PASS is refused if any section is empty. Diagnostic cycles
(`change=none`) emit RESULT and INSTRUMENT only. Governed by BIBLE.md
Part XI.A.2 and the v4.2 amendment._

## RESULT
| field | value |
|---|---|
| gate(s) exercised | e.g. age_at_death, CDR, $8.30, cohort_frozen_cells |
| number(s) | before → after, with seed σ |
| target | from the gate table, with its prereg hash |
| gap | after − target |
| agents / seeds | 20000 × 3 |
| flag set | full env, substrate tag |
| hashes | tree · substrate table · anchors · concordance · constants file |
| host / commit / wall-clock | stamped by the runner (Rule 10) |

## INSTRUMENT
What was checked before believing the number: ground truth provenance
(fetched, series id, vintage, sha256); units; leakage (which data
roles were read, under which purpose); persistence (state survived
save→restore); canonical-path confirmation (the tested code is the
shipping flag set on the unified loop, not a script-level assembly);
the known-answer verification that passed (e.g. floor reproduces
canonical 10.08 within 0.01; null_branch bitwise-identical). Name the
failure case this instrument would report and show it reports it
(Rule 2).

## DIAGNOSIS
Causal path from code to number, with `file:line`. Quantified
attribution: which mechanisms, parameters, datasets or missing
channels account for what share of the gap. State whether the miss is
(a) instrument, (b) input/anchor, (c) parameter, (d) structurally
missing channel — and how you know (sensitivity/ablation: if no
parameter can move it, it is (d)).

## RESEARCH
Literature searched and methods considered (peer-reviewed,
authoritative reports, reference simulators, government models). At
least two competing approaches named with citations. Why the selected
approach applies to Earth-1 and the others were rejected. If the field
has an established method, it is used — no invention where research
exists (XI.A step 5). A number without mechanism and citation is not a
result (Rule 7).

## IMPLEMENTATION
The smallest defensible change: what, where (`file:line`), behind
which flag, default OFF. Provenance class of every constant introduced
or changed (SOURCED / ANCHORED / FITTED / DERIVED / ASSUMED) and, for
FITTED, the data-role hash it was fitted on. Substrate tag if
substrate-dependent. Why this is the smallest change.

## ABLATION
Controlled runs isolating what produced the improvement: change ON vs
OFF on identical seeds (paired CRN); the mechanism disabled on the
benchmark built to exercise it (acceptance test iv); sensitivity of
the gate to the new constant across its plausible range. Report which
of the observed movement is attributable to this change alone, with σ.
A change that moves the target gate but regresses any other gate by
>2σ is VOID.

## RETEST
The new number on TRAIN/DEV against the **unchanged** gate, compared
to the previous cycle on the same frozen cells/anchors/seeds. Every
other gate in the table re-run in this same cycle, listed with
before/after. 200k rerun if 20k moved ≥0.3pp in the right direction
(sign-flip check only at 200k).

## STATUS
One of: **PASS** (gate met with margin >2σ, no regression, all
sections complete → eligible for FREEZE consideration; holdout
untouched) · **ITERATING** (gate not met; next hypothesis named, one
line) · **INERT** (moved nothing beyond 2σ; flag OFF; artifact and
sign findings retained) · **VOID** (instrument defect; row struck;
instrument diagnosis recorded; rerun scheduled) · **FALSIFIED**
(repeated clean experiments, correct implementation, literature
approaches and calibration all fail; negative evidence preserved;
capability redesigned, never faked).
