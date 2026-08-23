# STAGE C METHODOLOGY + STAGE D HOLDOUT — LOCKED (frozen)

Frozen before any Stage A result has been opened (Stage A still
computing on prime at commit time). Companion to
ACCEPTANCE_BATTERY_0_8.md and STAGE_B_ADVERSARIAL_PREREG.md.

## Stage C — cascade census methodology (D2)

The measured object is C_t = F_effective − F_stored, per agent and
channel. Frozen measure set:
- duration above DESCRIPTIVE levels |C| > 0.05 (press-scale),
  > 0.20 (event-scale), > 0.45 (near-clip) — bins chosen from the
  contract's own scales (press coefficient, rule amplitudes, ±0.5
  clip), declared here BEFORE any Stage C data exists; they are
  descriptive bins, NOT gates;
- earthling fraction exposed (any |C| > 0.05, per channel and
  overall) over time;
- superposition count distribution (active residues per (agent,
  channel));
- rule attribution of C by channel (each rule's summed
  contribution);
- locality distribution (localities with active overlay; top-decile
  concentration);
- residue age distribution and half-life composition;
- clip occupancy: fraction of agents where the ±0.5 total clip or
  the [0,1] bound truncates C;
- peak vs terminal expression per channel;
- recovery: time from last residue expiry in a locality to
  |C| < 0.01 (analytic check: must be immediate — C is derived —
  so measured recovery tests the instrument, not the physics).
Gate policy (frozen): Stage C produces a measured scientific
characterization ONLY. If a hard effective-expression gate is later
justified, it must be derived from semantics/empirical evidence
independent of the Stage C scored dataset and preregistered before
scoring any fresh run against it. No "0.64 → threshold 0.65" logic.
Seed 8905 and the 0.64 observation remain development evidence.

## Stage D — the independent persistence holdout, NAMED AND LOCKED

Holdout = T2 of the frozen empirical target registry
(EMPIRICAL_TARGET_REGISTRY_0_8.md): post-9/11 collective fear decay
(NEJM 2001 national survey; NYC longitudinal PTSD series; reviews
PMC3386850, PMC8533613).
Provenance for independence: T2 was registered as VALIDATION in the
registry, frozen before IT12 existed; IT12's h*=10d was fitted to
T1 (day-10 persuasion point) plus the news-lifecycle recurrence
schedule; no T2 moment entered any calibration.
- Population: whole affected-nation cohort (event-scale scope).
- Construct: population FEAR-channel response to a single
  event-scale collective threat (chronicle-mediated, per T2's own
  registered Earth-1 mapping).
- Exposure definition (frozen): one canonical event-scale memory
  via the production chronicle path — FEAR signature at the frozen
  event scale (+0.50), salience 1.0, news-class half_life = 10d,
  nationwide scope, WITH production rehearsal and spread enabled
  and the frozen endogenous news-recurrence class (the IT12 frozen
  follow-up schedule as the news-lifecycle proxy); paired no-event
  control, common dice; N=200k; fresh seeds 9201–9203.
- Timepoints (frozen): population expression residual (normalized
  to peak) at days 30, 60, 90; and the carrier+expression tail at
  day 365 where horizon permits.
- Transformation (frozen): Earth-1 observable = cohort FEAR
  expression delta vs control, normalized to its peak — mapped to
  T2's symptom-prevalence decay SHAPE per the registry.
- Acceptance metric (frozen, from the registry's uncertainty band):
  two-component decay REQUIRED — fast-phase population half-life
  within 3–8 weeks (normalized residual crosses 0.5 between day 21
  and day 56), AND a persistent nonzero tail: residual at day 365
  in [0.15, 0.45] of peak. Hard structural exclusions: 1-day
  erasure; permanent saturation; monotone non-decay.
- Uncertainty: scored on the 3-seed mean; per-seed spread reported;
  the registry band IS the acceptance interval (no narrowing or
  widening after results).
This is validation, not calibration: h=10d, boost 0.35, press 0.02,
spread 0.06 and the recurrence class are all FROZEN inputs. A miss
is a FAIL → STOP AND DIAGNOSE naming the falsified hypothesis; no
retuning path exists inside Stage D.

## Sequence attestation

At the time of this commit, no Stage A output (log, verdict, panel,
or intermediate artifact) has been read. Ordering: master (334abf5)
→ this lock → Stage A opened. If the Stage A watcher delivers
results before this commit lands, that fact will be disclosed in
the commit message rather than concealed.
