# V1 UNIFICATION AUDIT — WP-0

**Branch:** `v1-unification` · **Audited commit:** `e7545f8` · **Date:** 2026-08-19
**Scope:** audit only. No physics changed, no file edited outside this document.
**Status:** ✅ **SIGNED OFF 2026-08-19** by the founder, with three amendments
(§A below) and a re-ordered execution sequence. Amendments are binding and
override the body of this document where they conflict.

---

## §A — FOUNDER RULING (2026-08-19), binding

### Execution order (supersedes Part 8 and BIBLE Part VIII's ordering)

```
credential rotation  →  0.0e provenance gate  →  0.0c state/persistence
  →  0.0a/0.0b/0.0d aging, rebirth, fabric  →  One-Earth integration
  →  0.8 physics re-measurement  →  benchmarks may begin accumulating evidence
```

Note **0.0c now precedes 0.0a** — persistence invariants land before the
demographic clock. 0.0e is promoted to *Phase 0.0 / provenance gate*: everything
after it is meaningless if we cannot say which source tree the civilization is
executing.

### Amendment A — N2 is broader: the daemon has the same defect

The audit reported N2 against `timeline.restore` (where `presence`/`mobility`
become `None`). It applies equally to the **always-on daemon**:
`scripts/world_alive.py:74-127` saves `climate`/`flourishing` but still does not
save `presence` or `mobility`. On restart they do **not** become `None` — worse,
`birth_world()` at `:106` silently creates *new* presence/mobility state before
the saved state is restored at `:107-108`. So:

> **S_t(before restart) ≠ S_t(after restart), without advancing time at all.**

This merges audit items **N2 + N16** into one defect with two faces, and both
belong to **0.0c**. The founder confirms the audit's recommendation: persistence
must be **schema-driven**, not another hand-maintained field list. Supporting
evidence already in the tree — `CIV_ARRAYS` (`scripts/world_alive.py:65-71`) also
omits the five optional `Civilization` fields (`religiosity`, `marital`,
`employed`, `ideology`, `social_class`). A hand-authored list will keep losing
new state as the world grows.

### Amendment B — extract the clock, not the trait physics

Do **not** lift all of `generational.py:181-194`. Verified boundaries at
`e7545f8`:

| lines | content | disposition |
|---|---|---|
| **181-185** | `d_age = dt_years/_AGE_SPAN`; `civ.age = clip(age + d_age)`; `age_years`; `civ.age_bucket = digitize(...)` | ✅ **EXTRACT** — this is the unambiguous missing clock |
| **187-192** | `for t, g in _AGE_GRADIENTS.items(): apply_trait_delta(...)` — openness −0.08, risk_appetite −0.12, desire_intensity −0.30, conscientiousness +0.10, agreeableness +0.05, extraversion −0.06, neuroticism −0.04 per age-unit | ❌ **DO NOT EXTRACT** — behavioural physics, not a correctness fix |
| **193-194** | `civ.forces[:, EXPERIENCE] = civ.age` | ⚠️ **DEFERRED — see the open question below** |

Phase 0 ships `advance_age(...)` maintaining **age and age_bucket only**.

> **Governing rule:** *Bug? Fix it. Contradiction? Fix it. Architectural or
> behavioural preference? Don't silently change the model.*

### ✅ EXPERIENCE — RULED 2026-08-19: leave it alone

**Ruling:** `advance_age()` touches **only** `age` and `age_bucket`. Do **not**
re-assert EXPERIENCE from age. In the living world EXPERIENCE has become a
genuine dynamical state receiving contributions from curiosity, travel,
propagation, circumstances, feed and contagion; replacing it from age would
**erase lived history**.

N10 therefore moves to 0.8 — but the competing arm is *not* "overwrite EXPERIENCE
from age." The scientific question is whether the stateful EXPERIENCE channel
needs **decay / mean-reversion** versus its current pure-accumulation law.

*(Original analysis retained below, since it is the reasoning the ruling rests
on.)*

### Open question as originally raised — EXPERIENCE

The ruling says `advance_age` may also maintain *"definitionally age-derived
state such as EXPERIENCE."* **In the old substrate that is safe; in the living
world it is not**, and the audit must flag it rather than choose.

`generational.py:193-194` re-asserts `forces[:, EXPERIENCE] = civ.age` as an
identity map. But in the living world EXPERIENCE is a **live dynamical channel
that six modules write every day** — `flourishing.py:243-244` (`+= 0.10 *
curiosity`), `mobility.py:170-171` (`+= 0.01` per flyer), plus `propagate`
(`alive.py:143`), the circumstance relax (`:173`), `feed.py:137` and
`contagion.py:210`.

Re-asserting the identity map daily would **overwrite all six** — deleting live
behaviour. That is exactly the silent model change Amendment B forbids. Yet
leaving it alone means EXPERIENCE and age remain decoupled (audit defect **N10**:
EXPERIENCE ratchets upward with no decay consumer, since
`PERISHABILITY_HALF_LIFE[EXPERIENCE]=4000` has no live consumer).

Neither option is a pure correctness fix. **Recommendation: `advance_age` touches
age and age_bucket ONLY in Phase 0**; the EXPERIENCE identity re-assertion joins
the **0.8 registered A/B** alongside conviction decay. Awaiting ruling.

### Amendment C — 0.1(c) conviction decay: make the truth explicit, activate at 0.8

`influence.py:107` (`- decay * 0.0`) contradicts its own docstring and
`CONVICTION_DECAY = 0.02` (`:43`). But activating it changes α_{t+1}, and
therefore the conviction kernel, influence, polarization, cascades and possibly
the chaotic regime. **That is physics.**

Phase 0 marks isolation decay as **disabled/unadjudicated in code and docstring,
leaving output bit-identical**. Phase 0.8 runs the registered A/B — A = decay
disabled (current), B = decay active — on identical worlds, seeds and forcing,
measuring conviction distribution, camp persistence/extinction, propagation,
macro stability, FSLE/chaos diagnostics, and benchmark consequences. **Promote B
only if the evidence earns it.** Do not turn it on because the docstring says it
was intended.

### Founder's independent verification, and what remains uncertified

Independently confirmed against the codebase: `answer.py` zero importers; the
`generational_tick` hazard (*"two incompatible demographic authorities"*); N2.

**Not certified:** the remote-only claims — box on `14401ea`, exactly 133 commits
behind, and `/etc/systemd/system/earth1-alive.service` existing there — require
direct machine evidence unavailable in the founder's environment. *(This audit's
evidence for them is the SSH transcript logged in the Appendix; the
repository-side half — no service file in git — is independently confirmed.)*
A full pytest collection timed out founder-side, so **899/616 remain
this-audit-only**; the founder counted **894 explicit `test_*` functions** and
independently confirmed **zero** direct test references to `earth1.alive`,
`birth_world`, `live_one_day`, `Chronicle`, mobility, contagion, or the living
timeline. The load-bearing conclusion is agreed either way: **the most important
runtime has essentially no CI protection.**

---

## How to read this

This document is the entry-point graph, state schemas, persistence field lists,
test gaps, and exact edit sites required by BIBLE v4.1 §16 (WP-0). It was
produced by five parallel read-only investigations of the repository at
`e7545f8`, reconciled, with every Bible-contradicting claim re-verified by hand
before inclusion.

It follows Standing Rule 11: **a design document does not outrank current code.**
Where the Bible and the code disagree, the code wins and the disagreement is
recorded in **Part 1**. Part 1 is the most important section — it contains four
findings that change what Phase 0 has to do.

Evidence labels are E0–E5 per BIBLE §1. Everything below is **E1 (executable code
path, read)** or **E3 (measured artifact)** unless marked otherwise. Nothing here
is E2 — there are no semantic tests yet; creating them is task 0.3.

---

## Part 0 — Preflight confirmations

| check | method | result |
|---|---|---|
| Live world ticking | `systemctl is-active`, `/var/log/earth1-alive.log` | ✅ **active**, **day 110**, 3,991,874 alive, unemp 9.2%, gini 0.667, entropy 3.0849 |
| Test suite collects | `python3 -m pytest --collect-only -q` | ✅ **899 tests in 9.6 s** (Bible says 894 — stale by 5) |
| Prime reachable | `ssh`, `nproc`, `free`, `uptime` | ✅ 96 cores / 503 GB, **load 0.08** — still idle |

