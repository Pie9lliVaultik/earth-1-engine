# Epoch-0 backup record — the first off-box copy of the living world

**2026-08-19T14:22:38Z · world day 240 · 3,970,839 alive of 4,000,000 slots**

The canonical 4M civilization has an off-site copy for the first time in
its existence. Obtained **while Epoch 0 kept running** — no stop, no
world-days lost — per the founder's simplification: the daemon saves
every 30 ticks, so a completed snapshot already existed on disk.

## What was copied

Source `167.233.77.48:/opt/earth1/data/alive/` → Storage Box
`u652120:earth1/alive/epoch0-day240/`, 6,108,370,904 bytes at
298 MB/s.

| file | bytes | sha256 |
|---|---:|---|
| `world.pkl` | 5,718,592,773 | `7ae853d66c31f5deec53ff8431bc6bef5ebe0449f6b5117e0fd74ab77edf55ea` |
| `adj.npz` | 389,778,037 | `75da611d0a16008f3a6c0f57edb3aafab3b26157913d89c35ef1e4af21822246` |
| `state.json` | 94 | `08e77fb199aadb607f2e4b1ca914ea92a62abd77de9220ada9e2ea80226c41cf` |

`state.json` contents:

```json
{"day": 240, "pop": 4000000, "seed": 42, "alive": 3970839,
 "saved_at": "2026-08-19T14:22:38Z"}
```

## Verification — independent, not inferred

Hashes were recomputed **on the Storage Box itself**, not taken from
rsync's exit code. rsync's success proves transport; only a digest
computed at the destination proves integrity. All three matched
byte-for-byte.

### The negative control (Standing Rule 2)

A green checksum counts only once the check has been shown to fail on
its known failure case. Both realistic corruption modes were exercised
against the real artifact:

| control | result |
|---|---|
| clean copy vs reference | **MATCH** ✓ |
| 1 byte flipped mid-file, **size unchanged** | `783753d1…` → **REJECTED** ✓ |
| truncated 94 → 93 bytes (partial-transfer mode) | `b0db229e…` → **REJECTED** ✓ |

The size-preserving byte-flip matters: it proves the verification is not
merely comparing file sizes.

## Two findings from the capture

### 1. The v0 save is not atomic — an active risk, every 30 minutes

The copy was very nearly taken mid-save. Observed live:

```
14:21:27  adj.npz   153,650,094      (growing)
14:22:29  adj.npz   389,778,037      (growing)
14:22:31  world.pkl 1,394,717,273    (TRUNCATED from 5.7 GB, rewriting)
14:22:37  world.pkl 5,718,592,773    (complete)
14:22:38  state.json                 (written last — the completion signal)
```

The pre-0.0c `save_world` **truncates `world.pkl` in place** and
rewrites ~5.7 GB. For that entire window — recurring **every 30
minutes** — no complete snapshot of the civilization exists on disk. A
crash, OOM or power loss inside it loses the world outright, because the
previous good copy has already been destroyed.

This is precisely what 0.0c removes: write to `.tmp`, atomic `replace`,
and the sha256 sidecar written **last** so its presence proves the save
completed. Until Epoch 1 is deployed, the risk is live.

*Method note for any future capture: on a v0 world the completion signal
is `state.json`'s mtime advancing, since it is written after the pickle.
Do not copy on file-size stability alone.*

### 2. The Storage Box held 120 MB

Independent confirmation of the backup defect. `earth1-backup.timer` has
been firing green for weeks against `data/living/` — the retired 200K
opinion world. 120 MB of a 1.0 TB box was in use. The 6.1 GB
civilization had never been written to it.

The instrument worked perfectly and watched the wrong Earth.

## Status against the Epoch 1 acceptance criteria

| # | item | state |
|---|---|---|
| 1 | frozen code provenance | ⬜ deployment not run |
| 2 | **verified off-box `data/alive/` backup** | ✅ **PASS** |
| 3 | **corrupted-copy control demonstrably fails** | ✅ **PASS** |
| 4–10 | continuity boundary, v1 snapshot, perturbed-field control, restart equality, recurring backup, restore rehearsal, override removal | ⬜ not run |

**Epoch 1 does not exist.** Items 4–10 require mutating operations on
the world box (`git commit`, service install, `systemctl stop/start`)
which are currently being refused. The safety net, however, is now real:
if anything goes wrong from here, day 240 is recoverable off-site with
verified hashes.
