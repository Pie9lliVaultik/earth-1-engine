# GOQA-40 polarity & binarization audit (2026-07-31)

Method: every stored ground-truth item was re-derived from the original
Anthropic/llm_global_opinions (GOQA) source distributions (`selections` +
`options`) and compared against three candidate cuts:

- 4-point confidence/interest scales: `top2` (1–2 = YES, correct), `top3` (1–3),
  `bottom2` (inverted).
- 1–10 justifiability scales: `6–10` (correct), `2–10` (any justification),
  `1–5` (inverted).

An item is flagged when the stored values track a cut other than the correct
one (lower MAE against the wrong cut, and/or near-zero / negative correlation
against the correct cut across countries).

## Verdict

**No polarity inversions found.** Every justifiability item (Q176–Q194) and
every confidence item correlates *positively* with the correct cut; the
inverted cut always correlates negatively. Reverse-coded texts (Q254 proud,
Q27 satisfaction, Q121, Q131, Q142, Q240) are stored in the already-flipped
"YES = agree/important/proud" direction, matching the seed-corpus text.

**Two binarization errors found — both a top-3 cut where top-2 is correct:**

| ID | Item | Stored cut | Correct cut | Global YES before | after |
|----|------|-----------|-------------|-------------------|-------|
| Q222 | Interest in politics (1 very … 4 not at all) | 1–3 | 1–2 | 82.1% | 43.0% |
| Q65 | Confidence in the press (1 great deal … 4 none) | 1–3 | 1–2 | 81.2% | 38.1% |

Evidence: for Q222 the stored values match the source top-3 cut (MAE 0.15) and
correlate **negatively** with top-2 (r = −0.12); Q65 matches top-3 (MAE 0.18)
while sibling confidence items (police r = 0.88, government r = 0.92) match
top-2 cleanly.

Corrected file: `supabase/functions/benchmark-globalopinion/ground_truth_v2.json`
(regenerate with `python3 scripts/fix_goqa_binarization.py`).

## Source-unvalidated items (kept, but excluded from the validated subset)

Stored values could not be reproduced from GOQA under any cut (r < 0.2):
**Q64** (armed forces), **Q194** (death penalty), **Q199** (jobs scarce — GOQA
option order is Agree/Disagree/Neither, not 1/2/3), **Q176** (unentitled
benefits), **Q186** (tax evasion). These are WVS7-microdata-derived cells with
no matching GOQA panel; flagged as unverified, not corrected.

## The five worst performers, after correction

| Q | Item | Earth-1 | Truth | MAE (pp) | Diagnosis |
|---|------|---------|-------|----------|-----------|
| Q222 | Interested in politics | 38.8% | 45.6% | **14.9** | was a bad cut — fixed (was ~37 pp) |
| Q65 | Confidence in press | 38.9% | 41.5% | **14.9** | was a bad cut — fixed |
| Q254 | Proud of nationality | 46.7% | 88.6% | 43.0 | ground truth correct → **engine compression** |
| Q187 | Bribery justifiable | 54.7% | 13.0% | 41.7 | ground truth correct → engine compression |
| Q180 | Casual sex justifiable | 50.8% | 9.7% | 41.1 | ground truth correct → engine compression |
| Q73 | Confidence in major companies | 73.6% | 39.1% | 37.0 | ground truth correct (r = 0.78 to top-2) → engine bias |

Q254/Q187/Q180 all sit within a few points of 50% against floor/ceiling truth:
this is Problem 1 (compression to 45–55%), not a mapping fault.
