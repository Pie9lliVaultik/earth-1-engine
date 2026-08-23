# H-CASCADE-1 — RESULT (development evidence; NOT canonical until ruled)

Registration: H_CASCADE_1.md (c96dd9e). Implementation: f84fb0d
(`earth1/alive.py` cascade block only; `EPISODE_ENTRY_RULES`;
`chronicle.cascade_episode_active`; `PHYSICS_VERSION =
0.8-candidate-v3/H-CASCADE-1`). Nothing else changed: thresholds,
0.12, pop≥10, amplitudes, cooldowns, half-lives, decay, clip, open-loop
overlay all verbatim.

## 1. Semantic KAs (scripts/h_cascade_1_ka.py, data/h_cascade_1/ka_results.json) — ALL PASS

| KA | result |
|---|---|
| KA1 persistent-hot (340 hot days > 10 cooldowns) | exactly 1 firing per scoped rule |
| KA2 recurrence (hot 5 / cold 40 / hot 5) | 2 firings, days 1 and 46 |
| KA2b re-entry inside cooldown (hot 3 / cold 5 / hot 3) | 1 firing (episode opens, cooldown guard holds) |
| KA3 cooldown elapsed while hot (95 days) | 1 firing |
| KA4 already-hot initialization (40 days) | 0 firings, episode state established; later cold→hot fires on entry (day 43) |
| KA5 save/load mid-episode (full world, canonical serializer) | restored == unsaved twin: same cooldown map, residues bit-identical, episode state equal, 0 duplicates |
| KA6 deepcopy (clone_world path) mid-episode | state equal, 0 duplicates over 60 hot days |
| KA7 unrelated rule (panic_cascade) | fires d0, d0+14, d0+28 — PF-DECAY KA3 contract verbatim |
| KA8 stored world (20k, seed 8890, 30d, full canonical loop) | world hash per day identical between H-CASCADE-1 and incumbent semantics; scoped fires 281 vs 527 (detector differs, substrate does not) |

Instrument notes (VOID-rule disclosure): two KA instruments were
repaired before passing — KA5 originally used a stripped world (the
serializer correctly refuses it) and KA1/KA5 originally read firings
from the residue list, which legitimately expires (h=60/30); firings
are now recorded cumulatively / from the never-expiring cooldown map.
No implementation change followed either repair. Test suite: 1,101
pass (test_cascade_cooldown retargeted to panic_cascade for the
cooldown contract + 4 episode-semantics tests added).

## 2. Characterization — seeds 9501/9502, 200k, 365d (data/h_cascade_1/)

Stored world unchanged at full scale: per-day hot sets for both rules
and the locality census are IDENTICAL between the incumbent A run and
H1 on every one of 365 days, both seeds; `sat_stored` identical at
every census panel; reach migration count identical (2,929). Every
stored-force diagnostic (Stage A v2 / Stage C) therefore carries over
exactly — the overlay is open-loop.

Firings (A → H1):

| rule | 9501 | 9502 |
|---|---|---|
| identity_collapse | 5,553 → 1,666 | 5,071 → 1,780 |
| collective_surge | 11,456 → 772 | 11,541 → 762 |
| both | 17,009 → 2,438 (−86%) | 16,612 → 2,542 (−85%) |

Hot-set prevalence: unchanged by construction (identical hot sets).

IDENTITY overlay (seed 9501 / 9502, A → H1):

