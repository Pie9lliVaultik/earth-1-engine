# PROVENANCE / OBSERVABILITY AUDIT — identity_collapse, collective_surge

Read-only. Founder ruling 2026-08-23 (H-CASCADE-1 ACCEPTED as development
baseline; no thresholds/amplitudes/half-lives/cooldowns/hysteresis/reset
semantics changed; no dataset chosen; no simulation run). Sources: git
history f933c59 → HEAD, `data/*_prereg.json`, BIBLE.md, STATUS.md.

## Roadmap-language correction (recorded)

Stage C / CASCADE_IDENTITY_DIAGNOSTIC_1 / H-CASCADE-1 are an **E3
physics-resolution thread** opened by the Stage C expression-layer
finding. They are NOT the Bible's canonical 0.8 battery. True Bible 0.8
(canonical butterfly / FSLE / noise-floor / consciousness remeasurement
after 0.7 closure) HAS NOT STARTED. Earlier wording in STAGE_C_REPORT.md,
H_CASCADE_1_REPORT.md and SESSION_STATE.md that called this "the 0.8
battery" is superseded by this paragraph.

Ruling recorded: H-CASCADE-1 (39994f0) = accepted development baseline
for the next candidate. Incumbent 76a574c-canonical and all evidence
preserved. Not production promotion, not external validation.

## The lineage (one chain, five steps)

| step | commit | date | what changed |
|---|---|---|---|
| 1 | f933c59 "Builds 16-25: Emergence architecture + calibration benchmark" | 2026-08-12 | `thresholds.py` created with all five rules verbatim as today (predicates, thresholds, effects, cooldown, half-life). Detector: **national force MEAN** per country, pop ≥ 10, cooldown honoured, fires a `WorldEvent` into the event log. |
| 2 | a5ceedc ERRATUM + 5561287 FIX 1 | 08-18 | mean → per-agent participation fraction, MIN_PARTICIPATION 0.25 (Centola 2018 / Granovetter band), country scope. Real-world four-arm test REGISTERED (see §5). |
| 3 | 21dd0e4 FIX 1 result; 8a2286c LIFE SUBSTRATE | 08-18/19 | knife-edge FAIL at 0.25 → traced upstream to distribution width; life substrate widens tails. |
| 4 | ddc6b85 BUTTERFLY; chaos.py | 08-19 | cascade block re-inlined in `chaos.world_step`: instant permanent write (`forces += delta`), cooldown and half-life NOT read. `CRITICAL_FRACTION = 0.15` ("Pietro's spec … a cascade should be able to START before it has already won"). The chaos sweep's "operating point" (β 2.0, relax .25, residue .02, **crit 0.12**) is chosen in the same commit; 0.12 then propagates as the daemon STEP dict (825bb76, 59d716f, cdc6658) and becomes `CANONICAL_DAY` (ca95903). |
| 5 | debec56 SOCIAL FABRIC | 08-19 | country → **locality** (country·1000 + region·2 + urban): "a cascade belongs to a place". |
| 6 | probe-1 (RESIDUAL_PROBES_REPORT), PF-DECAY-1/2, H-CASCADE-1 | 08-21→23 | cooldown restored; decay restored as open-loop read-time overlay; episode-entry semantics (development). |

## Per-rule facts

### identity_collapse — FEAR>0.7 ∧ COLLECTIVE>0.6 → IDENTITY −0.15; cooldown 30; h 60

1. **Intended phenomenon**: none stated anywhere. The only text is the
   module docstring at f933c59: "Non-linear thresholds — phase
   transitions that produce cascades. When regional force means cross
   defined thresholds, events are injected into the event log. Those
   events modify forces, which may trigger further thresholds." The rule
   has no comment, no docstring, no design note, no BIBLE entry by name.
   The name is the whole specification.
2. **Original comments / rationale**: none. Created in a 25-build batch
   commit (f933c59, "Co-Authored-By: Claude Opus 4.6"); the commit body
   never mentions the rule.
3. **Why IDENTITY is the destination**: not documented. The effect map
   `{"identity": -0.15}` is authored with no derivation; the amplitude
   has no provenance (already tagged AUTHORED / REQUIRES PARAMETER
   PROVENANCE in the diagnostic registry).
4. **EVENT / EPISODE / STATE**: designed as an **EVENT** — the original
   detector emitted a `WorldEvent` (timestamped, region-patterned) with
   a `decay_half_life`, and the event log's `effective_deltas_vectorized`
   applied `force_deltas × 2^(−Δt/h)` as a stacked, decaying **overlay**
   (f933c59 `event_log.py`: "Events … decay over time, and stack to
   produce per-agent force deltas. Layer 0 genesis + Layer 1 accumulated
   experience"). I.e. the ORIGINAL semantics were exactly the open-loop
   decaying overlay PF-DECAY-2 later restored; the instant permanent
   write was introduced by the chaos.py re-inlining (ddc6b85), not by
   the rule's author. Cooldown was honoured from day one (f933c59
   `detect_transitions`), lost at ddc6b85, restored at probe-1.
