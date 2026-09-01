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
