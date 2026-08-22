# STAGE B — ADVERSARIAL BATTERY: PASS 13/13 (with the B11 record)

Scored against e89c98a at N=200k on candidate v2 (76a574c lineage).
Artifact: data/acceptance_0_8/stageB/stageB.json (verdict amended
at a177d05). Every broken twin DETECTED by its named instrument;
every healthy twin CLEAN through the identical instrument.

## B11 clarification (permanent record; founder's four questions)

1. What made B11 "unscored"? — Nothing in the arm or instrument.
   The B11 broken arm (seed 9110, 120d, 5× impulses d10–d90, at-bound
   occupancy census) ran in the Stage B batch exactly as registered
   and its data was recorded at run time. The defect was in the
   runner's VERDICT ASSEMBLER: it contained scoring blocks for twelve
   tests and none for B11, so the printed "STAGE B PASS" was computed
   over twelve and silently omitted the thirteenth.
2. Discovered before any scored B11 result was observed? — There
   never was a scored B11 output to observe: the assembler produced
   none. The omission was discovered during self-review of the
   verdict list AFTER the other twelve tests' scored results had
   been seen. The B11 arm's raw data was produced before any
   scoring; the B11 criterion (at-bound ≥5% sustained ≥30d in the
   broken arm; healthy arm descriptive) was fixed in e89c98a before
   the run.
3. Rerun with a valid instrument? — Not rerun: the instrument was
   valid and the data complete. The prereg criterion was applied
   verbatim to the already-recorded data (amendment a177d05; the
   runner gained the missing block for future runs).
4. Exact evidence earning the PASS — DETECTED: broken-twin stored
   at-bound occupancy 0.125 at every census point d10–d90 (eight
   consecutive points; ≥5% sustained ≥30d satisfied), then recovery
   to 0.00031 by d100 once impulses stop. CLEAN (descriptive per
   prereg): healthy candidate at-bound 0.0 at every census point —
   measured on the seed-9106 healthy endurance arm; a same-seed
   (9110) healthy twin was NOT in the job list and was not run.

Resolution: B11 is scorable and scored — Stage B stands at 13/13,
with the same-seed-twin omission footnoted permanently. Should the
founder require strict same-seed CLEAN for B11, a single 120-day
healthy arm at 9110 would settle it; not executed absent that
instruction.

## Instrument-integrity incidents (both disclosed at the time)

- B7's prereg-named KA8-variant detector proved insensitive to the
  resurrected target-path loop (its daily clamp resets the
  sub-threshold accumulation the loop needs); VOID per the prereg's
  own rule, repaired to the KA10 stored-divergence pair, which
  detects the loop immediately; the wipe-pair receipt retained.
- B11 verdict-assembly omission, as above.
