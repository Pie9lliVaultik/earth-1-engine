# DISTANCE FROM HUMANS — 2026-09-02
_One question: how far is Earth-1 from what real people actually said and did. Frozen 0.9 + adopted flags, 200k, 3 seeds, leave-one-country-out, named-entity abstention ON (2,198 cells abstained, excluded from both sides). Bible tiers exist and are not the subject of this report. Baselines are context columns only._

## HEADLINE

- Majority agreement with humans: 83.5% of 21,776 scored (item,country) cells.
- Within the survey's own 95% sampling noise: 14.2% of the 12,669 cells where survey n is known (WVS estates).
- Median distance: 3.78 noise units (MAE 10.65pp).
- Best family tech/climate (2.97σ), worst religion/values (3.91σ); best region Oceania (2.28σ), worst East Asia (4.66σ).
- Events: 40% of resolved-event direction calls match what happened (5-rep battery; most sub-significance — see events table); protest geography rank-corr with real onsets ρ=0.552 (p=0.005).

## BY ESTATE

| estate | cells | majority-agree | within-noise | median σ-dist | MAE pp | signed pp | ≤1σ / 1–2σ / 2–4σ / >4σ |
|---|---|---|---|---|---|---|---|
| wvs_heldout | 5,807 | 84.6% | 13.8 | 3.8 | 10.84 | -0.04 | 13.8/13.6/24.7/47.9 |
| wvs_extended | 6,862 | 83.7% | 14.6 | 3.75 | 10.32 | -0.0 | 14.7/14.8/23.2/47.3 |
| goqa_dev | 9,107 | 82.7% | n/a (no cell n) | n/a | 10.77 | +0.19 | n/a |

## BY FAMILY (signed direction is the finding)

| family | cells | majority | median σ | MAE | signed pp (+ = model too high) |
|---|---|---|---|---|---|
| tech/climate | 735 | 90.5% | 2.97 | 8.33 | +0.84 |
| religion/values | 1,163 | 86.0% | 3.91 | 9.98 | +0.29 |
| security | 553 | 87.9% | 3.65 | 10.24 | -0.04 |
| democracy/governance | 2,861 | 83.7% | 3.79 | 10.51 | +0.14 |
| other | 14,161 | 83.4% | 3.81 | 10.74 | -0.03 |
| intl-relations | 1,162 | 79.7% | 3.71 | 11.36 | +0.28 |
| economy | 1,141 | 79.5% | 3.55 | 11.51 | +0.21 |

## COUNTRIES — 10 CLOSEST / 10 FARTHEST (median σ-dist, ≥40 cells)

**closest:** GB (2.04σ), CY (2.16σ), AU (2.24σ), NZ (2.32σ), RO (2.48σ), AR (2.64σ), EC (2.69σ), UY (2.8σ), RU (2.82σ), SK (2.88σ)
**farthest:** BD (4.79σ), TH (4.88σ), TN (4.97σ), CN (5.0σ), MM (5.01σ), MN (5.27σ), EG (5.58σ), ID (6.05σ), VN (6.27σ), TJ (7.85σ)

## ITEMS — 20 CLOSEST / 20 FARTHEST (WVS, median σ-dist)