Two preflight side-findings, both recorded in Part 1: the world box is **133
commits behind** this branch (§1.1), and the laptop launchd job is **dormant but
armed** (§1.4).

---

## Part 1 — Where the Bible is wrong at `e7545f8`

Four corrections. Each was verified by hand, not inherited from a subagent.

### 1.1 The live world runs code that is not this commit — and its unit file is not in the repo

**CRITICAL. Not in the Bible at all. This is the finding with the widest blast radius.**

The world box is running **`14401ea`** — 133 commits behind `e7545f8` — with a
dirty tree in which `earth1/alive.py`, `earth1/answer.py`, `earth1/assimilate.py`
and others are **staged-but-uncommitted adds** (`A` in `git status`). The living
substrate was hand-copied onto the box, not deployed from a commit.

```
box:     /opt/earth1 @ 14401ea + dirty ("A earth1/alive.py", "M data/...")
laptop:  e7545f8
git merge-base --is-ancestor 14401ea e7545f8  →  YES (box is behind, not divergent)
git rev-list --count 14401ea..e7545f8         →  133
```

I hashed the nine live-path files on both machines to determine whether this
audit describes the running world:

| file | box | laptop | verdict |
|---|---|---|---|
| `scripts/world_alive.py` | `7eeca4e5` | `7eeca4e5` | identical |
| `earth1/alive.py` | `e09b3081` | `e09b3081` | identical |
| `earth1/memory.py` | `6e825814` | `6e825814` | identical |
| `earth1/influence.py` | `8b56b32d` | `8b56b32d` | identical |
| `earth1/health.py` | `0342ba11` | `0342ba11` | identical |
| `earth1/timeline.py` | `fc618407` | `fc618407` | identical |
| `earth1/generational.py` | `9429379e` | `9429379e` | identical |
| `earth1/institutions.py` | `76773d01` | `1b36cfc2` | **differs** |
| `earth1/branch.py` | `9bc4a98f` | `9b1d5bc0` | **differs** |

I diffed both differing files against the defects this audit reports:

- **`institutions.py`** — box is 358 lines, laptop 361. The difference is a
  **3-line offset only**. War's cause code is `= 5` at box `:268` / laptop `:271`;
  the migration block (`MIGRATION_RATE_YR` `:50`, `dest_pool` box `:334`/laptop
  `:337`, `civ.country[idx]` box `:336`/laptop `:339`) is character-identical.
  **Every 0.1(d) and 0.0d finding holds on the running world.**
- **`branch.py`** — changed by `e7545f8` itself ("Backtest corrections"). Not
  imported by the daemon; affects no live-path finding.

**Conclusion: this audit is valid for the running 4M world.** But that had to be
*proven*, and it will not stay true. Two consequences:

1. **`earth1-alive.service` is not in the repo.** `find . -name "*.service"`
   returns only `ops/supervisor/earth1-supervisor.{service,timer}`. The unit
   exists solely at `/etc/systemd/system/earth1-alive.service` on the box
   (`ExecStart=/opt/earth1/.venv/bin/python3 /opt/earth1/scripts/world_alive.py`,
   `ALIVE_POP=4000000`, `ALIVE_PERIOD=60`, `ALIVE_SAVE=30`, `Restart=always`).
   BIBLE §20 requires *"deployment-as-code for the living daemon: checked-in unit
   file, health endpoint, restart policy, state lock, deployment manifest with
   commit SHA and physics version."* **None of that exists.**
2. **There is no way to know what the world is running without hashing it.**
   Standing Rule 10 (provenance stamping) is unenforceable while the deployed
   tree is untracked.

> **Proposed new task 0.0e — pin the deployment.** Check in
> `ops/alive/earth1-alive.service`; add a deploy manifest stamping commit SHA +
> physics version into `state.json` at every save; make the daemon refuse to
> start on a dirty tree. **This must land before 0.0a**, because otherwise we
> will fix aging on the laptop and have no guarantee the box received the fix.

### 1.2 `answer.py` is an orphan — the Bible's stated reason for keeping `tick.py` is void

BIBLE:777 justifies keeping the dead-engine shells because
*"`tick._make_mutable` (imported by the **live** `answer.py`)"* still lives there.

The import is real — `earth1/answer.py:231`. But:

```
$ grep -rn "earth1\.answer" --include="*.py" . | grep -v "^./earth1/answer.py"
[empty]
```

**`answer.py` has zero importers repo-wide.** No API route, no script, no test,
no other `earth1` module. There is no `tests/test_answer.py`. It is not live; it
is dead code holding a live-looking import.

**Consequence for 0.5:** the retirement rationale must be rewritten. `tick.py`
survives because of `living.py:33`, `g5.py:36`, `api/deps.py:31` and 9 test
files — *not* because of `answer.py`. And 0.4 ("repoint the opinion path") is
not a repointing job: `answer.py` has no traffic to repoint. It is a **wiring
job on a module that has never been connected**.

### 1.3 `generational_tick` cannot be wired into `live_one_day` as written

BIBLE:115 (task 0.0a) says *"wire `generational_tick` (or equivalent) into
`live_one_day`."* The parenthetical is load-bearing and must be taken.

`generational_tick` (`generational.py:146-155`) does **three** things:

1. **aging** — `generational.py:181-194` (the part we want)
2. **its own Gompertz mortality** — `generational.py:197-201`
3. **its own rebirth into freed slots** — `generational.py:226-282`

Blocks 2 and 3 **never touch `health.alive`** (verified: `grep -n "\.alive" earth1/generational.py`
returns nothing). Wiring the whole function into `live_one_day` would:

- **double the death rate**, on top of `health_tick`, `weather`, `mobility`,
  `flourishing` and war;
- **reincarnate agents whose `health.alive` is still `True`**, silently
  overwriting living people;
- **collide with `_be_born`** over the free-slot pool.

**The fix is an extraction, not a wiring.** Lift `generational.py:181-194` into a
new `aging_tick(civ, dt_days)`; wire only that.

### 1.4 The laptop's third world is dormant but armed — and the climate fix is misdated

- **launchd:** `com.earthling.earth1-daily.plist` is present in
  `~/Library/LaunchAgents/`, but `launchctl print gui/501/com.earthling.earth1-daily`
  returns *"Could not find service."* It is **not loaded** — but a plist in
  `LaunchAgents` is loaded at next login, so 0.6 is a file deletion, not a
  `bootout`. The Bible's "running daily" (§II.3) is **not currently true**; the
  job last ran 2026-08-17 (`data/living/heartbeat.log`, day 3→4).
- **Misdated fix:** BIBLE:24 dates the climate/flourishing persistence fix to
  08-19. `git log -S'"climate": w.climate'` returns exactly one commit —
  **`d3d2a0c`, 2026-08-18 23:09:25 +0200**. The irony is load-bearing: **the same
  commit that fixed climate/flourishing persistence is the commit that introduced
  `presence` and `mobility` unpersisted.** The defect class was re-committed in
  the patch that fixed its predecessor. This is why 0.0c needs a *schema-driven*
  save, not another hand-maintained field list.

---

## Part 2 — Entry-point graph

### 2.1 The two substrates, as actually reachable

```
LIVING SUBSTRATE                          OLD SUBSTRATE
─────────────────                         ─────────────
[world box] earth1-alive.service          [laptop] com.earthling.earth1-daily.plist
  └─ scripts/world_alive.py:292              └─ scripts/heartbeat.sh:13
       └─ alive.birth_world / live_one_day        └─ scripts/world_daily.py:53
            └─ 17 live modules                         └─ living.LivingWorld
                                                            └─ advance.advance_world:275
  [manual] scripts/backtest_run.py:24                            └─ tick.world_tick:19
  [manual] scripts/hormuz.py:25                                       └─ engine.run_question:15
  [manual] 19 other living scripts                                         ├─ forces.project_all:19
                                                                           └─ diffusion.diffuse:20
                                                                    ├─ coupling:18
                                          [running] uvicorn earth1.api.main:app
                                            └─ api/deps.py:31 → tick.WorldState
                                                 └─ 31 of 33 routes → engine

SHARED: genesis.py · types.py · thresholds.py        (calibration._build_features is NOT shared — see §2.4)
```

### 2.2 FastAPI surface — 31 of 33 substantive routes reach the dead engine

`earth1/api/deps.py:19-35` is the single resolution point, and **both** of its
branches are old:

