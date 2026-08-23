# BIBLE 0.8 — RE-MEASURE THE PHYSICS ON THE UNIFIED CANONICAL EARTH (execution note, frozen before running)

Bible row 0.8: "butterfly, FSLE, noise floor, consciousness profile —
same preregs, same thresholds; exit: the chaos chapter re-stated on the
real system." Stage H (ACCEPTANCE_BATTERY_0_8.md): "λ > 0, λ = 0, λ < 0
are all admissible outcomes; nothing is tuned to manufacture chaos."

System under measurement: Epoch 2 (uuid ad0e4af4-9cc5-4d1f-8f5e-
28710de6b731), physics `0.8-candidate-v3/39994f0-canonical`, main
633c5fd+. Registered snapshot: Epoch-2 day 30 (sha256 55a8d551…, world
hash 3627ea31…), byte-identical copy on prime
(`/opt/earth1-data/epoch2_day30`). The live trajectory is not touched.

## Instruments (unchanged definitions; configuration = canonical)

| measurement | instrument | start state | configuration | registered reading |
|---|---|---|---|---|
| butterfly | `butterfly_full.run` divergence/reach/entropy + `chaos.lyapunov_from`; perturbation = one employed agent (the middle employed index) loses their job; placebo = identical worlds | Epoch-2 day-30 snapshot, both worlds, RNG = persisted stream (identical draws) | `CANONICAL_DAY` only (no beta/residue/critical-fraction/relax overrides; the 0.2-era sweep rows are parameter exploration and are NOT run on canonical physics) | placebo divergence must be EXACTLY 0.0 (else HARNESS VOID); λ from the initial linear region; reach = fraction of agents with any force differing > 1e-12; "chaotic" flag as registered: λ > 0.01 ∧ max reach > 0.01 |
| FSLE | `fsle_test.trial` (R = 2, separation ‖ΔF‖₂, 8 trials, pick = i·7919 among employed) | same snapshot | `CANONICAL_DAY` | FSLE/day = mean ln2/T_double (0 where never doubled); reach; doubling days; trials doubled |
| noise floor | `noise_vs_scale.py` unchanged (sizes 50k/200k/600k, escalation scenario, 45 warm + 45 days, paired seeds 101/907) | fresh genesis at each size (the instrument measures scaling with size; a single live snapshot cannot) | canonical via `branch.run` | slope of per-country noise floor vs size: registered reading SAMPLE-LIMITED (rising) vs GENUINELY CHAOTIC (flat) |
| consciousness profile | `consciousness_profile.py` unchanged (12k, 25 days; phi-proxy, self-reference, novel coherence, anticipation, phase scan) | fresh genesis (the sever-the-world construction requires it) | canonical via `integration.STEP = CANONICAL_DAY` | five signatures reported as measured |

Scale note: butterfly and FSLE run at the full 4,000,000 on the real
snapshot (Bible: "on the real system"); at ~30 s/day, butterfly = 120 d
× 2 worlds, FSLE = 8 trials × 40 d × 2 worlds in parallel on prime.

## Discipline
No physics modified; no parameter chosen after seeing results; every
outcome admissible; instrument defects ⇒ VOID + repair + rerun.
Artifacts: `data/bible_0_8/`. Report: BIBLE_0_8_REPORT.md.