| observable | day 180 | day 360 |
|---|---|---|
| residues per exposed person | 9.2 → 2.3 / 8.4 → 2.3 | 12.0 → 3.8 / 13.0 → 5.5 |
| p95 simultaneous residues | 16 → 7 / 16 → 7 | 24 → 11 / 24 → 11 |
| pop with ≥3 residues | 82% → 18% / 82% → 18% | 82% → 42% / 83% → 50% |
| mean C_IDENTITY | −0.24 → −0.075 / −0.23 → −0.056 | −0.24 → −0.079 / −0.24 → −0.054 |
| frac \|C_IDENTITY\| > 0.20 | 76.5% → 11.1% / 68.7% → 7.0% | 77.4% → 7.2% / 75.9% → 7.5% |
| frac > 0.45 | 0.7% → 0 / 1.4% → 0 | 0.3% → 0 / 2.7% → 0 |
| effective IDENTITY saturation | 0.75 → 0.063 / 0.62 → 0.041 | 0.68 → 0.044 / 0.63 → 0.047 |
| clip ±0.5 hit | 0.05% → 0 / 0.3% → 0 | 0.2% → 0 / 0.9% → 0 |
| at-bound effective (any) | 10.1% → 1.2% / 7.7% → 1.1% | 8.9% → 1.6% / 9.2% → 2.6% |

Per-agent IDENTITY exposure (9501 / 9502):
- ever exposed: 85.5% → 85.5% / 85.1% → 85.0% (UNCHANGED — see §3)
- episode duration median: 341 d → 95 d / 341 → 95; p95 365 → 273 / 284
- days exposed, median fraction of year: 0.94 → 0.59 / 0.94 → 0.34
- episodes per exposed agent median 1 → 2 (exposure is now intermittent,
  not one year-long block)
- year-end persistence: n_residues day 360: 9,204 → 3,118 / 9,186 → 3,433;
  pop with 0 residues 15% → 25% / 16% → 32%.
- recovery check after expiry: 0.0 both (overlay returns exactly to zero).

Reach (9501): direct 99.94% / indirect 0.06% of first exposures —
structure unchanged, fires 17,009 → 2,438.

Positive control (KA9): localities cold on their first eligible day
that later turned hot — identity_collapse 618/618 and 594/594,
collective_surge 463/463 and 468/469 fired on their exact entry day.
The single non-match (seed 9502, loc 50000, day 36) is a recorder
timing edge: a migrant arrived that day (pop 150→151); the detector
fired on the post-migration population on day 36, the hot-history
snapshot registered hotness from day 37. Detector correct.

## 3. Answer to the one registered question

Does correcting level-with-cooldown into episode-entry semantics
remove the repeated-event generator while preserving genuine episode
detection?  YES.

- The periodic pulse generator is gone: a continuously hot locality
  fires once (KA1/KA3); firings fell 85–86%; the −0.5-clipped,
  year-long IDENTITY plateau is replaced by a decaying overlay (mean
  −0.24 → −0.06/−0.08; >0.20 displacement 77% → 7%; saturation
  0.68 → 0.04; clip 0).
- Genuine entries are detected at 100% (2,143/2,143 after the recorder
  edge is accounted for).

What H-CASCADE-1 does NOT do — and was registered not to do:
- Ever-exposed stays 85%, because ~80% of the population lives in
  localities that ENTER the hot set at least once under the authored
  thresholds (secondary cause: threshold calibration, untouched).
- Residual stacking (3.8–5.5 residues/person at day 360) comes from
  FLICKER: the broad hot set sits at the 0.12 line, so localities
  close and re-open episodes after short cold gaps (identity_collapse:
  4,002 / 4,604 entries, median cold gap 2 d, 63% of re-entries after
  ≤3 cold days; collective_surge 1,203 / 1,120 entries, median gap
  3 d). The retained cooldown blocks most of these (1,666 / 1,780
  fires from 4,002 / 4,604 entries) but one fire per cooldown window
  survives in flickering localities (p90 5–6 fires per locality/year).
  This is the SAME threshold-calibration cause seen from the other
  side — a population sitting on the trigger line — not a defect of
  episode semantics, and no hysteresis/reset parameter was added per
  registration.

## 4. Status

Development evidence only. Canonical physics remains
76a574c-canonical until a ruling. Next decision belongs to the
founder: threshold calibration against empirical event incidence.
STOP.