```python
deps.py:23   if os.getenv("EARTH1_LIVING") == "1":
deps.py:27-29    from earth1.living import LivingWorld    # → tick.WorldState
deps.py:31-34  from earth1.tick import WorldState; WorldState.create(...)
```

`.env` contains only `ANTHROPIC_API_KEY` — **`EARTH1_LIVING` is unset**, so even
the aspirational branch is dead and the running uvicorn serves a *fresh
in-memory* `WorldState`, not even the persisted one. `alive.World` is never
constructed anywhere under `earth1/api/`.

| route group | file | count | substrate |
|---|---|---|---|
| `/ask`, `/ask/segment`, `/ask/freetext`, `/ask/mind` | `routes/ask.py:17,35,52,99` | 4 | OLD (`engine`) |
| `/forecast/*` (multiverse, perishability, timeline, scenarios, tree) | `routes/forecast.py:23,42,117,140,189` | 5 | OLD |
| `/lab/*` (superposition, order-effect, cube, layer-scrub, evolve) | `routes/lab.py:16,30,43,63,87` | 5 | OLD (`diffusion`, `forces`, `dynamics`) |
| `/loop/*` | `routes/loop.py:24,67,78,121` | 4 | OLD |
| `/receiver/*` | `routes/receiver.py:32,50,67,82,113` | 5 | OLD |
| `/world/*` | `routes/world.py:58,98,142,169,190,214` | 6 | OLD (`advance`→`tick`) |
| `/observatory/standing-readings` | `routes/observatory.py:22` | 1 | OLD |
| `/health`, `/civ` | `api/main.py:73,79` | 2 | OLD |
| `/forecast/events` | `routes/forecast.py:174` | 1 | neutral (static) |
| `/observatory/questions` | `routes/observatory.py:12` | 1 | neutral (static) |
| `/predictions/*`, `/billing/*` | `routes/predictions.py`, `billing.py` | 10 | DB-only, no substrate |

**0.5's exit criterion** — *"every production surface answers from the same world
UUID/hash as the daemon"* — therefore covers **31 route handlers across 9 files**,
not the three named in the Bible.

### 2.3 Retirement blast radius, per old module

Import-site counts, classified. This is the cost table for 0.5.

| module | sites | live | API | bench | tests | scripts | other `earth1` | cheapest? |
|---|---:|---|---|---|---:|---|---|---|
| `engine.py` | **78** | `world_daily.py:94` | 7 files | 4 | 34 files | 13 | 10 | ❌ hardest |
| `forces.py` | 22 | — | `lab.py:56` | `g5.py:64` | 6 | 3 | 7 | ❌ |
| `tick.py` | 17 | via `living` | `deps.py:31` | `g5.py:36` | 9 | 3 | 3 | ❌ |
| `living.py` | 10 | `world_daily.py:53` | `deps.py:27` | — | 2 | 2 | — | medium |
| `dynamics.py` | 7 | — | `lab.py:95` | `benchmark.py:767` | 3 | — | 2 | medium |
| `advance.py` | 6 | — | `world.py:64` | `g5.py:167,538` | — | 1 | `living.py:275` | medium |
| `diffusion.py` | 6 | — | `lab.py:55` | — | 2 | — | 3 | medium |
| `graph_dynamics.py` | 4 | — | via `observatory` | — | 2 | — | `tick.py:20` | ✅ near-leaf |
| `coupling.py` | **3** | — | — | — | 1 | — | `tick.py:18`, `advance.py:42` | ✅ **cheapest** |
| `event_generation.py` | 3 | — | — | — | 1 | — | `tick.py:21` | ✅ near-leaf |
| `perishability.py` | **2** | — | `forecast.py:11` | — | 1 | — | — | ✅ **cheapest** |

**The hardest edge is not in this table.** `earth1/__init__.py:1-4`:

```python
from earth1.engine import (
    build_civilization, build_genesis_civilization,
    run_question, run_segment, run_multiverse,
)
```

**Every** `from earth1.X import ...` in the repo — including
`from earth1.alive import birth_world` — executes `engine.py`, which pulls
`forces`, `diffusion`, `population`, `genesis`, `llm_gateway`. The old substrate
cannot be retired while this line stands, regardless of the call graph. **Emptying
`earth1/__init__.py` is the first physical step of 0.5**, and it is a one-line
change that will surface every latent implicit dependency at once.

### 2.4 Shared-module ruling — one correction, one addition

| module | Bible says | verdict |
|---|---|---|
| `genesis.py` | shared | ✅ **confirmed** — 119 sites; old `tick.py:14`, living `alive.py:56,238` |
| `types.py` | shared | ✅ **confirmed** — `Civilization` + `Force` used by both; genuinely neutral |
| `calibration._build_features` | shared | ❌ **CORRECTED — not shared.** Defined `calibration.py:62-82`; callers are `answer.py` (dead), `benchmark.py:1570,1574`, 14 scripts. **No alive-substrate file calls it.** It bridges the *dead opinion path* to the *benchmark path*, not old to living. |
| `thresholds.py` | not listed | ➕ **ADD.** Old `tick.py:19` (`detect_and_append`), living `alive.py:181` (`TRANSITION_RULES`). Both substrates read the same rule table via **two divergent implementations** — `alive.py:181-206` reimplements the cascade inline rather than calling `thresholds.detect_and_append`. Cannot be retired with the old family; is a drift risk today. |

**Consequence for 0.4:** repointing the opinion path means **creating** the
old→living bridge, not preserving one. The Bible's framing understates the work.

---

## Part 3 — State schemas

### 3.1 `World` — `earth1/alive.py:34-49` (14 fields, believed list confirmed exactly)

| # | field | runtime type | shape | built | mutated by |
|---:|---|---|---|---|---|
| 1 | `civ` | `types.Civilization` | — | `alive.py:61` | nearly every module (§3.3) |
| 2 | `life` | `life.Life` | — | `alive.py:62` | `life`, `institutions`, `flourishing`, `mobility`, `health` |
| 3 | `fabric` | `fabric.Fabric` | — | `alive.py:63` | **never mutated** — write-once, aliased to `civ.adj` at `alive.py:64` |
| 4 | `health` | `health.Health` | — | `alive.py:75` | `health`, `mobility`, `institutions`, `flourishing`, `weather`, `alive` |
| 5 | `knowledge` | `knowledge.Knowledge` | — | `alive.py:71` | `knowledge`, `alive:303-308` |
| 6 | `gov` | `institutions.Governments` | — | `alive.py:70` | `institutions:161-221` |
| 7 | `klass` | `institutions.Class` | — | `alive.py:70` | `institutions:306-340`, `alive:309-311` |
| 8 | `chronicle` | `memory.Chronicle` | — | `alive.py:77` | `memory:75-115` |
| 9 | `feed` | **bare `scipy.sparse.csr_matrix`** — *not* a dataclass | `(N,N)` | `alive.py:74` | immutable after build; `feed_tick` writes `civ.forces` |
| 10 | `climate` | `weather.Climate` | — | `alive.py:78` | `weather` |
| 11 | `flourishing` | `flourishing.Flourishing` | — | `alive.py:79` | `flourishing:221-244` |
| 12 | `presence` | `contagion.Presence` | — | `alive.py:80` | `contagion:193-262` |
| 13 | `mobility` | `mobility.Mobility` | — | `alive.py:81` | `mobility:128-184` |
| 14 | `day` | `int` | scalar | `alive.py:49` | **only** `alive.py:224` |

Two type corrections worth recording: `feed` is a bare sparse matrix with no
dataclass (so it has no schema to version), and `fabric` is never advanced after
birth — which is exactly the staleness 0.0d must fix.

**`rng` is not a `World` field.** It is passed positionally into
`live_one_day(w, rng, ...)` (`alive.py:84`). This matters for 0.0c: persisting RNG
state requires either adding a field or changing the save signature.

### 3.2 Sub-state field tables

Scale constants: `N` = agents, `NC` = **194** countries (`len(GENESIS_COUNTRIES)`,
`genesis.py:26`), `K` = **8** forces (`NUM_FORCES`, `types.py:20`), `F` = firms =
`max(1, N // 24)` (`AGENTS_PER_FIRM = 24`, `life.py:87`).

