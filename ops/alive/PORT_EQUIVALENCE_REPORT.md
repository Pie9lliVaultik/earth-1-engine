# PROGRAM 2 — PORT EQUIVALENCE: PASS

Lab candidate 76a574c (pinned worktree at 47ab046, three flags) vs
canonical port (42b61c3, flagless `live_one_day`). Tolerance as
registered: bitwise (0). Artifacts: prime `/opt/earth1-data/port_eq/`
(fingerprints every checkpoint); summaries in `data/port_eq/`.

| case | result |
|---|---|
| 1. KA-short, N=20k, seeds 8890 & 424243, 10 days, every day | **BITWISE IDENTICAL** (11 checkpoints each: all 8 force arrays, alpha, effective view, life/material, flourishing, adjacency, chronicle, cooldown map, residues, world hash) |
| 2. GEO-1 KA battery on canonical, N=200k | **ALL PASS** (T=B at reference, error 0.0; slopes exact 1e-17; no dynamic centering) |
| 3. PF-DECAY-2 KA battery on canonical, N=200k | **11/11 physics KAs PASS** (UNIT, KA2 level/plant, KA3, KA4, KA5 restart, KA6, KA8–KA11); KA0 see case 4 |
| 4. IT6 social-dynamics invariants (canonical it6 arm @8890, 120d + fork) | every frozen IT6 gate green: tau 5 / resid 0.065; rings 0.00704 / 0.00073 / 0.00055; sdr 0.599; α interior; unanimity 0.033; sat d120 0.0018. The registered reference `data/geo1/it6_all.json` proved DEFECTIVE (see below); replaced by `data/port_eq/it6_canonical_8890.json` as the continuity fixture |
| 5. Full 365 days, N=200k, dev seed 9301, every 10 days + final | **BITWISE IDENTICAL — 38/38 checkpoints**, day-365 world hash equal; canonical endurance census == recorded Stage A v2 END_9301 exactly (panels and census) |

## Reference defect found by this battery (disclosed, repaired)

Case 4's registered reference — the GEO-1 "IT6-ALL @8890" record —
was produced by an it6 arm config with no `residue` key, so the lab
runner popped `EARTH1_DECAY_RESIDUE`: that record ran candidate v2
with INSTANT-WRITE cascades, not the open-loop contract. The
canonical loop diverges from it from day 10 because the canonical
loop is the correct physics (less saturated, less unanimous: no
stored-force cascade writes). The GEO-1 IT12 rerun shared the gap.
Both are labeled INSTRUMENT-DEFECTIVE / NON-SCORABLE in
GEO_1_REPORT_AND_FREEZE_V2.md (amendment) and re-evidenced here on
canonical: IT12 COMPOSITE true-peak-normalized 0.595 ∈ [0.2, 0.6],
INTRINSIC 0.434, carrier 0.125/0.25 exact, KA1_delete 0.029
(`data/port_eq/it12_arms_canonical.json`). Stage A v2, Stage B,
Stage C, PF-DECAY-2 set the residue flag explicitly and are
unaffected — case 5's exact match to the Stage A v2 record proves it.
No physics was changed to obtain any agreement.

## Verdict

PROGRAM 2 PASS — canonical implementation == lab candidate 76a574c,
bitwise, over a full year at production scale. The laboratory
assembly (`field_lab`, `conviction_lab`, the it6/it11 patch paths)
is now temporary reference code to be archived in Program 3.
