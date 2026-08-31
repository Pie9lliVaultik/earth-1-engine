# SCOREBOARD v1 — opinion on instruments Earth-1 never calibrated on
2026-08-31 evening. 200k candidate flag set (mortality-board-green), 3 seeds,
LOO-by-country per item. Baselines per BIBLE v4.2 R-A: MrsP = census-covariate
ridge (registered tonight), naive grand-mean, region-copy. Tiers: ACCEPT <=7.0 /
GOOD <=5.0 / WIN <=3.5 pp. No LLM baseline anywhere. Pew direct microdata
PENDING_FETCH (login wall); the GAS/Pew frame arrives via the public GOQA
dataset. Coverage = 1.0 by construction (no abstention wired; named future change).

| estate | wave | items | Earth-1 MAE ± σ | MrsP | naive | region-copy | excess vs MrsP | tier | beats naive | estate sha | concordance sha |
|---|---|---|---|---|---|---|---|---|---|---|---|
| goqa_dev (GAS/Pew frame) | GOQA snapshot | 468 | 12.05 ± 0.09 | 11.06 | 12.02 | 10.31 | +0.99 | MISS | NO | a27e0cfececf | 775016524441 |
| wvs_heldout (national) | WVS-7 | 98 | 11.78 ± 0.20 | 11.18 | 12.80 | 9.70 | +0.59 | MISS | yes | 659a667552db | n-wtd cohorts |
| anes_dev | 2020 | — | PENDING_FETCH | | | | | | | | |

## Worst five cells (goqa_dev, seed 4242)
- 90.3pp — BR — economy
- 84.1pp — JO — democracy/governance
- 79.7pp — KW — democracy/governance
- 79.0pp — CN — other
- 77.0pp — GR — intl-relations

## Best five cells
- 0.0pp — BE — economy
- 0.0pp — JO — democracy/governance
- 0.0pp — TZ — other
- 0.0pp — UG — tech/climate
- 0.0pp — NG — democracy/governance

## Level-error decomposition — three largest cells (family × region × income)
- other × Western Europe × HIC: weighted share 10451.0 (n=978)
- other × Eastern Europe × HIC: weighted share 6730.4 (n=554)
- other × Middle East/N. Africa × LMIC: weighted share 5997.7 (n=396)

## Reading (data, not commentary)
Earth-1 12.05 ~= naive 12.02 on the Pew frame; census-MRP 11.06; region-copy
10.31 strongest on both estates. Distance to ACCEPT: ~5.1pp. These rows are the
morning's named-change queue, not tonight's.