**`Civilization`** — `types.py:34-80`, 30 fields. Per-agent `(N,)` unless noted:
`n`(scalar,`:37`) `seed`(scalar,`:38`) `country`(`:40`) `region`(`:41`)
`age_bucket`(`:42`) `age`(`:43`) `education`(`:44`) `income`(int32,`:45`)
`urban`(bool,`:46`) `openness`(`:48`) `empathy`(`:49`) `risk_appetite`(`:50`)
`doubt`(`:51`) `desire_intensity`(`:52`) `economic_field`(`:53`)
`culture_offset`(`:54`) `conscientiousness`(`:56`) `agreeableness`(`:57`)
`extraversion`(`:58`) `neuroticism`(`:59`) `power_distance`(`:61`)
`individualism`(`:62`) `uncertainty_avoidance`(`:63`) `long_term_orientation`(`:64`)
**`forces`(N,8)**(`:66`) `alpha`(`:68`) **`means`(8,)**(`:70`) `adj`(csr `(N,N)`,`:72`)
+ 5 flag-gated optionals `religiosity` `marital` `employed` `ideology`
`social_class` (`:76-80`, `None` unless `EARTH1_RELIGIOSITY=1`).

**`Life`** — `life.py:165-223`, 32 fields. Per-agent except **`firm_health`(F,)**
`:178` and **`firm_country`(F,)** `:179`; and **`force_baseline`(N,8)** `:184`,
**`trait_baseline`(N,3)** `:191`. Note `policy_net` `:210` is `None` after
`birth_life` — first assigned at `institutions.py:240`.

**`Health`** — `health.py:92-103`, 8 fields, all `(N,)`: `condition`(int8,`:94`)
`diagnosed_day`(`:95`) `in_treatment`(bool,`:96`) `alive`(bool,`:97`)
`cause_of_death`(int8,`:98`) `lifetime_illnesses`(int16,`:99`) `declining`(`:102`)
`falls`(int16,`:103`).

**`Knowledge`** — `knowledge.py:55-63`: `stock` `status` `connected` `works_made`
`discoveries` all `(N,)`; **`global_stock`** and **`living_works`** scalar commons.

**`Governments`** — `institutions.py:71-85`, **all `(194,)`**: `tax` `welfare`
`policing` `legitimacy` `at_war_with`(int64, −1=peace) `war_days` `unrest_norm`
`dep_norm`.

**`Class`** — `institutions.py:88-94`, all `(N,)`: `homeless` `criminal`
`days_homeless` `crimes_committed` `migrated`.

**`Chronicle`** — `memory.py:56-61`: `events: list[Memory]` `forgotten` `total_ever`.
**`Memory`** — `memory.py:42-53`: `id` `label` `day` **`force_signature`(8,)**
**`scope`(N,) bool** `salience` `half_life` `rehearsals` `origin`.

**`Climate`** — `weather.py:53-64`, **all `(194,)`, zero per-agent state**:
`baseline_temp` `comfort` `tropical` `farm_share` `anomaly` `soil` `storm_days`.

**`Flourishing`** — `flourishing.py:78-92`, all `(N,)`: `hunger` `thirst` `breath`
`hope` `curiosity` `meaning` `belonging` `satisfaction` `art_received` `lifetime_joy`.

**`Presence`** — `contagion.py:145-152`: `locality`(int64,`(N,)`) `density`(`(N,)`)
`gathering`(int8,`(N,)`,−1=none) **`crowd_events`**(scalar counter)
**`riots`**(scalar counter).

**`Mobility`** — `mobility.py:71-78`: `owns_car` `flies_per_year` `commute_minutes`
`travelled`(int32) all `(N,)`; **`imported_disease`**, **`road_deaths`** scalar counters.

**`Fabric`** — `fabric.py:65-73`: `adj`(csr `(N,N)`) `by_type`(dict, **7** csr
matrices) `household`(int64 `(N,)`).

**Not stored:** `susceptibility` — `(N,8)`, recomputed fresh every day at
`alive.py:142`, never persisted. Correct as-is.

### 3.3 Two schema findings not in the Bible

**(a) `civ.means` is stale forever in the living world.** Set once at
`genesis.py:372`; updated only by `feedback.py:143`, `generational.py:283`,
`living.py:331`, `loop.py:270`, `dynamics.py:273` — **none reachable from
`live_one_day`**. Any readout that centres on `civ.means` (`forces.py:67`,
`engine.py:71,196`, `decompose.py:21`) centres a 110-day-old drifting world on
**day-0 means**. This is **Class GM occurrence #8** — a global constant standing
in for a quantity that has moved.

**(b) The EXPERIENCE force drifts free of age.** `genesis.py:362` sets
`forces[:, EXPERIENCE] = age` as a bare identity map. `generational.py:194`
re-asserts it — but is dead on the live path (§1.3). Meanwhile the live loop
injects into EXPERIENCE **monotonically and positively** with no counterbalance:
`flourishing.py:243-244` (`+= 0.10 * curiosity`, every day) and
`mobility.py:170-171` (`+= 0.01` per flyer, every day). `PERISHABILITY_HALF_LIFE[EXPERIENCE] = 4000`
(`types.py:28`) has **no consumer on the live path**. So EXPERIENCE starts as age
and thereafter ratchets upward — compounding D4-k, and interacting with 0.0a:
unfreezing age without re-asserting the identity map leaves two divergent notions
of "experience" in the same array.

### 3.4 RNG census

The live path takes exactly **one** `rng` argument (`alive.py:84`) and threads it
everywhere. `birth_*` constructors each derive `default_rng(seed ^ MAGIC)`:
`fabric:119`(`0xFAB`) `life:239`(`0x11FE`) `knowledge:75`(`0xC0DE`)
`institutions:99`(`0x607`) `weather:69`(`0x5C1`) `flourishing:96`(`0xF10`)
`mobility:90`(`0x40B1`) `feed:66`(`0xFEED`).

**Global unseeded RNG, entire repo — three sites, one on the live path:**

| site | classification |
|---|---|
| **`memory.py:108`** `np.random.random(civ.n)` | **LIVE — this is bug 0.1(a)** |
| `training.py:264-265` `np.random.seed(42)` / `permutation` | offline training only |
| `living.py:217` `default_rng()` unseeded | old path; immediately state-restored at `:218`, benign |

Plus one design-level determinism hole: **`scripts/world_alive.py:238`** seeds
from the wall clock — `default_rng(int(time.time()) % 2**31)`. The production
daemon is unreproducible by construction, independent of 0.1(a).

No stdlib `random` usage anywhere in `earth1/` (verified).

---

## Part 4 — Persistence field lists

### 4.1 The paths

| # | path | file:line | object | storage |
|---|---|---|---|---|
| **P1** | `save_world`/`load_world` | `scripts/world_alive.py:74`/`:98` | `alive.World` | `data/alive/world.pkl` + `adj.npz` + `state.json` |
| **P2** | `_save`/`restore` | `timeline.py:298`/`:310` | `alive.World` | `data/timeline/<ISO>.pkl` + `.adj.npz` + `index.json` |
| **P3** | `LivingWorld.save`/`.load` | `living.py:145`/`:195` | `tick.WorldState` | `data/living/earth1/{civ.npz,adj.npz,world.json}` |
| **P4** | `copy.deepcopy` | `branch.py:106,136` | `alive.World` | in-memory |
| P5 | `save_manifold` | `db/store.py:327` | `Civilization` | SQL, lossy by design, **no loader** |
| P6 | `deepcopy` | `assimilate.py:211,345` | `alive.World` | in-memory, complete |

**Note the brief's file path is wrong:** there is no `earth1/world_alive.py`. It
is **`scripts/world_alive.py`**.

### 4.2 `World`-level save matrix

| field | P1 `world_alive` | P2 `timeline` | P4 `branch` |
|---|---|---|---|
| `civ` | ⚠ **25 hardcoded arrays only** (`:81`, `CIV_ARRAYS:65-71`) | ✅ whole (`:302`) | ✅ |
| `life` `fabric` `health` `knowledge` `gov` `klass` `chronicle` `feed` | ✅ `:82-85` | ✅ `:302-305` | ✅ |
| `climate` `flourishing` | ✅ `:90` *(fixed in `d3d2a0c`)* | ✅ `:306` | ✅ |
| **`presence`** | ❌ **DROPPED** — rebirthed fresh at `:106` | ❌ **DROPPED** — stays `None` | ✅ |
| **`mobility`** | ❌ **DROPPED** — rebirthed fresh at `:106` | ❌ **DROPPED** — stays `None` | ✅ |
| `day` | ✅ `:91` | ✅ `:307` | ✅ |
| **RNG state** | ❌ **DROPPED** — clock-seeded `:238` | ❌ **DROPPED** — `:255`, never saved | ⚠ deliberately fresh (CRN design, correct) |
| **schema version** | ❌ **ABSENT** | ❌ **ABSENT** | n/a |

