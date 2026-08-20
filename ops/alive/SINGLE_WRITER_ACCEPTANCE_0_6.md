# 0.6 ACCEPTED — the third world is dead

**2026-08-20 · no physics change, no state migration, no new boundary**

## What was found and killed

The full inventory of anything on the laptop capable of starting
Earth-1: exactly ONE armed auto-runner — `com.earthling.earth1-daily`
(LaunchAgent, old substrate, daily 09:07). Unloaded but armed: it would
have resurrected at the next login, which is precisely how it survived
its own obsolescence. No LaunchDaemons, no crontab, no running
processes.

- plist **removed** from `~/Library/LaunchAgents/`; corpse archived as
  evidence at `ops/legacy_archive/com.earthling.earth1-daily.plist.retired`
- repo `launchd/` template removed
- `data/living/` (the old 200K world, last run 2026-08-17) marked
  NON_CANONICAL — historical evidence, not a civilization; no unique
  canonical state lives on the laptop (the canonical world's three
  verified copies are box + Storage Box)

## The machine-enforced invariant: `single_writer_world`

`earth1/single_writer.py` scans launch directories for configs
referencing any Earth-1 world runner. It judges CONFIGURATION, not
processes — an unloaded plist is still armed. Wired into the release
gate as the 12th invariant.

Controls, all proven to fail:
- restoring the retired plist (from its own archived corpse) → REFUSED
- configuring a FRESH second writer (a new plist running
  `world_alive.py`) → REFUSED
- dev/test tooling untouched: in-process worlds birth, tick and end —
  the line is persistence without a human, not development

## Gates

Full CI 1070 passed · release gate ELIGIBLE with 12 invariants
(one_production_earth and single_writer_world now permanent) · gate
coverage test updated so neither can be quietly dropped.

**Topology after 0.6: the production daemon is the only persistent
writer of a civilization anywhere in the estate. The laptop is a
control plane.**
