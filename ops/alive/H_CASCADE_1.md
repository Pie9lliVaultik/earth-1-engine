# H-CASCADE-1 — EPISODE-ENTRY EVENT SEMANTICS (PREREGISTRATION)

Status: FROZEN BEFORE IMPLEMENTATION. Founder ruling 2026-08-22
("HOT-SET DIAGNOSIS ACCEPTED. MOVE TO THE BIBLE HYPOTHESIS STEP").
Evidence base: CASCADE_HOTSET_STRUCTURE_ANSWER.md (38ef1f1).

## 0. Bookkeeping precondition — locality denominator reconciled

- "≈2,300 localities" (CASCADE_IDENTITY_DIAGNOSTIC_1_REPORT.md, trace
  section) was an unmeasured estimate written from the key formula
  country·1000 + region·2 + urban; it was never a census. Corrected in
  place.
- Measured (hot_history_A_9501.pkl, every recorded day): 879 occupied
  localities (878 on day 0), population sum = 200,000 on every day —
  every agent is represented. 194 countries × 1–7 observed genesis
  regions per country × 2 urban flags = 886 theoretical cells; 879 occupied.
- Cascade-eligible (pop ≥ 10, the verbatim existing rule): 869
  localities holding 199,955 agents; 10 localities with <10 residents
  hold 45 agents and are ineligible by the existing rule (unchanged).
- Verdict: theoretical-vs-occupied count, not missing data, not an
  instrument error. CONTINUE.

## 1. Scientific ruling (founder, accepted)

PRIMARY STRUCTURAL CAUSE — persistent level conditions are converted
into repeated discrete events by cooldown-only re-arming.
SECONDARY CAUSE — authored absolute thresholds are no longer calibrated
to the current stored-force geometry (NOT addressed here).
AMPLIFIERS — persistence + additive superposition + amplitude (NOT
addressed here). Migration/network spread ruled out (99.9% direct).

## 2. Hypothesis

H-CASCADE-1: a rule named as an event fires on ENTRY into an episode,
not repeatedly while the same level condition remains true.

Scope: `identity_collapse` and `collective_surge` ONLY. Every other
cascade rule keeps the incumbent cooldown-only semantics bit-identically.

## 3. Preserved verbatim (not touched by this experiment)

trigger predicates; numerical thresholds; critical_fraction 0.12 and the
pop ≥ 10 eligibility; amplitudes (effects); cooldown_days (30 / 20);
decay_half_life (60 / 30); destination forces; residue decay
2^(−Δt/h) and 0.01 expiry; open-loop read-time overlay; superposition
and ±0.5 clip; detector substrate = STORED forces.

## 4. The only change — meaning of a firing

Incumbent:  hot ∧ (day − last_fire ≥ cooldown)            → FIRE
Candidate, per (rule, locality), with persistent boolean episode state
`active`:
    cold → hot  : episode opens; FIRE iff (day − last_fire ≥ cooldown)
                  (cooldown is kept as the secondary guard; if it
                  blocks, the episode still opens and NO fire occurs)
    hot  → hot  : NO new event, regardless of elapsed cooldown
    hot  → cold : episode closes; rule becomes eligible for a future
                  episode (no hysteresis band, no reset-duration: the
                  episode closes on the first day the predicate is false)
    cold → hot again : new event, subject to the existing cooldown
"hot" keeps its exact incumbent definition (frac ≥ 0.12 ∧ pop ≥ 10).
A locality that drops below pop 10 is "cold" for this purpose.

Initialization: if the chronicle carries no episode state (fresh
genesis, or a snapshot written before this change), the first cascade
step RECORDS the current hot set as open episodes and fires nothing for
the two scoped rules on that step. Historical consequences belong to
the lived timeline; day-zero re-detection is not synthesized.

State: `chronicle.cascade_episode_active` — a set of (rule_name,
locality) keys, stored on the Chronicle (already a PERSISTENT_FIELD),
so it travels through `save_world`/`load_world`, timeline
snapshot/restore (same serializer), `clone_world` (`copy.deepcopy`),
and `ScenarioBranch.fork`. Deterministic: derived only from stored
forces and prior state, no RNG. Versioning: `PHYSICS_VERSION` is
bumped to `0.8-candidate-v3/H-CASCADE-1` (development, NOT canonical
until ruled); the persistence blob records it. SCHEMA_VERSION stays 1
(no World field added/removed; the Chronicle payload gains an
attribute that older code would carry inert and newer code initializes
when absent).

No new parameter is introduced.

## 5. Semantic KAs — frozen; all must PASS before any characterization

Synthetic harness: a small world where the detector substrate is
driven directly (stored forces planted per locality per day) so the
predicate's hot/cold trajectory is exactly controlled.

KA1 persistent-hot: cold→hot once, stays hot > 10 cooldown periods
    (≥ 330 days for identity_collapse) → exactly 1 firing per scoped
    rule in that locality.
KA2 recurrence: cold→hot (day a) → cold → hot (day b, b − a ≥ cooldown)
    → exactly 2 firings.
KA3 cooldown: continuously hot for 3 cooldowns → 0 additional firings
    after the first (firings == 1 across the whole window).
KA4 initialization: world initialized with the locality already hot,
    no episode state → after the first step: episode recorded, 0
    firings; subsequent hot days → still 0.
KA5 restore: save mid-episode with `save_world`, `load_world`, continue
    hot → 0 new firings; restored world's firing sequence over the
    following 100 days equals the unsaved twin's, bit-identical
    residues.
KA6 branch: `copy.deepcopy` mid-episode → 0 new firings in the clone
    while hot; clone's cascade state == parent's.
KA7 unrelated rules: for the three non-scoped rules, firing days and
    residues are bit-identical to the incumbent code path on the same
    planted trajectory (including cooldown-repeat firing).
KA8 stored world: a 30-day canonical run (200k not required; 20k, seed
    8890) produces a bit-identical stored-force trajectory (world hash
    per day) between incumbent and H-CASCADE-1 — the overlay is
    open-loop, so only chronicle cascade state may differ.
KA9 (positive control, in the characterization): at least one
    locality in seeds 9501/9502 that is cold at its first eligible day
    and later becomes hot produces a firing on its entry day.

Decision rule: any KA FAIL → instrument or implementation defect →
repair and re-run; no characterization until ALL PASS.

## 6. Characterization (development evidence only)

Seeds 9501 and 9502, 200k, 365 days, canonical loop with H-CASCADE-1,
the Stage C census instrument unchanged
(`scripts/stageC_census.py`) plus the hot-history recorder. Report
against the Stage C incumbent numbers: firings per rule; hot-set
prevalence (unchanged by construction — the predicate is untouched);
ever-exposed population; simultaneous residues per person; effective
IDENTITY displacement (|F_eff − F_stored| distribution, fraction
> 0.20); effective saturation; episode duration of the overlay; year-end
persistence; all eight stored-force health diagnostics.

Expected if H-CASCADE-1 is right: firings of the two rules collapse
from ~17k to ≈ the number of episode ENTRIES (≤ ever-hot localities +
genuine re-entries); residues/person falls toward ≤ 1–2 transient;
IDENTITY displacement decays on the 60/30-day half-lives instead of
holding at the −0.5 clip; stored-force diagnostics unchanged. The hot
set itself will remain broad (secondary cause, not addressed) — that
is NOT a failure of this experiment and will NOT be tuned away.

## 7. Explicitly out of scope

Threshold calibration; amplitude, half-life, cooldown, stacking, or
clip changes; any parameter search; canonicalization (requires a
ruling); Stage D; Epoch 2.
