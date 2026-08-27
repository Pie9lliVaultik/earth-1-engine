# PRODUCTION CANDIDATE 0.9 — "real-anchored" (founder: take it to production)
2026-08-27. Candidate physics assembled today, every calibration target
FETCHED from World Bank / PIP open APIs (data/anchors_worldbank.json,
registered EVALUATION_OUTCOME). Nothing authored from memory.

## What the candidate is
| component | flag | change |
|---|---|---|
| hardship gradient | EARTH1_HARDSHIP_MODE=gradient | deprivation = depth-of-shortfall × (1 − reserve cushion), replacing a binary gate that pinned 30.5% of the world at ≈1.0 |
| income calibration | EARTH1_INCOME_CALIBRATION=v1 | WAGE_LEVEL 2.1306, WAGE_LOG_SD 1.1995 — derived from PIP world median $9.27 and mean/median skew 2.33 |
| C2+ substrate v2 | substrate="c2plus_v1" (tables v2) | joint demographic draw, sex axis, WVS-measured education, material-income margin |
| H_poverty operator | (class 0) | household per-capita consumption, matching how PIP measures |

## Standing vs REAL data (20k × 180d)
| metric | REAL (fetched) | canonical v4.1 | candidate |
|---|---|---|---|
| median income/day | $9.27 | $3.97 | **$9.25** (1.00×) |
| poverty $8.30 | 46.1% | 90.3% | **48.8%** (1.06×) |
| poverty $4.20 | 18.9% | 57.4% | **27.0%** (1.43×) |
| poverty $3.00 | 10.4% | 35.1% | **19.1%** (1.83×) |
| crude deaths/yr | 0.76% all-ages | 2.24% | **1.31%** |
| unemployment | 4.81% | 8.44% | ~9% (RED) |
| mean age at death | LE 73.5 | 43.7 | ~48 (RED) |

## PROMOTION REQUIREMENTS (EPOCH_POLICY + VALIDATION_INHERITANCE)
The gradient is a **class-3 foundational** change; deprivation feeds
mortality, cascades, institutions, flourishing and migration. Owed
before Epoch 4 can carry it — none may be skipped:
1. 200k living-baseline battery (scale rung 2) — canonical vs candidate,
   paired seeds.
2. A-v2 DEVELOPMENT scoring on the candidate substrate (the registered
   judge of the population miss).
3. Benchmark B DEVELOPMENT event retest — B's magnitude gates were
   computed under the cliff form and must be recomputed.
4. Cascade-rate regression (cascades halved; confirm the mechanism is
   intact rather than merely quieter).
5. Full test suite + dynamics-identity KA for the default path
   (currently green: 1136 passed, default byte-identical).
6. Freeze as PHYSICS_VERSION 0.9-candidate/real-anchored, then Epoch 4
   birth under EPOCH_POLICY (new genesis, archived Epoch 3, restore
   rehearsal). Epoch 3 is NEVER mutated.

## STANDING RED (carried into promotion, not hidden)
M-LOWER-TAIL ($3.00 line 1.83×; floors/household structure thinner than
reality — next fetch: ILO social protection), M-UNEMPLOYMENT (~2×),
M-MORTALITY-AGE (deaths ~25 years too young; scoring BLOCKED_ON_DATA
until UN WPP / WHO life tables are fetched).
