# EXTERNAL REVIEW VERIFICATION — 2026-09-08

Subject: "Earth-1 First-release analysis" (19 pp, reviewed archive
earth-1-engine-main (20).zip, sha 9314d76d…) + its evidence bundle
(17 files, synthetic-only probes). Verified against THIS tree at HEAD
dfe3b64 by six independent verification agents, every probe re-run
read-only (tiny worlds, temp dirs, synthetic keys/registries; no sealed
paths, no credential files). Probe scripts: scratchpad review_verify/.

## Verdict on the review itself

**Take it seriously: it is essentially all true.** 18 findings; zero
DISPUTED, zero stale. Two findings are stronger than the reviewer
stated: M08 has a THIRD failure mode they missed (basename-vs-key
substring match), and M01a's consumer inventory is larger than both
their list and ours (rent -> deprivation). The reviewer also correctly
fixed two errors in OUR OWN docs (EXPERIENCE-audit claim; stale scoreboard
citation is the one place THEY are stale — their 4.2 quotes 12.05/11.78
from SCOREBOARD_v1.md, superseded by A-FULL-1's 12.01/11.84).

## Verdict table

| id | finding | verdict | fix class | status |
|---|---|---|---|---|
| M01a | urban boolean inverted (1-census everywhere) | ALREADY_REGISTERED | PHYSICS-GATED | v1.1 cycle stands; consumer inventory corrected upward (addendum in DEFECT_URBAN_INVERSION.md); poverty anchors may move at fix — gate them |
| M01b | four age scales: engine 18+72a=54.0y; profile 18+82a=59.0y; model filter 87.6a=43.8y; answer cohort 100a=50.0y at a=0.5 | CONFIRMED (unregistered) | FREE | batch: route all conversions through generational._age_years |
| M02a | configstamp checks env strings, not loaded module state | CONFIRMED | FREE | batch: AND a loaded-state mismatch into is_freeze_09/assert |
| M02b | stamp omits 4 frozen coefficients (7 of 11 degrees covered) | CONFIRMED | FREE | batch: parse freeze09.env as single source of truth |
| M02c | v1 API hardcodes freeze label; no startup assert | CONFIRMED | FREE | batch: serve stamp(), refuse/degrade on mismatch |
| M02d | default birth ignores EARTH1_SUBSTRATE_FLAG | CONFIRMED | FREE | batch: default substrate from flag |
| M03a | hash blind to dynamic fields (civ.sex, cascade_residues, firm_distress): equal hashes, divergent next tick | CONFIRMED | FREE | batch: declare fields as dataclass members |
| M03b | rebirth keeps corpse's sex (field invisible to policy gate) | CONFIRMED | FREE | batch: declare + POLICY entry + slot-keyed draw |
| M03c | checkpoints accept missing checksum / tampered sidecar ("verified") / wrong physics label | CONFIRMED | FREE | batch: three load-path guards |
| M04 | public branch.run desynchronizes arms (treatment-only Memory consumes RNG); adapter path correct | ALREADY_REGISTERED in effect (published results used adapter) | FREE | batch: null-on-both-arms in run() or deprecate |
| M05a | _add_mutual clamps whole matrix to new edge weight | CONFIRMED — RECLASSIFIED: LIVE, not latent | **PHYSICS-GATED** | Implementation found the reviewer's 'latent' premise false: plasticity grows friends/weak weights past nominal daily and genesis stacks duplicates, so the clamp mass-collapses drifted weak ties to 0.15 EVERY migration day, partially undoing echo-chamber formation; the repair moves the frozen trajectory (bisect-proven). Fix shipped flag-gated EARTH1_REHOME_LOCAL_CLAMP=1 default-off; flipping it is a founder ruling alongside M01a |
| M05b | indexed Chronicle CSC cache never invalidated | CONFIRMED (indexed path off by default) | FREE | batch: provenance-check the cache; keep disabled for V1 |
| M05c | partner sampler IndexError on empty graph | CONFIRMED | FREE | batch: early return |
| M06a | geography delta_people lacks the 8.1e9/N conversion the global line uses | CONFIRMED | FREE | batch: same scale or relabel |
| M06b | day-30 fallback labelled "force units at day 180" | CONFIRMED (the line ABSTAINs in all committed artifacts) | FREE | batch: stamp actual day |
| M06c | SEM = std(ddof=1)/sqrt(n-1): all consequence ± ~3.3% too wide; GFC t=2.2 is really 2.28 | CONFIRMED | FREE | batch: divisor sqrt(n); frozen artifacts keep committed values, erratum noted |
| M06d | consequence path counts dead SLOTS (0% capture in 90-day probe) despite deathwatch existing | CONFIRMED | FREE | batch: thread DeathWatch through _run_pair |
| M07a | p = d_NO/(d_YES+d_NO) is direction-blind; under-calls on big-consequence events partially structural | CONFIRMED (registered design) | PHYSICS-GATED | readout-semantics change = founder ruling |
| M07b | binary path never reads fitted temperature; tier can say CALIBRATED anyway | CONFIRMED | FREE | batch: tier keyed to what binary consumes |
| M07c | conditional 2-outcome door KeyError('O0') — crashes real path | CONFIRMED | FREE | batch: YES/NO keys for 2 forks |
| M07d | requests write question_classes.json + mutate cached templates | CONFIRMED | FREE | batch: overlay file; deepcopy template |
| M08 | sealed guard inert (3 ways: wrong level, fail-open, basename-vs-key) | CONFIRMED | FREE | **FIXED THIS COMMIT** — fail-closed, nested entries, path-based match; tested against real registry semantics |
| M09 | install fails (flat-layout discovery); earth1-benchmark entry point dead; unconditional torch import | CONFIRMED | FREE | batch: packages.find, repoint script, importorskip |
| S01 | cross-tenant model overwrite; ../ path escape; raw token as owner | CONFIRMED | FREE | **FIXED THIS COMMIT** — id regex, ownership checks, hashed principal |
| S02 | async job id was a dead end (no retrieval route) | CONFIRMED | FREE | **FIXED THIS COMMIT** — GET /v1/jobs/{jid} |
| S03a | Bearer allowlist fails open to anonymous when empty; two disjoint auth systems | CONFIRMED | FREE | batch: fail closed unless EARTH1_DEV_OPEN=1; unify stores |
| S03b | /billing/usage discloses every key's usage to any caller | CONFIRMED | FREE | batch: auth + self-scope |
| S03c | webhook parses unsigned JSON without secret -> forged tier grants | CONFIRMED | FREE | **FIXED THIS COMMIT** — refuse unsigned |
| S03d | subscription cancellation never downgrades | CONFIRMED | FREE | batch: handle subscription_change |
| S04 | backup omits history.sqlite + model stores | CONFIRMED | FREE | batch: extend run_backup.sh list |
| 4.3 | sigma mislabel: noise_dist unit is the 95% HALF-WIDTH (1.96 SE); "3.78 sigma" = 7.41 SE | CONFIRMED (I re-verified by hand) | FREE | paper relabelled v3.2; ops docs carry forward with this note |
| 4.2 | MrsP is a LOO census-covariate ridge, not full MRP; serving path is a different estimator | CONFIRMED | FREE | paper corrected v3.2 |
| docs | EXPERIENCE-audit claim wrong; scoreboard superseded; 468 unique GOQA items | CONFIRMED | FREE | addenda appended; paper 468 v3.2 |

## Fixed in this commit (guard hardening, zero physics)

1. `_forbid_sealed`: fail-closed on unreadable registry, walks nested
   entries, matches on recorded paths. Tested: refuses goqa_judge /
   sbi theta (abs path) / prospective register; allows TRAIN/VALIDATION;
   503 on broken registry.
2. Model store: id regex `[A-Za-z0-9][A-Za-z0-9_-]{0,63}` (blocks
   traversal), 409 on cross-tenant recreate, 403/404 ownership checks on
   scenario, owner stored as sha256(key)[:12] — never the raw token.
3. Billing webhook refuses unsigned payloads.
4. `GET /v1/jobs/{jid}` serves async ask results.

## Remaining work, triaged

- **FREE batch (one named apparatus cycle, ~25 items above)**: age-scale
  unification, configstamp completeness, hash/checkpoint declarations and
  guards, branch-runner deprecation, graph fixes, measurement schema
  (units/SEM/DeathWatch), multiverse adapter fixes, packaging, auth
  unification, backup list. None touches frozen physics; all shift
  outputs of the SERVING layer, so run the apparatus cycle before any
  new published numbers from the API.
- **PHYSICS-GATED (founder rulings)**: M01a urban fix (v1.1, first tier,
  now with poverty anchors gated rather than assumed inert); M07a
  binary-readout semantics (any change alters registered answer
  behaviour).
- **Reviewer's release-gate table (G1-G10)**: adopt as the v1 release
  checklist; it is compatible with our governance and stricter than our
  current release_gate.py families.

## Errata to send the reviewer

Their 4.2 table cites the superseded SCOREBOARD_v1.md (12.05/11.78);
current board is BENCHMARK_A_FULL_v1.md (12.01/11.84, 468 unique items).
Everything else stands.
