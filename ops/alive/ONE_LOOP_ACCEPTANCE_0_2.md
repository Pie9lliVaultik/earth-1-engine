# 0.2 PRODUCTION ACCEPTANCE — one world loop

**2026-08-19 · VERDICT: ACCEPTED**

There is one definition of a civilization day. Deployed `ca95903` at
world day 553; accepted at day 562 after a live window.

## The four closing criteria

| criterion | evidence | verdict |
|---|---|---|
| tick budget ≤ 60 s/day | median wall spacing 60.0 s; **compute 31.5 s/day at 4M** (measured both entry points on prime — identical); max 61.0 s is second-precision timestamp quantization of the pacing loop | ✅ |
| restart continuity exact | `ca95903 · day 562 · rng_continued True · dirty False` | ✅ |
| boundary count unchanged | 2 continuity events (day-284 annulled + real), 1 remediation — no new records | ✅ |
| canonical config in force on production | the startup journal record itself carries `beta 2.0, residue 0.02, critical_fraction 0.12` = `CANONICAL_DAY`, config-hashed | ✅ |

## Production-scale observational identity

Two copies of the real day-553 4M world, same dice, one stepped through
`chaos.world_step`, one through `live_one_day`:
**bit-identical world hash (`b603e9f1…`) and identical RNG stream
states.** Any caller entering through the wrapper enters the real
living civilization — there is nothing else to enter.

## The finding that outgrew the task

The Bible knew `beta 1.0 vs 2.0`. The audit of defaults found worse:
`live_one_day` imported its `residue`/`critical_fraction` defaults FROM
`chaos.py` (0.01/0.15) while production ran 0.02/0.12 — so **every bare
`live_one_day(w, rng)` caller (branch, backtest, timeline, hormuz,
assimilate, every research script) studied a world with different
physics than the world it claimed to study.** The configuration existed
in five places; it now exists in one (`alive.CANONICAL_DAY`), consumed
by object identity, with divergence CI-refused.

## Scientific rule honoured

No chaos/FSLE/butterfly numbers were compared across this change — the
instrument itself changed. 0.8 re-measures everything from scratch;
the six measurement scripts are migrated to Worlds and banner-marked.

## Status

Epoch 1 ✅ → 0.0a ✅ → 0.0b ✅ → 0.0d ✅ → 0.1 ✅ → **0.2 ✅** →
0.3 release gate begins now.
