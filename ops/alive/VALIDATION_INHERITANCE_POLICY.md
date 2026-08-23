# VALIDATION INHERITANCE POLICY (permanent, from 2026-08-23)

Principle: **validation evidence is inherited unless the new change can materially affect the mechanism or observable that produced that evidence.** A localized correction gets localized regression; a foundational change gets broad revalidation. A bug fix does not reset Earth-1 to zero — it invalidates only the evidence that depends on what changed.

| class | examples | required |
|---|---|---|
| **0 — non-dynamic change** | API routes, docs, storage/observability metadata, instrument changes proven not to touch canonical state (proof = dynamics hash identical before/after on a pinned trajectory) | no physics rerun; the world-hash pin may be re-pinned with the dynamics-hash proof cited |
| **1 — localized physics correction** | dead agents no longer participating as living agents | written dependency analysis (`*_CHANGE_IMPACT.md`), targeted regressions on the stages whose mechanism the change touches, inherited evidence for the rest (each inheritance justified in one line), escalation to full rerun of a stage only if a targeted regression shows unexpected divergence or a gate becomes marginal |
| **2 — subsystem physics change** | new transmission law, new memory carrier, changed conviction dynamics | full rerun of the affected subsystem's validation stages and of every downstream stage that consumes its outputs; unrelated subsystems inherit |
| **3 — foundational physics change** | replacing the force evolution law, changing civilization update topology, changing fundamental agent interaction mechanics | broad/full revalidation (the frozen campaign from Stage A) |

Rules: (1) every change is classified in writing BEFORE any run; (2) "INHERIT" requires a stated reason that the tested mechanism is unaffected, never the absence of a reason to rerun; (3) targeted regressions are paired (old vs new physics from identical starting worlds and random streams) and scored against the already-frozen gates — no new thresholds; (4) OUTSTANDING stages are scientific work owed once, run on the candidate intended for deployment, in the frozen order; (5) deployment of a candidate requires its validated-or-inherited A/B/C/H equivalents — outstanding stages do not block deployment unless a ruling says so; (6) instrument defects found during regression ⇒ VOID + repair + rerun (Standing Rule 2 unchanged).
