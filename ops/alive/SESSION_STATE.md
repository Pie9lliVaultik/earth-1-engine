# WHERE THINGS STAND — read this immediately after BIBLE.md

## Document precedence (founder ruling, 2026-08-19)

| document | authority |
|---|---|
| `BIBLE.md` | governing architecture and scientific program |
| **`ops/alive/SESSION_STATE.md`** (this file) | **current execution checkpoint** |
| `ops/alive/DEPLOY_RUNBOOK.md` | the immediate procedure |

*Updated 2026-08-20, mid-0.7.*

## Phase 0 status

| phase | state |
|---|---|
| WP-0 → 0.6 | ✅ ACCEPTED, tagged (`phase0-0.5`, `phase0-0.6`, …). Acceptance reports in `ops/alive/`. Production world day ~1180+, 3.79M alive, running v1-unification. |
| **0.7a — current-hardware/software leg** | ✅ **COMPLETE** (founder ruling 2026-08-20): frozen 20-pair workload; restore/reproducibility/topology controls banked; bit-identical optimization done (serial 4M day 48.4s → 35.0s; ensemble projection 64m → 43-50m); prime PROVEN memory-bandwidth bound; <30m NOT achieved on this hardware — by evidence, not by lack of effort. No more prime squeezing. |
| **0.7b — hardware acceleration / final acceptance** | ▶ **OPEN**. Exit unchanged: 20 paired 4M 30-day futures <30 min wall-to-wall on an executor with earned correctness/equivalence evidence. Plan: rent higher-bandwidth node(s) → same frozen protocol → close. f32-v4 certification is an OPTIONAL acceleration branch (canonical f64 on faster hardware suffices to close). |
| **Pre-0.8 product-science gate: meaningful-outcome probe** | ▶ IN FLIGHT tonight (NOT a 0.7 deliverable). f64 paired recession probe (firm_health shock via existing mechanisms, India; placebo arm on smallest country). After its causal report: STOP — founder ruling gates both v4 and hardware provisioning. |
| 0.8 | ⬜ next after 0.7 closes. Queued diagnostics: FEAR≈0.978 saturation; −0.20 force shock ~98% erased in 3 days (over-restoring/pinned force field hypothesis, w/ diffusion-no-value + narrow-trait-variance audit findings); chaos onset seed-dependence (trajectory identity ≠ model equivalence — Technical Architecture paper material). |

## 0.7 progress (contract: prime = lab, CCX33 = sole writer, <30-min 20-pair ensemble)

1. **Backup/restore chain — ✅ CLOSED.** Checked-in `earth1-backup.timer`
   + `earth1-restore-rehearsal.timer` installed AND enabled on the box
   (old wrong-target unit replaced). Timer-driven backup exit 0. On-box
   rehearsal PASSED (day-1142 backup → checksums → canonical loader →
   whole civilization). Two-hop prime materialization PASSED. Corruption
   controls demonstrated: flipped bit → manifest check exit 1 AND
   `SnapshotError` from the loader. Two real defects caught and fixed by
   exercising it: TAINTED-dir selected as "newest" backup; loader ran on
   system python. **Fourth world found and retired**: `earth1-daily.timer`
   was ENABLED on the box (old substrate, last success 2026-08-19,
   wrote only `data/living/` — canonical home proven untouched).
   Units archived in `ops/legacy_archive/`; `single_writer` gate now
   scans systemd unit files AND names; box passes as canonical writer.
   NOTE: `/opt/earth1/data/living/` left in place as inert evidence
   (rename denied by permission policy); founder may archive/delete.
   NOTE: prime was NOT granted Storage Box credentials (permission
   policy); restores to prime relay through the box, which is also a
   defensible least-credential topology — founder may change.
2. **Reproducibility — ✅ built.** `earth1/manifest.py` records SHA,
   snapshot identity, schema, config hash, seeds, machine, workers,
   wall time, artifacts for every prime experiment.
3. **Workload — ✅ FROZEN before measurement.**
   `ops/alive/ENSEMBLE_PROTOCOL_0_7.md`: day-1142 backup, 20 pairs,
   common random numbers, +0.20 FEAR shock to most populous country,
   30 days/member, `live_one_day` + `CANONICAL_DAY`, full 4M. Runner
   `scripts/ensemble_paired.py` proven deterministic (identical runs →
   identical world_hashes). Prime staged: fresh clone `/opt/earth1-0.7`
   at the pinned SHA (main `/opt/earth1` checkout left untouched —
   carries stray lab files), snapshot at
   `/opt/earth1-data/snapshots/2026-08-20T074529Z-day1142` (checksums
   verified on prime).
4. **20-pair < 30 min** — ⏳ calibration subset running; then frozen run.
5. Optimization (only if miss; equivalence rule) — ⬜
6. Saturation study — ⬜
7. Machine-role gates — ◐ systemd scan + canonical allowlist done; run
   evidence on prime/laptop + prime-cannot-write-production proof due.
8. Acceptance report → tag `phase0-0.7` — ⬜

## Governing doctrine

`BIBLE.md` XI.A — NO DEAD-END RESULTS. Standing Rule 2: a test that
cannot demonstrate failure is not yet evidence. Git: everything to
`origin/v1-unification` immediately; `main` untouched until post-0.8.

## Open founder-side items

| item | status |
|---|---|
| RunPod token rotation | ⏳ owner-only (console) |
| WVS microdata registration | ⏳ gates R16; longest lead |
| FRED / ACLED keys | ⏳ |
| Destitution-bar ruling (34.5% measured vs 25% bar) | ⏳ |
| `data/living.retired` + Storage Box credential topology | see 0.7 notes above |