### 4.3 The four claims, adjudicated

| claim | verdict |
|---|---|
| (a) presence not persisted | ✅ **CONFIRMED** — both `World` paths |
| (b) mobility not persisted | ✅ **CONFIRMED** — both `World` paths |
| (c) RNG state not serialized | ✅ **CONFIRMED for P1/P2** · ❌ **REFUTED for P3** — `living.py:181-182` saves it, `:217-218` restores it, and `tests/test_living.py:57` proves it. **The dead engine has the discipline the living world lacks.** |
| (d) clock/version incomplete | ✅ **CONFIRMED** — `day` saved everywhere, but **no schema version on either `World` path**, and **no day→calendar epoch anywhere**. P2's date lives only in the *filename* and `index.json`; `START = date(2015,2,1)` (`timeline.py:57`) is never written into the snapshot. Rename a `.pkl` and its date is unrecoverable. |

### 4.4 The finding that outranks the field list

**A restored world does not run the same physics as the live world.**

`presence` and `mobility` are `None`-defaulted optionals (`alive.py:47-48`).
`timeline.restore` constructs `World(...)` without them (`timeline.py:322-326`,
verified verbatim). And `live_one_day` gates on them:

```
alive.py:150   if w.presence is not None:      → contagion_tick, shared_attention  (:152-157)
alive.py:160   if w.mobility is not None:      → mobility_tick                      (:161-164)
```

So a restored timeline world **permanently and silently loses**: co-presence force
mixing on all 8 channels (`contagion.py:200-210`), gatherings (`:216-234`), crowd
events (`:249-256`), riots (`:262-268`), road deaths — *which kill agents*
(`mobility.py:126-136`), commute tie-erosion (`:139-145`), fuel→cost pass-through
(`:148-151`), imported disease (`:173+`), and flight cultural mixing
(`:161-172`) — described in its own source as *"the sole source of genuine
mixing"* and the model's only non-convergent cultural channel.

Because `mobility_tick` kills agents, the two worlds diverge in **population**,
not just opinion. **Any backtest or scenario run from a restored world is not
comparable to one run from the live daemon.** This is strictly worse than "fields
missing from a save," and it is the sharpest available test for invariant (iv).

**Secondary:** `branch.apply` (`branch.py:54-89`) writes only `chronicle:73`,
`life.firm_health:81`, `life.cost:85`, `gov.at_war_with/war_days:88-89`. **There
is no lever for lockdowns, travel bans, crowd suppression or mobility
restriction** — the exact channels a COVID adapter needs. The `Scenario`
dataclass (`:38-51`) has no corresponding field. This blocks Phase 2's first task.

### 4.5 On-disk reality

Only `data/living/earth1/` exists (P3 — the *old* path):

```
civ.npz   36.5 MB  25 members = the 25 mandatory Civilization arrays
adj.npz    5.1 MB
world.json 73 KB   16 keys incl. format_version, rng_state(4), events(34)
```

`world.json` carries **`format_version`** and **`rng_state`** — the only versioned,
RNG-complete artifact in the repo, and it belongs to the substrate we are retiring.

**Absent:** `data/alive/`, `data/timeline/`, **`data/history/`**. The last is
consumed by `timeline.load_signals` (`:125,154`); when missing, `build()` silently
runs in `"ENDOGENOUS ONLY (no signal file)"` mode (`:257`) **without failing or
warning loudly**. A decade of "historical" timeline can be generated containing
zero real history. (Bible §II.4 notes `data/history/` is missing; it does not note
the silent-fallback.)

### 4.6 Persistence test coverage

| path | tests |
|---|---|
| P3 `LivingWorld` (dead) | **10** — `tests/test_living.py:24-142`, incl. `test_deterministic_continuation:57` |
| **P1 `world_alive`** | **ZERO** |
| **P2 `timeline`** | **ZERO** |
| **P4 `branch` parity** | **ZERO** |

This is precisely why the climate/flourishing loss ran undetected in production
under `Restart=always`.

---

## Part 5 — Test gaps

### 5.1 Headline numbers, re-measured

| Bible claim | measured at `e7545f8` | verdict |
|---|---|---|
| 894 tests | **899** | corrected |
| 611 import a dead-engine module | **616** (68.5%), 36 of 53 files | corrected |
| **zero test files import the live path** | **CONFIRMED — 0 files, 0 tests** | **confirmed, and stronger than stated** |

The live-path zero was verified by **transitive import closure** (not just direct
imports — necessary because `alive.py` does all its imports lazily *inside*
`live_one_day`):

```
alive 0 · influence 0 · chaos 0 · branch 0 · backtest 0 · consequences 0
answer 0 · health 0 · life 0 · institutions 0 · flourishing 0 · memory 0
contagion 0 · mobility 0 · feed 0 · knowledge 0 · weather 0 · susceptibility 0
fabric 0 · timeline 0 · assimilate 0 · observer 0 · signal_bus 0 · embedder 0
```

**24 of 25 live modules have exactly zero coverage — ~5,400 LOC.** The sole
exception is `generational.py` (10 tests, `tests/test_generational.py`), and it is
driven **through the dead `engine`/`tick` path**, never through `live_one_day`.

The five `scripts/*_test.py` files that import live modules (`butterfly_test.py`,
`fsle_test.py`, `life_substrate_test.py`, `lyapunov_test.py`,
`scale_artifact_test.py`) **define zero test functions** and collect zero tests.

### 5.2 Infrastructure that must be built first

**There is no `conftest.py` anywhere in the repo** (verified). No shared fixtures;
all 32 existing fixtures are file-local; every test file opens with a
`sys.path.insert(0, ".")` prologue.

Phase 0.3 must build: (a) `tests/conftest.py`; (b) a `tiny_world` fixture wrapping
`birth_world`; (c) **`world_hash(w)`** spanning all 14 `World` components;
(d) `force_death(w, i)`; (e) a global-RNG-untouched guard.

**Patterns to port** (do not import — they live in dead modules):

| asset | location | use |
|---|---|---|
| `pop_hash_full(civ)` | `living.py:50-65` | the state-hash pattern — sha256 over sorted dataclass ndarrays + `adj.indices/indptr/data`. **Covers `civ` only; must be extended across all 14 components.** |
| `test_deterministic_continuation` | `tests/test_living.py:57-71` | exact template for invariant (v) |
| `test_pop_hash_full_sees_alpha_and_graph` | `tests/test_living.py:138-151` | proves a hash is not blind — port for `world_hash` |
| `test_aging_advances_with_clock` | `tests/test_generational.py:22-28` | template for invariant (i) |
| `test_reproducibility` | `tests/test_engine.py:137-140` | template for invariant (vi) |
| `make_rng(seed)` | `rng.py:6` | canonical seeded factory — **unused by the live path**; standardise the new suite on it |

### 5.3 Population sizing

`birth_world(pop, seed)` calls `genesis(pop, seed)` (`alive.py:61`) **without
forwarding `min_per_country`** (default 500, `genesis.py:170`). `_allocate_countries`
(`genesis.py:151-166`) rescales the floor away, so tiny populations work:

```
pop=2000  → 194 countries, min 10 / max 11 per country, zero empty   ← usable
pop=1000  → min 5 / max 6                                            ← marginal
pop=194   → 1 per country                                            ← degenerate
```

**Recommended smoke size: `pop=2_000`.** Floor: `_be_born` requires
`living.size >= 10` (`alive.py:244`).

⚠ **Documented caveat:** at pop=2000 locality populations fall below the
`pop_l >= 10` cascade gate (`alive.py:197`), so **cascades never fire at tiny
pop**. None of the six invariants depend on cascades — but nothing else may be
smoke-tested at this size without re-deriving the floor.

### 5.4 The semantic invariant suite — the 0.3 release gate

| file to create | invariants |
|---|---|
| `tests/conftest.py` | infrastructure (§5.2) |
| `tests/test_alive_semantics.py` | (i) aging, (ii) virgin rebirth |
| `tests/test_persistence_roundtrip.py` | (iii) hash round-trip, (v) RNG continuation |
| `tests/test_branch_reproducibility.py` | (iv) restored-branch parity |
| `tests/test_determinism.py` | (vi) same-seed bit-identity |

