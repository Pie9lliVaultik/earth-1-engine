# BENCHMARK A — PER-ITEM WIN/LOSS MAP v1 (2026-09-01)

Founder order: "I need the question by question answers and benchmark. Where we win,
where we lose." Full interactive table (676 items, per-country drill-down):
**https://claude.ai/code/artifact/ec8180f7-c077-4b97-b8d2-9e87864a98fa**
Raw: `data/cycles/sb1_items_{wvs_heldout,wvs_extended,goqa_dev}.{json,csv}` — computed
with score_sb1's own loaders and LOO ridge, so items reconcile with the committed
aggregates exactly.

## Headline counts

| estate | items | Earth-1 beats region-copy | outright best of all 4 |
|---|---|---|---|
| WVS held-out | 98 | 7 (7%) | 6 |
| WVS extended | 110 | 17 (15%) | 7 |
| Pew frame | 468 | **137 (29%)** | **64** |

## Where Earth-1 WINS (pattern, with receipts)

- **Interpersonal/outgroup trust**: Q62 trust-other-religion (−1.2pp vs region-copy),
  Q61 trust-strangers (−1.2), Q63 trust-other-nationality (−1.1) — the social-graph
  and force substrate carries real signal here.
- **Material hardship**: Q54 gone-without-cash-income (−0.9) — the economics substrate.
- **Pew event-era items with high within-region variance**: Iraq-war era judgments
  (−8.6, −7.9, −7.3pp), Islam-in-politics (−7.4) — where regional averaging fails,
  country covariates win.

## Where Earth-1 LOSES worst (pattern, with receipts)

- **Religious belief**: Q170 religion-exclusivism (+7.8pp), Q167 hell (+7.5),
  Q166 afterlife (+5.5) — NO religiosity input exists in genesis; region-copy wins
  because religion is regionally clustered.
- **Moral norms**: Q25 unmarried-couples-as-neighbours (+5.9).
- **Institutional confidence**: Q87 World Bank (+6.6).
- **Pew geopolitical favorability**: EU-understands-you (+25.7pp!), US-impact items
  (+9 to +16) — no geopolitical-alignment input.

## What this pins for B2

The loss map converts the B2 queue from cells to named inputs: (1) **national
religiosity** (Pew Religion — founder account pending) attacks the single worst WVS
family; (2) **geopolitical alignment** (e.g. UN voting-similarity, fetchable free)
attacks the Pew intl-relations losses; (3) institutional-confidence levels (V-Dem,
free). Each is one XI.A.2 fetch-and-wire cycle behind EARTH1_NATIONAL_INPUTS=v2.
