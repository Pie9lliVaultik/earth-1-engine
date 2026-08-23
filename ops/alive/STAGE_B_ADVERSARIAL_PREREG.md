# STAGE B — ADVERSARIAL BATTERY, DETAILED PREREGISTRATION (frozen)

Frozen BEFORE any Stage A result has been opened or scored (as of
this commit no Stage A output has been seen; Stage A is still
computing on prime). Per founder ruling the sequence is: master
frozen → THIS prereg frozen → Stage A opened. Candidate executable
1ae8740; instruments at the commit containing this file.

Governing question, predeclared per test: WHAT DELIBERATELY BROKEN
IMPLEMENTATION MUST THIS INSTRUMENT DETECT? A test that cannot
visibly fail its broken twin is not evidence (Standing Rule 2).

Seed policy: fresh block 9101–9120, assigned in the order below;
horizon 120d at N=200k unless stated; every broken arm runs beside
the healthy frozen candidate through the IDENTICAL instrument.
Decision rule: each test scores DETECTED (the named instrument
flags the broken arm) AND CLEAN (the healthy candidate passes the
same instrument). Any broken arm not detected ⇒ the associated
acceptance instrument is VOID and must be repaired before its
acceptance claim is usable. Any healthy-arm flag ⇒ FAIL / STOP AND
DIAGNOSE. No thresholds may be adjusted after results.

B1 planted consensus (seed 9101): broken = daily global mean-
   reversion of stored forces (rate 0.05) injected as an extra
   writer. Must be detected by: sdr < 0.5 and/or unanimity ≥ 50%
   within 60d.
B2 conviction ratchet (9102): broken = incumbent ratchet conviction
   law (the retired cnv="inc"). Detected by: alpha_gt99 ≥ 1% and/or
   softening_frac ≈ 0 (< 1e-4) by d90.
B3 zero influence (9103): broken = op "zero" (no encounters).
   Detected by: clustered ring1 < 0.006 at the transmission probe.
B4 excessive reversion (9104): broken = relax 0.60. Detected by:
   tau half-life < 5d at the standing fork.
B5 absent persistence (9105): broken = Chronicle press disabled.
   Detected by: IT12-protocol event, normalized d30/peak < 0.2.
B6 event accumulator (9106): broken = one scenario event executed
   as an unconditional daily force write (the probe-1 grinder,
   deliberately resurrected in the harness only). Detected by:
   stored sat_max ≥ 0.20 and/or channel-mean runaway ≥ 0.15 within
   90d, on the release-gate invariant instrument.
B7 self-rearming cascade (9107): broken = residues re-applied into
   life_force_target (the PF-DECAY-1 closed loop, deliberately).
   Detected by: the KA8 instrument (planted sub-threshold substrate
   + supra-threshold effective view ⇒ a fire occurs) AND the
   wipe-pair divergence (N_fires_caused_only_by_actuation > 0).
B8 cascade→cascade contamination (9108): broken = detector reads
   effective_forces() instead of stored forces. Detected by: KA10
   pair divergence (identical substrate, residue-bearing world
   fires differently).
B9 effective-view mutation (no world needed): attempt to write
   through effective_forces() in both branches. Detected by:
   ValueError raised; any silent success ⇒ VOID.
B10 duplicate causality (9109): broken = one scenario ingested
   twice (chronicle memory + direct force impulse for the same
   event). Detected by: paired expression delta ≈ 2× the
   single-path arm (ratio > 1.6) on the double-count instrument.
B11 clamp stress (9110): per the D1 ruling. Instrument: at-bound
   occupancy census (stored per channel) + recovery after an
   R3-class sustained stress. Broken twin = event amplitudes ×5 so
   the [0,1] clip becomes load-bearing. Detected by: at-bound
   occupancy ≥ 5% sustained ≥ 30d in the broken arm; healthy arm
   reported (descriptive; no new numeric gate on the healthy arm).
B12 restart/serialization (9111): mid-run canonical save/load at
   d60 must continue bitwise (stored forces, residues, cooldowns,
   chronicle, rng). Broken twin = serializer that silently drops
   cascade_residues. Detected by: post-restore trajectory
   divergence flagged by the bitwise comparator.
B13 time-step invariance: NOT APPLICABLE — registered
   determination: the frozen candidate defines dt = 1 day and no
   alternative integrator exists in the executable; no synthetic
   test is fabricated. Revisit only if a sub-day integrator is ever
   proposed (which would be new physics requiring its own ruling).

Artifacts: data/acceptance_0_8/stageB/. Stage B runs only after
Stage A is scored, but this specification is immutable from this
commit forward.