**(i) Ages advance.** Use **one call with `dt_days=365.0`** (`alive.py:88` accepts
it) — same semantics as 365 iterations, 365× cheaper.
```python
surv = before & w.health.alive
np.testing.assert_allclose(w.civ.age[surv] - age0[surv], 1.0/72.0, atol=1e-12)
assert np.array_equal(w.civ.age_bucket, np.digitize(18.0 + w.civ.age*72.0, [30,45,60,75]))
```

**(ii) Virgin rebirth.** Call `_be_born` **directly** — the conception hazard is
`tfr/(25*365)*0.5 ≈ 2.5e-4/day` (`alive.py:254-255`), so waiting for a stochastic
birth takes ~10 simulated days. Assert `not (new_nbrs & old_nbrs)` on the CSR row
**and** column, plus `fabric.household[i]` changed, plus the §6.2 field list.

**(iii) Round-trip hash.** Requires `world_hash` first. Also assert
`w2.presence is not None and w2.mobility is not None` — **fails today**.

**(iv) Restored-branch parity.** The sharpest test in the suite. Mechanism: because
`restore` drops presence/mobility, the restored world's `live_one_day` takes the
`is not None` branches false and **consumes a different number of draws from the
shared rng** — every subsequent draw is offset, so the ensembles diverge from day
1 at identical seed. `days=2, repeats=1`.

**(v) RNG continuation.** Direct port of `tests/test_living.py:57-71`. Requires
`_save` to persist `rng.bit_generator.state` and `restore` to return the generator.

**(vi) Determinism.** Cheapest regression lock in the whole plan — needs no world
hash and no world:
```python
s = np.random.get_state()[1].copy()
live_one_day(w, rng)
assert np.array_equal(np.random.get_state()[1], s), "live_one_day touched the global RNG"
```
The sharp unit form needs only `pop=194`, one memory, one scope mask.

---

## Part 6 — Exact edit sites

Every line below was read at `e7545f8`. Quoted code is verbatim.

### 6.0e — Pin the deployment *(new; see §1.1)*

| action | target |
|---|---|
| check in the unit file | new `ops/alive/earth1-alive.service` (currently only on the box) |
| stamp provenance | `scripts/world_alive.py:74-95` — add commit SHA + physics version to `state.json` |
| refuse dirty start | `scripts/world_alive.py:main` |
| reconcile box → branch | box is `14401ea`+dirty, 133 behind |

### 6.0a — Aging

**`live_one_day` = `alive.py:84-225`.** Call order: govern`:100` → policy/war`:101`
→ life_tick`:104` → health_tick`:106` → class_tick`:108` → knowledge`:111` →
weather`:117` → flourishing`:123` → target`:131` → susceptibility/propagate`:142-144`
→ contagion`:152-157` → mobility`:162` → feed`:169` → relax/conviction`:173-174` →
chronicle`:177-178` → cascade`:181-206` → feedback`:209-215` → `_be_born``:222` →
`w.day += 1``:224`.

**`civ.age` is never written in this function** (verified: `grep -n "generational" earth1/alive.py`
→ no match; the only `civ.age` writes repo-wide are `generational.py:183` and
`alive.py:276` newborn-zeroing).

**Insert at `alive.py:102-103`** — after policy/war`:101`, before `life_tick``:104`.
Constraints that fix this position:

| must precede | why |
|---|---|
| `health_tick``:106` | `health.py:151` `age_years = 18.0 + civ.age * 72.0` feeds cancer t⁵ `:136/163`, cvd `:166`, infection `:169`, falls `:177-178`, decline `:207` |
| `life_tick``:104` | `life.py:532` bereavement, `:536` fertility window |
| `susceptibility_of``:142` | `susceptibility.py:48` `plasticity = clip(1.35 - 0.7*civ.age, .45, 1.4)` |
| `_be_born``:222` | so newborns are not aged on their birth day |

**Extract `generational.py:181-194` into `aging_tick(civ, dt_days)`** — do **not**
call `generational_tick` whole (§1.3).

**Blast radius — 15 live hazards unfreeze at once:** `health.py:151,136,166,169,177-178,207` ·
`mobility.py:118-119` (road-death peak at 24) · `weather.py:137` (frailty) ·
`institutions.py:264` (conscription `age<0.35`), `:332` (migration `age<0.5`) ·
`alive.py:251` (fertility) · `life.py:532,536` · `susceptibility.py:48` ·
`fabric.py:166` (friend ties keyed on `age_bucket` — **go stale as buckets advance**).

> ⚠ **0.0a is blocked by a latent bug.** `life.py:267` sets
> `in_lf = (civ.age <= 0.78) & (rng.random(n) > 0.28)` **once, in `birth_life`, and
> never recomputes it.** Unfreezing age produces a cohort of 90-year-olds
> permanently in the labour force. **Retirement must be added in the same change**,
> or 0.0a's invariant passes while the economy silently breaks.

### 6.0b — Virgin-slot rebirth

**`_be_born` = `alive.py:228-323`.** Resets `civ.country/region/urban``:265-267`,
9 traits`:269-275`, `age``:276`, `age_bucket``:277`, `education``:278`,
`forces``:279-280`, `alpha``:281`; `life` wealth/spells/tenure/employment`:284-289`,
mental`:291-295`; `knowledge``:303-308`; `klass``:309-311`; `health``:313-318`.

**Does it clear the adjacency row? No.** `_be_born` contains no reference to
`civ.adj`, `w.fabric`, or `fabric.by_type`.

**What clearing requires** — `fabric.py:205-216` builds **scipy CSR** per tie type
plus a summed `Fabric.adj`, and applies `m = m.maximum(m.T)` (ties are mutual):
1. zero **row *i* AND column *i*** — a row-only clear leaves inbound edges and
   `adj @ x` still delivers influence to *i*;
2. do it on `Fabric.adj` **and each of the 7 `by_type` matrices**, then
   `eliminate_zeros()`, then re-alias `civ.adj = fab.adj` (`alive.py:64`);
3. reassign `Fabric.household[i]` (`fabric.py:69`);
4. **write an incremental tie-builder** — `_pairs_within` (`fabric.py:91-114`) is
   whole-population/vectorised; there is no "add k ties for agent i" helper.

**The reborn slot inherits far more than ties.** Fields `_be_born` does *not*
reset, each a defect:

| object | inherited fields |
|---|---|
| `Health` | **`declining`, `falls`** (`health.py:102-103`) — **a newborn can be born in post-fall decline**, multiplying fall hazard ×3.5 (`health.py:188-189`) and heat/cold mortality ×3 (`weather.py:143-145`) |
| `Life` | `occupation` `wage` `cost` `physical` `relationship` `social_need` `political` `mental_setpoint` `relationship_setpoint` `last_event_day` `durables` `durable_spend` `owns_home` `rent` |
| `Civilization` | `economic_field` `culture_offset` `power_distance` `individualism` `uncertainty_avoidance` `long_term_orientation` `income` + 4 optionals (note `generational.py:268-270` *does* reset `income`; `_be_born` does not) |
| `Knowledge` | `status` `connected` |
| `Class` | `days_homeless` `migrated` |
| `Flourishing` | **all 10** |
| `Presence` | **all 3 per-agent** — `locality` is *not* recomputed even though `civ.country/region/urban` are overwritten at `:265-267` |
| `Mobility` | **all 4 per-agent** |
| `Chronicle` | every `Memory.scope` mask (`memory.py:48`) — the slot stays "someone this happened to" forever |
| feed | the dead person's readers/sources (`feed.py:78-90`) |

**This argues for a central reset schema** (as BIBLE 0.0b says) rather than
extending the hand-written list — the list is how we got here.

**Second fertility path — CONFIRMED, with a qualification that matters.**

| | `_be_born` `alive.py:247-256` | `life_tick` `life.py:535-538` |
|---|---|---|
| age window | `>0.03` (20.2y) | `>0.05` (21.6y) |
| relationship | `>0.55` | `>0.60` |
| deprivation | `<0.6` clipped | `<0.5` unclipped |
| **alive gate** | `h.alive &` | **NONE — dead agents "have children"** |
| daily rate | `tfr[country]/(25*365)*0.5` ≈ **1.10e-4** | flat `0.055/365` = **1.51e-4** |
| creates an agent? | **yes** | **no** |

