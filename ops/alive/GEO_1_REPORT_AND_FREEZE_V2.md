# COLLECTIVE-GEO-1: PASS → CANDIDATE v2 FROZEN

Scored against the frozen registration (edb2f47). Artifacts:
data/geo1/ (KA batteries, GEO-1A endurance, IT12 arms, IT6-ALL arm,
PF-DECAY KAs).

## Verdict against the three frozen conditions

1. ALL KAs PASS — locally, at full N=200k, and KA0 incumbent
   continuity (flag off ⇒ recorded 1ae8740 metrics exact). Core
   invariant: neutral reference state ⇒ T = B at max error 0.0;
   per-modifier slopes exact to 1e-17; no dynamic centering; seven
   other force rows bit-identical.
2. GEO-1A — the known-failure seeds LOSE the diagnosed pathology:
   COLLECTIVE target mean 0.86 → 0.74 (registered expectation 0.73);
   frac(T>0.95) 41.8% → 17.8–18.7%; stored COLLECTIVE mean 0.885 →
   0.76–0.80; year-horizon max_t saturation across ALL channels
   0.212/0.226/0.358 → 0.023/0.031/0.114. Every other Stage-A-class
   gate green on all three worlds. (Development evidence only —
   9001–9003 can never validate.)
3. Full regression healthy: IT6-ALL @8890 flag on — tau 5,
   ring1/2/3 0.00699/0.00076/0.00059 (recorded: 0.00702/0.00081/
   0.00059), sdr 0.665, α interior, softening present, hardening
   1.0, sat d120 0.048; IT12 arms — COMPOSITE true-peak-normalized
   0.574 ∈ [0.2, 0.6], INTRINSIC carrier analytics exact
   (0.5/0.125), carrier-delete reverts; PF-DECAY open-loop KA
   battery ALL PASS under the new law.

Honest note on residual geometry: frac(T>0.95) ≈ 18% is still a
wide near-pole tail (the target distribution is broad); the stored
field no longer rails (max_t ≤ 0.114 over a year) and the mean is
off the pole. The authored slopes (0.25/0.20/0.40/0.20) remain
tagged AUTHORED / REQUIRES PARAMETER PROVENANCE in the registry.

## CANDIDATE v2 (frozen)

    candidate_executable_commit_v2: THE COMMIT CONTAINING THIS FILE
        (supersedes 1ae8740, which remains forever the historical
        Stage-A-v1-failing candidate)
    flags: EARTH1_CASCADE_COOLDOWN=1, EARTH1_DECAY_RESIDUE=1,
           EARTH1_COLLECTIVE_CENTERED=1
    change vs 1ae8740: COLLECTIVE centered-deviation target law ONLY
        (life.py + field_lab belonging term; reference constants per
        COLLECTIVE_GEO_1.md). Everything else identical.

## Stage A v2 (preregistered here, before any run)

Fresh seeds: 9301, 9302, 9303 (never used anywhere). Identical
protocol, instruments, and gates to 334abf5 Stage A — NO gate
revision, no new thresholds. Instrument note: the endurance runner
gains an EARTH1_STAGEA_SEEDS env override (mechanical, no scoring
change). On PASS: Stage B executes exactly per e89c98a.

## Stage B version-continuity declaration

The e89c98a specification is compatible with candidate v2 unchanged:
its broken twins, instruments, seeds, and gates reference the
candidate abstractly; the only binding change (COLLECTIVE target
law) does not intersect any Stage-B test definition. Stage B arms
run with the three candidate flags plus their per-test broken flag.
Gates unchanged.
