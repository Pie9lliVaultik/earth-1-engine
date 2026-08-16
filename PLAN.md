# Build 29 — One Earth: production-readiness sprint

*Started 2026-08-16 evening. Rule: no new mechanisms until the existing ones
constitute one internally consistent Earth. Every fix lands with a semantic
test. Every claim re-measured after the fixes.*

## Verified-live findings being fixed (external audit, re-verified at HEAD)

| # | Fix | Status |
|---|-----|--------|
| 1 | Event force-key canonicalization + semantic injection test | ✅ 819e9f8 |
| 2 | Feedback direction from sign of the dominant force's question weight; trait deltas propagate to forces locally (no global recompute) | in progress |
| 3 | Regional/genesis priors preserved: retire `_recompute_forces` global rebuild from the feedback path | in progress |
| 4 | One Earth in the API: `/world/*` serves the same civilization as `/ask` (kill module-global `_world_state`) | queued |
| 5 | One country registry: `loop.py` off the 50-country legacy list | queued |
| 6 | G5 coupling honesty: matrix real or declared off in protocol | queued |
| 7 | Production wiring: corpus into `/ask/mind`, `BudgetMiddleware` mounted, pause switch dynamic | queued |
| 8 | Semantic test battery: feedback-sign both polarities, no-op identity, save/load continuation | queued |
| 9 | Re-measure: G5 event + demography legs on the fixed engine (first TRUE injection through the original harness) | queued |

## Deferred to next build (physics changes needing recalibration)
- Census-weighted force centering inside the model core
- Signed anatomy alongside force energy
- One named physics version (force-dynamics vs scalar) for G5 + API

## Accumulating autonomously meanwhile
- Daily heartbeats (launchd 09:07 + cron 09:37): world reads news, fast lane arms ≤7d markets
- Post-cutoff backtest grows toward n≥30 gate (n=8 tonight: engine 0.367 / market 0.152 / raw-LLM 0.498)
- Headline fetcher → G5 run #8 (A4) fires automatically when data lands
- WDI tide data → secular-drift physics (fit W5→W6, blind test W6→W7)

## On Hetzner IPs arriving
Migration night: world + Postgres + systemd timers + G4 from German IP
(Polymarket unblocked) + 1M genesis on AX162-R + training env on GEX131.
