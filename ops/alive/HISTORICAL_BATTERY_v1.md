# HISTORICAL EVENT BATTERY v1 — scored rows (register order)
_Protocol: birth(T) on real archive news → frozen output → judge fetched → one pass.
Priors were committed in HISTORICAL_EVENTS_v1.json before any run._

## Row 1 — ARAB SPRING (T=2010-12-16, frozen pre-judge, scored 2026-09-02)

**What the population did (frozen):** sustained unrest — protest_risk +4.56 hot
localities (±0.63, t≈7), unrest intensity +489 hot-locality-days (±102); material
stress ordered Egypt > Morocco > Yemen > Algeria > Saudi > Tunisia
(hungry_by_country basis). 6 live / 13 abstain / 3 known-defect; 5 vintage flags.

**Judge:** real GDELT protest events (root 14) by country, 2010-12-17→2011-03-16,
archive-sha'd. 185-country overlap.

| basis | Spearman global (n=185) | Spearman MENA (n=16) |
|---|---|---|
| hungry_by_country | **+0.168 (p=0.022)** | +0.372 (p=0.16) |
| fear_by_country | +0.069 (p=0.35) | +0.303 (p=0.25) |

Real top5: US*, EG, TN, LY, YE · Model top5 (fear): YE, JO, MA, TN, SY ·
Model top (hunger): EG.

**Prior vs result:** prior said "geography partially right (ρ~0.55 lineage);
magnitude under; govs weak." Measured: partial confirmed — a significant but weak
global signal (ρ=0.17, p=0.02) carried by the HUNGER field, not fear; MENA ordering
right-direction and under-powered at n=16; magnitude qualitatively under (a
region-wide uprising ≫ +489 hot-days); regime chain not quantitatively scored per
its own prior. The interesting surprise: **material stress predicts real protest
geography better than the fear field does** — consistent with the whole campaign's
"material channels first" arc.

**Judge caveat (named for the next event, not applied retroactively):** raw GDELT
counts carry media-density bias (US #1 with 19.5k events — Wisconsin coverage);
the next event's prereg normalizes by each country's total event volume.

*Rows land here in register order as events freeze and score.*

## Row 2 — GFC (T=2008-09-14, 200k flagship, scored 2026-09-02)
Judge: the c-SHOCK-fetched WB unemployment series (sha fe7ea901), real 2008→2009
world delta +0.585pp. Model: Δunemployed **+449 ± 203 agents (t=2.2, right
direction)** ≈ +0.37pp of the labor frame → **magnitude ratio 0.64× — WITHIN 2×.**
11 live lines; movers DE/AU/SE (OECD-scoped scenario; within-scope ordering is the
content). Hungry +95 ± 21. Prior said "jobs right at low significance, 16 seeds may
lift" — CONFIRMED and lifted (5-rep t=0.7 → 16-seed t=2.2). Hope carries its
KNOWN-DEFECT stamp per the ledger.

## Row 3 — COVID (T=2020-02-28, 200k flagship, scored 2026-09-02)
Judge: same series, real 2019→2020 +0.999pp. Model: Δunemployed **+4,177 ± 230
(t≈18)** ≈ +3.5pp → **3.5× over — within the 5× band, direction emphatic.** Frame
caveat carried from c-SHOCK: real furloughs hid in the u-rate; the model has no
furlough state, so its layoffs SHOULD exceed the u-rate delta. Richest report of the
battery (13 live lines): hungry +1,916 ± 28 (≈ +78M world-scaled), fear +0.039.
Deaths line carries the epidemic-channel KNOWN-DEFECT. Prior CONFIRMED on all
counts (jobs real, deaths absent, mobility unmodeled).

## Row 4 — SVB (T=2023-03-08, 200k flagship, scored 2026-09-02, ruled framing)
**Forecast: p_model 0.302 on "contagion to ≥2 further banks within 30d" — resolved
YES** (Signature Bank closed 2023-03-12; provenance wiki-fetched, snippet sha
88a9e9b3; the market priced contagion higher). **The miss is real and specific: the
model was right about the fear and missing the plumbing.** Every material line
ABSTAINS, yet the US is the TOP force mover (0.0356 — 2× the runner-up): a
US-concentrated fear response with no deposit/interbank transmission to carry it
into balance sheets. The named v1.1 mechanism (interbank/deposit network, FDIC +
H.8 public data) was registered with the prior and is now evidenced. Prior
CONFIRMED: under-contagion, exactly as written.