**Qualification:** B is a *life-event* fertility (nudges `relationship += 0.05`
`life.py:558`, stamps event code 5 `:574-579`) — not a competing birth process. So
this is a divergent-window bug plus a missing `h.alive` gate, **not** the
double-birth the Bible implies. Fix: one shared predicate; add the alive gate.

### 6.0c — Persistence

**P2 `timeline.py`** — write field list **`:302-307`**, read constructor **`:322-326`**
(verified verbatim; `presence`/`mobility` absent from both). RNG created
`:255`, never persisted.

**P1 `scripts/world_alive.py`** — write dict **`:81-91`**, read **`:106-124`**,
`CIV_ARRAYS` **`:65-71`**, RNG **`:238`** (clock-seeded).

Three traps in P1:
1. `load_world` calls `birth_world(d["n"], d["seed"])` at `:106` **before**
   overwriting `civ` at `:107-108` — so `presence.locality` is rebuilt from the
   *fresh genesis* civ and is **stale relative to the restored population**.
2. `CIV_ARRAYS` omits the 5 optional `Civilization` fields — silently regenerated
   from genesis priors on every restore.
3. **`_unused_save``:130` and `load_or_birth``:144` are dead AND broken** —
   `load_or_birth` references `genesis`, `birth_life`, `build_fabric`, none of
   which are imported in that file (imports are `:38-40`). It would `NameError`.
   `LIFE_ARRAYS``:59-64` is used only by the dead `_unused_save`, so its 7
   omissions are a trap for a future editor, not a live bug. **Delete all three.**

**Recommendation:** make the save **schema-driven** (iterate
`__dataclass_fields__`) rather than hand-listed, and add `schema_version`. §1.4
shows the hand-listed approach re-introduced the same defect in the very commit
that fixed it.

### 6.0d — Fabric re-homing

**Migration — `institutions.py:326-344`.** The comment at `:341` says *"arriving
costs you your ties"*; **it touches no tie.** `civ.adj`, `w.fabric`, `feed` all
untouched.

> ➕ **Bonus defect:** `:339` updates `civ.country` but **not `civ.region` or
> `civ.urban`**, so the migrant's locality key
> `country*1000 + region*2 + urban` — used identically at `fabric.py:158-159`,
> `contagion.py:156-157`, `alive.py:182-183` — becomes an **invalid address**.
> This must be fixed regardless of tie rebuilding.

**Job change — `life.py:393-397`** (loss) and **`:410-421`** (find). `life.firm`
changes for a slice of the population every tick; `fabric.by_type["colleagues"]`
is built once at `alive.py:63` and never rebuilt. **Colleague ties are permanently
the day-0 firm assignment.**

**The 7 tie types — `fabric.py:44-57`:**

| tie | weight/k | built | keyed on | stale after migration | after job change |
|---|---|---|---|---|---|
| `household` | 1.00/— | `:126-150` | `civ.country` + poisson | **YES** | no |
| `colleagues` | 0.60/6 | `:153-155` | `life.firm` | **YES** | **YES** |
| `neighbours` | 0.40/5 | `:158-161` | locality key | **YES** | no |
| `friends` | 0.70/5 | `:164-168` | `country*100+education*10+age_bucket` | **YES** | no (**but stale on aging — 0.0a**) |
| `weak` | 0.15/2 | `:171-178` | `civ.country` | **YES** | no |
| `diaspora` | 0.55/1 | `:184-195` | country/region cross-pairs | **YES** | no |
| `media` | 0.30/3 | `:198-203` | random hubs | no | no |

**Co-presence is a separate structure** — `Presence.locality`
(`contagion.py:155-166`), same key, **also never rebuilt**.

`rehome(w, idx)` must: set `civ.region`/`civ.urban` coherently; drop rows+cols
from 6 of 7 tie types; draw replacements via a new incremental `_pairs_within`;
recompute `Fabric.household`; re-sum `Fabric.adj` and re-alias `civ.adj`;
recompute `Presence.locality`+`density` (**both origin and destination shift**);
optionally re-wire feed rows. Call from `institutions.py:344` and
`life.py:397`+`:421` (colleagues-only, cheaper).

### 6.1(a) — `memory.spread` unseeded global RNG

**`memory.py:99-112`**, offending line **`:108`** (verified verbatim):
```python
catch = (~m.scope) & (np.random.random(civ.n) < rate * exposure)
```
`spread` does not even accept an `rng` parameter (`:99`).

**Plumbing is one hop.** Exactly one caller repo-wide — `alive.py:178`
`st["memory_spread"] = w.chronicle.spread(civ)` — and `rng` is already a parameter
of the enclosing `live_one_day` (`alive.py:84`).

**Fix:** `def spread(self, civ, rng, rate=0.06)`; `:108` → `rng.random(civ.n)`;
`alive.py:178` → `spread(civ, rng)`. No dataclass change.

**Blast radius (R3):** every paired-difference result measured with a populated
chronicle is suspect. `remember()` is called from `timeline.py:239`,
`branch.py:73`, `observer.py:75`, `scripts/world_alive.py:223` — **so every
timeline, branch and production run has a populated chronicle.**

### 6.1(b) — `health.py` shared random row