### CLOSEST
- Q155 (1.31σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q157 (1.53σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q173 (2.08σ, religion/values, 63c) Are you a religious person?
- Q11 (2.22σ, other, 63c) Should children be encouraged to learn imagination at home?
- Q189 (2.27σ, other, 62c) Is it justifiable for a man to beat his wife?
- Q93 (2.28σ, other, 59c) PENDING_FETCH (WVS-7 official codebook)
- Q61 (2.29σ, other, 63c) Do you trust people you meet for the first time?
- Q109 (2.3σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q104 (2.49σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q255 (2.5σ, other, 62c) PENDING_FETCH (WVS-7 official codebook)
- Q58 (2.53σ, other, 63c) Do you trust your family?
- Q44 (2.59σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q161 (2.6σ, tech/climate, 62c) Do we depend too much on science and not enough on faith?
- Q101 (2.61σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q111 (2.62σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q153 (2.64σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q192 (2.66σ, religion/values, 62c) Is terrorism as a political, ideological or religious means justifiable?
- Q219 (2.67σ, other, 60c) PENDING_FETCH (WVS-7 official codebook)
- Q92 (2.67σ, other, 62c) PENDING_FETCH (WVS-7 official codebook)
- Q110 (2.68σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
### FARTHEST
- Q170 (8.02σ, religion/values, 62c) Is the only acceptable religion your religion?
- Q167 (7.89σ, other, 61c) Do you believe in hell?
- Q25 (7.81σ, other, 62c) Would you object to having unmarried couples living together as neighbours?
- Q22 (6.98σ, religion/values, 61c) Would you object to having homosexuals as neighbours?
- Q20 (6.41σ, other, 63c) Would you object to having people who have AIDS as neighbours?
- Q113 (6.31σ, democracy/governance, 61c) Are state authorities in your country involved in corruption?
- Q136 (6.3σ, other, 62c) Are drugs sold in the streets in your neighbourhood?
- Q201 (6.23σ, other, 63c) Do you get political information from daily newspapers?
- Q230 (6.22σ, other, 62c) PENDING_FETCH (WVS-7 official codebook)
- Q193 (6.19σ, other, 59c) Is casual sex justifiable?
- Q133 (6.08σ, other, 62c) Is alcohol consumed in the streets in your neighbourhood?
- Q253 (5.91σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q140 (5.84σ, other, 61c) PENDING_FETCH (WVS-7 official codebook)
- Q258 (5.84σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q33 (5.83σ, other, 63c) PENDING_FETCH (WVS-7 official codebook)
- Q139 (5.79σ, other, 61c) PENDING_FETCH (WVS-7 official codebook)
- Q74 (5.69σ, other, 63c) Do you have confidence in the civil service?
- Q175 (5.62σ, other, 62c) PENDING_FETCH (WVS-7 official codebook)
- Q67 (5.61σ, other, 63c) Do you have confidence in television?
- Q18 (5.57σ, other, 63c) Would you object to having drug addicts as neighbours?

## FAMILY × REGION (median σ-dist, ≥30 cells)

| family \ region | Central Asia | East Asia | Eastern Europe | Latin America | Middle East/N. Africa | North America | Oceania | South Asia | Southeast Asia | Sub-Saharan Africa | Western Europe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| democracy/governance | 3.49 | 5.15 | 4.21 | 3.0 | 4.57 | — | — | 4.29 | 4.19 | 3.29 | 3.55 |
| other | 4.52 | 4.71 | 3.0 | 3.49 | 4.15 | 4.37 | 2.16 | 4.27 | 4.71 | 3.67 | 3.19 |
| religion/values | 4.73 | 5.11 | 4.38 | 3.29 | 3.9 | — | — | 4.2 | 4.37 | 4.36 | 3.11 |
| security | — | — | — | 3.54 | 4.16 | — | — | — | — | — | — |
| tech/climate | 4.44 | 3.79 | 2.24 | 3.11 | 2.62 | — | — | — | 4.99 | — | 1.98 |

## EVENTS — DISTANCE FROM WHAT HAPPENED

From the committed flag-battery t-table and RETRODICTION_v1 (events with |t|<1 are indistinguishable from no-response at 5 reps — the honest 'within its own uncertainty' analog):

| event | observable | model direction right? | significant? |
|---|---|---|---|
| covid_2020 | jobs | YES | yes (t=+2.2) |
| covid_2020 | poverty | YES | borderline (t=+1.3) |
| covid_2020 | displacement | YES | yes (t=+3.1) |
| covid_2020 | hope | NO | no (t=+0.3) |
| covid_2020 | deaths | NO | no (t=+1.0; channel absent) |
| gfc_2008 | jobs | YES | no (t=+0.7) |
| gfc_2008 | poverty | NO | no (t=−0.5) |
| gfc_2008 | hope | NO | yes-wrong-sign (t=+2.1) |
| arab_spring | govs/displacement/poverty | NO | no (all |t|≤1.2) |

Direction agreement: 40% of scored calls (4/10); of the SIGNIFICANT responses (|t|≥2): 2 right-signed, 1 wrong-signed. Protest geography vs real GDELT-verified onsets: Spearman ρ=0.552, p=0.005, 13× separation, placebo clean.

_Context columns (naive / region-copy / MrsP) are in cells.csv per cell at item granularity._