5. **Real-world observable / dataset named as calibration target**:
   none for this rule specifically. The only registered real-world test
   (a5ceedc `data/threshold_erratum_prereg.json`) is generic to "the
   detector": arm A "real preference cascades with known timing
   (candidate set: Arab Spring 2011 by country, #MeToo 2017,
   same-sex-marriage tipping by country, Brexit/Trump 2016
   polarization) … precision AND recall > 0.5 on held-out regions";
   arm B timing rank-corr ≥ 0.3; arm C false-positive rate on control
   country-years < 20%; arm D critical fraction must transfer to
   held-out cases without refitting. Status line: "detector fix and
   test to follow; production untouched until the test passes".
   **This test was never run** (no script, data, or commit implements
   arms A–D; the only "Arab Spring" in the repo is a backtest scenario
   that injects forces, not a cascade-detection target). The
   locality-level detector went live (debec56 → daemon) without it.
6. **Empirical justification of trigger conditions (0.7 / 0.6)**: none.
   No commit, prereg, or comment derives them. Their only empirical
   contact is negative: 712301a measured them as unreachable by any
   national mean at genesis (max FEAR mean 0.602); a5ceedc measured
   5.0% of agents globally / 15.2% in the strongest country already
   satisfying the rule at genesis, unforced.
7. **New episode vs short flicker**: never defined. f933c59 had only
   the cooldown (country-level, 30 d); no hysteresis, reset duration,
   or exit condition exists in any version. The question is open by
   construction.
8. **Ongoing episodes at world initialization**: no semantics in any
   version. `last_fired` started empty (`-1e9` default ⇒ eligible
   immediately), so every pre-H-CASCADE-1 detector treated an
   already-hot genesis as a day-0 event. BIBLE.md notes only that the
   historical-severity test "needs no historical initialisation"
   (§ Relative historical severity). H-CASCADE-1's "already hot at
   init ⇒ state, no event" is the FIRST explicit initialization rule
   and is recorded as an experiment convention; an Epoch-2
   from-real-world start will need a data-initialized pre-genesis
   episode state (founder note 2026-08-23).

### collective_surge — COLLECTIVE>0.75 ∧ FEAR>0.6 → IDENTITY −0.10, TEMPERAMENT −0.08; cooldown 20; h 30

1–4. Identical situation: no stated phenomenon, no comment, no rationale,
   destination forces undocumented; designed as a decaying, stacking
   EVENT in the event log (same f933c59 mechanism).
5. **Dataset named**: none rule-specific; the same unexecuted four-arm
   registration applies. Note the two rules share the IDENTITY
   destination and overlapping predicates (both need FEAR high and
   COLLECTIVE high; collective_surge is the stricter COLLECTIVE / looser
   FEAR variant), so under any persistent high-COLLECTIVE/FEAR state
   they co-fire on the same localities — observed in Stage C (both
   ever-hot sets ≈ the same 70–78% of localities).
6. **Empirical justification of 0.75 / 0.6**: none. Measured contacts:
   a5ceedc 9.1% global / 29.2% strongest country satisfying at genesis;
   5561287 FIX-1 run: 4 countries over 25%; 8a2286c life-substrate
   sweep: 318 events at 0.30 vs 114 at 0.50 (detector-count sweeps,
   never compared with reality).
7. **Flicker**: undefined (cooldown 20 d only).
8. **Initialization**: none (as above).

### Shared parameters

- **critical_fraction 0.12**: not an empirical anchor. chaos.py (ddc6b85)
  documents the spec value 0.15 ("Pietro's spec … START before it has
  already won", i.e. below the 0.25 literature anchor); 0.12 appears in
  the same commit only as the chaos sweep's "operating point" grid row
  `(2.0, 0.25, 0.02, 0.12)` chosen for Lyapunov/reach behaviour, then
  inherited by the daemon and canonicalized by ca95903 as "the values
  the production civilization has actually lived under". Its sole
  registered sensitivity is the FIX-1 sweep (0.10→104 events … 0.30→0)
  on the PRE-life-substrate population.
- **Cooldowns 30/20 d, half-lives 60/30 d, amplitudes**: authored at
  f933c59 with no derivation; never changed; flagged AUTHORED.
- **Force geometry drift**: the thresholds were written against the
  pre-life-substrate, pre-GEO-1 distribution (COLLECTIVE mean then
  ≈0.63 base; today's stored COLLECTIVE mean ≈0.76–0.80 after the
  centered law) — the secondary cause already ruled.

## Summary table

| question | identity_collapse | collective_surge |
|---|---|---|
| phenomenon stated | no | no |
| rationale / comments | none | none |
| destination justified | no | no |
| designed as | decaying stacking EVENT (event log) | same |
| dataset named | none rule-specific; generic 4-arm test registered, never run | same |
| thresholds justified | no (only reachability measurements) | no |
| flicker vs new episode | undefined | undefined |
| init semantics | none before H-CASCADE-1 | none before H-CASCADE-1 |

STOP. No dataset chosen, no rule proposed, nothing calibrated, nothing run.