**Allocation `health.py:154`:** `u = rng.random((len(DISEASES) + 1, n))`.
`DISEASES` = 5 (`:88`) → shape **(6, n)**. *(Note: rows are the first axis; the
brief's `(N,k)` is transposed.)*

| row | site | purpose |
|---|---|---|
| `u[0..3]` | `:194` (`j % u.shape[0]`, a no-op since `j<6`) | cancer, cvd, infection, injury onset |
| **`u[4]`** | **`:194` (j=4) AND `:235`** | **fall onset AND treatment acceptance** |
| **`u[5]`** | — | **allocated, never referenced** |

**Bias direction, stated precisely:** a faller passed `u[4] < haz_fall*dt_yr`,
i.e. a *very small* `u[4]`; at `:235` that same small value passes `u[4] < p`
almost surely. **Every faller is treated.** Untreated-fall mortality
(`SURVIVE_UNTREATED["fall"]=0.72` vs `SURVIVE_TREATED=0.93`, `health.py:61-63`)
is effectively never sampled.

**Fix: `health.py:235` → `u[5]`.** One character. Zero allocation change.

### 6.1(c) — `influence.update_conviction` decay no-op

**`influence.py:91-108`**, line **`:107`** (verified verbatim):
```python
return np.clip(alpha + gain * (agreement - 0.5) * 2.0 - decay * 0.0,
               0.02, 1.0)
```
`CONVICTION_DECAY = 0.02` (`:43`) multiplied by literal zero.

**What the docstring requires:** *"disagreement **and isolation** soften it."* The
`gain` term already handles disagreement (`agreement < 0.5` → negative). The dead
term is the **isolation** channel — and the function already computes `deg`
(`:101`) purely as a normaliser. Faithful fix:
```python
isolation = 1.0 / (1.0 + deg)      # 1 when isolated, → 0 when well-connected
return np.clip(alpha + gain*(agreement-0.5)*2.0 - decay*isolation, 0.02, 1.0)
```
Called once — `alive.py:174`, both params at defaults, **no call-site change**.

**Consequence today:** `alpha` is a ratchet. It feeds `propagate`'s alignment
weight (`influence.py:62`) and `susceptibility.py:51`, so the whole population
monotonically hardens. ⚠ This fix **changes live physics** — it must ship behind
the 0.8 re-measurement, with before/after conviction distributions reported.

### 6.1(d) — Cause-of-death collision

| code | meaning | assigned at |
|---|---|---|
| 0 | alive / reset | `health.py:111`, `alive.py:315` |
| 1–4 | cancer, cvd, infection, injury | `health.py:255` ← `condition` `:196` |
| **5** | **fall** | `health.py:255` ← `condition` (`:88`, `:94`) |
| **5** | **war** | **`institutions.py:271`** *(box `:268` — §1.1)* |
| 6 | weather | `weather.py:151` |
| 7 | want | `flourishing.py:173` |
| 8 | road | `mobility.py:127` |

**Collision confirmed.** No shared enum exists: repo-wide, only `Force`
(`types.py:8`) and `Scale` (`receiver.py:187`) are enums.

> **Loudest finding on this item: `cause_of_death` has ZERO readers.** Grep across
> `*.py`/`*.md`/`*.json` returns only the 6 assignment sites, the declaration
> (`health.py:98`) and the constructor (`health.py:111`). **The collision
> currently corrupts no output because no output consumes it.** Fixing it is
> migration-risk-free — and **any acceptance test must also add the first reader.**

**Second hazard:** `EVENT_CODES` (`life.py:160`) is an orthogonal 1–8 code space
for `life.last_event`. The two will read identically in any joint dump.

**Fix:** `CauseOfDeath` IntEnum in `types.py` (beside `Force`, already imported by
all six). Import sites: `health.py:111,255` · `institutions.py:271` ·
`weather.py:151` · `flourishing.py:173` · `mobility.py:127` · `alive.py:315`.
`health.py:255` needs an explicit `condition→cause` lookup once fall stops being 5.
**One-line unblock if the enum slips: move war to 9** (6/7/8 taken).

### 6.2–6.8 — Downstream, in dependency order

| task | primary edit sites | gated by |
|---|---|---|
| **0.2** unify the loop | `chaos.world_step` → thin wrapper over `live_one_day` (`alive.py:84`); delete the duplicated cascade at `alive.py:181-206` in favour of `thresholds.detect_and_append`; declare one `beta` (currently 1.0 / 2.0 / ×2.2 in three places) | 0.1 |
| **0.3** live-path tests | §5.4 — 5 new files + `conftest.py` | 0.0a–0.1 (tests encode the fixed semantics) |
| **0.4** repoint opinion path | `calibration.py:62-82` `_build_features` + a **new** World adapter; `answer.py` (**currently orphaned — this is wiring, not repointing**, §1.2) | 0.3 |
| **0.5** port + retire | **first: empty `earth1/__init__.py:1-4`** (§2.3); then `perishability`(2 sites) → `coupling`(3) → `event_generation`(3) → `graph_dynamics`(4) → `dynamics`; then 31 API handlers across 9 files (§2.2); quarantine last | 0.4 |
| **0.6** kill the third world | delete `~/Library/LaunchAgents/com.earthling.earth1-daily.plist` + `launchd/` in repo. **Already unloaded** (§1.4) — this is file removal, not `bootout` | none |
| **0.7** prime to work | `ops/supervisor/jobs_prime.json` — **none of the 12 jobs is a living-substrate job**; storage-box backup verify (F4) | none |
| **0.8** re-measure | butterfly, FSLE, noise floor, consciousness profile — same preregs, same thresholds, on the unified loop | 0.2 + 0.3 |

---

## Part 7 — New defects found (not in the Bible)

Numbered for the ledger. Each has file:line above.

| # | defect | severity | where |
|---|---|---|---|
| **N1** | Live world runs `14401ea`+dirty; `earth1-alive.service` not in repo | **CRITICAL** | §1.1 |
| **N2** | `timeline.restore` silently disables contagion, shared attention, mobility — a *physics* change, not a state gap | **CRITICAL** | §4.4 |
| **N3** | `earth1/__init__.py:1` imports `engine` unconditionally — blocks all retirement | **HIGH** | §2.3 |
| **N4** | `answer.py` has zero importers; the Bible's `tick.py` retention rationale is void | **HIGH** | §1.2 |
| **N5** | `generational_tick` carries its own mortality+rebirth that ignore `health.alive` | **HIGH** | §1.3 |
| **N6** | `life.in_lf` set once at birth, never recomputed — **blocks 0.0a** | **HIGH** | §6.0a |
| **N7** | `civ.means` stale forever on the live path — **Class GM #8** | **HIGH** | §3.3a |
| **N8** | `_be_born` inherits `health.declining`/`health.falls` + ~40 more fields | **HIGH** | §6.0b |
| **N9** | Migration updates `country` but not `region`/`urban` → invalid locality key | **HIGH** | §6.0d |
| **N10** | EXPERIENCE force ratchets upward, decoupled from age, no decay consumer | MED | §3.3b |
| **N11** | `branch.apply` has no presence/mobility lever — **blocks Phase 2 COVID adapter** | MED | §4.4 |
| **N12** | `timeline.build` silently runs "ENDOGENOUS ONLY" when `data/history/` is absent | MED | §4.5 |
| **N13** | `world_alive.load_or_birth` is dead **and** would `NameError`; `_unused_save`, `LIFE_ARRAYS` dead | MED | §6.0c |
| **N14** | `life_tick` fertility lacks an `h.alive` gate — dead agents "have children" | MED | §6.0b |
| **N15** | Two orthogonal 1–8 code spaces (`cause_of_death`, `EVENT_CODES`) | LOW | §6.1d |
| **N16** | P1 restore rebuilds `presence.locality` from genesis civ before restoring civ → stale | MED | §6.0c |
| **N17** | `/world/tick` defaults force-dynamics **off**, `world_daily.py` defaults **on** — same `advance_world`, opposing rationales written a day apart | LOW | §2.2 |

---

## Part 8 — What I need from you

**1. Sign off or amend this audit.** No code changes until you do.

**2. Rule on the proposed new task 0.0e (§1.1).** I recommend it lands **before**
0.0a: without a pinned deployment we cannot prove a fix reached the world. This is
the one place where I am departing from the Bible's task list, so it is your call.

**3. Rule on 0.1(c) sequencing.** The conviction-decay fix is the only Phase 0 item
that **changes live physics** rather than correcting an unambiguous defect. It
makes `alpha` non-monotonic for the first time. I propose shipping it with
before/after conviction distributions attached, inside 0.8's re-measurement rather
than silently in 0.1. Alternative: delete the parameter and the docstring claim
(the Bible permits this — "or delete the parameter and the docstring claim").

**4. The five founder-gated items** (F1–F5) are unblocked and independent of
everything above. **F3 (RunPod key rotation) is an open credential exposure and
should be done today regardless of everything else in this document.**

**Working-tree note:** this branch carries an uncommitted `data/leakage_test.json`
modification and an untracked `data/country_map_parallel.json`. Per your standing
rule on regenerated data I have left them untouched pending your call, but they
should be committed or discarded before 0.0a so the branch has a clean base.

---

## Appendix — Verification log

Claims re-verified by hand at `e7545f8` before inclusion, rather than accepted
from the parallel investigations:

| claim | command | result |
|---|---|---|
| `answer.py` orphaned | `grep -rn "earth1\.answer" --include="*.py" .` | zero non-self hits |
| `__init__` imports engine | `head -5 earth1/__init__.py` | confirmed `:1-4` |
| `memory.spread` global RNG | `sed -n '99,110p' earth1/memory.py` | confirmed `:108` |
| conviction decay ×0.0 | `sed -n '105,108p' earth1/influence.py` | confirmed `:107` |
| `u[4]` double-use, `u[5]` unused | `sed -n '154p;192,196p;233,236p' earth1/health.py` | confirmed |
| war=5 vs fall=5 | `grep -rn "cause_of_death" earth1/*.py` | confirmed 8 sites |
| aging absent from live path | `grep -n "generational" earth1/alive.py` | no match |
| presence/mobility gating | `sed -n '150p;160,162p' earth1/alive.py` | confirmed |
| `timeline.restore` omits both | `sed -n '322,327p' earth1/timeline.py` | confirmed |
| box commit + drift | `ssh … git rev-parse`, `git merge-base --is-ancestor`, `md5sum` ×9 | 133 behind; 7/9 identical; 2 differ, both benign to findings |
| launchd not loaded | `launchctl print gui/501/com.earthling.earth1-daily` | "Could not find service" |
| PDF is a faithful twin | `pymupdf` extract + word diff vs `BIBLE.md` | 99.2%; all residual diffs are link URLs + one repeated table header |
| test collection | `python3 -m pytest --collect-only -q` | 899 in 9.6 s |

**Not verified** (flagged rather than assumed):
- The production `data/alive/world.pkl` on the world box was not inspected; all P1
  on-disk claims are from source reading.
- Per-test dead/live attribution is at **file** granularity; per-test attribution
  needs `pytest --cov` with contexts, which requires running the suite.
- The predicted failures for invariants (i)–(vi) are code-reading conclusions
  anchored to specific lines. **None has been executed.** Executing them is 0.3,
  and each is expected to fail on first run — that is the point.
- Whether `birth_life`/`build_fabric`/`birth_institutions` hold undocumented
  minimum-size assumptions at 10 agents/country. The `tiny_world` fixture will
  discover this first.
