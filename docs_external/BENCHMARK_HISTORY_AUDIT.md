# Benchmark History Audit

_Reconciling the "we beat Claude and Gemini in early benchmarks" narrative against what is actually stored in `quality_benchmark_runs`. No code changes. All numbers below come from the SQL in the appendix, run 2026-07-16._

---

## TL;DR

1. **May 2026 runs were not head-to-head.** Every May row in `quality_benchmark_runs` has `mae_l1 = NULL` and `prediction = NULL`. They contain question text and a `run_label` and nothing else — no target, no Earthlings prediction, no LLM baseline. They cannot have "beaten Claude or Gemini" because no comparison was ever scored.
2. **The first real head-to-head is 2026-07-12** via `benchmark-standoff`. That function is the only path in the repo that writes `prediction.errors.earthlings / gpt5 / gemini / best_llm` side by side.
3. **On every scored standoff run to date, the best LLM baseline beat Earthlings.** Our Group-A MAE dropped 0.123 → 0.071 over four days, which is real improvement, but GPT-5 and Gemini-flash stayed flat at 0.02–0.05 the whole time. The narrative that "the gap is closing and we're beating them" appears to be a misread of our own improvement curve.
4. **The engine used by standoff (`compute_civilization_answer_v4`) still lives in the code, but the recent `benchmark-compare` test shows it now times out at RPC scope.** So the "winning engine" was never actually winning, and today it can't even respond within the request budget when called directly.

---

## 1. May 2026 runs contain no comparison data

```sql
select run_label, kind, count(*) as n,
       count(mae_l1) as scored, count(prediction) as with_payload
from quality_benchmark_runs
where created_at::date between '2026-05-01' and '2026-05-31'
group by 1,2 order by 1;
```

| run_label | kind | n | scored | with_payload |
|---|---|--:|--:|--:|
| after_l2_v1 | binary_personal / civ_opinion / multi_outcome / real_world_poll | 20 | **0** | **0** |
| after_sprint_v1 | binary_personal / civ_opinion / multi_outcome / real_world_poll | 60 | **0** | **0** |
| after_sprint_v2 | binary_personal / civ_opinion / multi_outcome / real_world_poll | 20 | **0** | **0** |
| sim_solved_v1__pending | binary_personal / civ_opinion / multi_outcome / real_world_poll | 20 | **0** | **0** |

Sampled row (`select question_text, mae_l1, prediction from quality_benchmark_runs where run_label='after_sprint_v1' limit 5`):

```
"Should I take a sabbatical year to travel?"   mae_l1=NULL   prediction=NULL
"Is marriage still important?"                 mae_l1=NULL   prediction=NULL
"Should I learn to code in 2026?"              mae_l1=NULL   prediction=NULL
"Is owning a home better than renting?"        mae_l1=NULL   prediction=NULL
"Should I quit social media?"                  mae_l1=NULL   prediction=NULL
```

These are smoke/labeling runs. No target, no LLM baseline, no scoring. Any May-based claim of beating Claude or Gemini is unsupported by the stored data.

---

## 2. First real head-to-head: `benchmark-standoff`, 2026-07-12

`supabase/functions/benchmark-standoff/index.ts` runs 20 fixed questions (Group A calibrated-adjacent US polling, Group B forward territory: FR/DE/JP/BR/IN/NG/MX/global) through the production pipeline:

```
resonate → ground-question → vote-v7 → compute_civilization_answer_v4
```

and compares to two LLM baselines (`openai/gpt-5`, `google/gemini-2.5-flash`), each averaged over 2 attempts. Errors are stored as `prediction.errors.{earthlings, gpt5, gemini, best_llm}`.

The 20 target questions and their sources are hardcoded in `benchmark-standoff/index.ts:33-56`.

---

## 3. Actual standoff results

Full aggregation of every standoff run with LLM comparison data, ordered by date.

**Group A — calibrated-adjacent US questions (n=10 each unless noted):**

| Day | run_label | Ours | GPT-5 | Gemini | Best LLM | Wins vs best LLM |
|---|---|--:|--:|--:|--:|--:|
| 07-12 | standoff_pre_expansion | **0.1041** | — | 0.0595 | 0.0595 | 3/10 |
| 07-12 | standoff_pre_expansion_grounded | **0.1229** | 0.0445 | 0.0435 | 0.0215 | 0/10 |
| 07-12 | standoff_pre_expansion_grounded_v2 | **0.0934** | 0.0310 | 0.0540 | 0.0210 | 2/10 |
| 07-12 | standoff_post_gss_v3 | **0.1099** | 0.0295 | 0.0500 | 0.0175 | 2/10 |
| 07-12 | nightly …_f6222bf4 | **0.0911** | 0.0445 | 0.0600 | 0.0250 | 2/10 |
| 07-13 | nightly …_29420d28 | **0.0976** | 0.0420 | 0.0425 | 0.0250 | 2/10 |
| 07-14 | nightly …_8c77b068 | **0.0834** | 0.0285 | 0.0605 | 0.0195 | 1/10 |
| 07-14 | nightly …_bb087d42 (n=20) | **0.0720** | 0.0388 | 0.0610 | 0.0238 | 4/20 |
| 07-15 | nightly …_1b1bf6b6 | **0.0709** | 0.0455 | 0.0445 | 0.0265 | 2/10 |
| 07-16 | nightly …_b76f0767 | **0.0883** | 0.0430 | 0.0445 | 0.0230 | 1/10 |

**Group B — forward territory (n=10 each unless noted):**

| Day | run_label | Ours | GPT-5 | Gemini | Best LLM | Wins vs best LLM |
|---|---|--:|--:|--:|--:|--:|
| 07-12 | standoff_pre_expansion | **0.1308** | — | 0.0680 | 0.0680 | 3/10 |
| 07-12 | standoff_pre_expansion_grounded | **0.1289** | 0.0645 | 0.0770 | 0.0515 | 3/10 |
| 07-12 | standoff_pre_expansion_grounded_v2 | **0.0968** | 0.0800 | 0.0830 | 0.0540 | 3/10 |
| 07-12 | standoff_post_gss_v3 | **0.1130** | 0.0510 | 0.0830 | 0.0485 | 2/10 |
| 07-12 | nightly …_f6222bf4 | **0.1432** | 0.0640 | 0.0650 | 0.0405 | 1/10 |
| 07-13 | nightly …_29420d28 | **0.1401** | 0.0470 | 0.0670 | 0.0410 | 2/10 |
| 07-14 | nightly …_8c77b068 | **0.1020** | 0.0810 | 0.0625 | 0.0420 | 2/10 |
| 07-14 | nightly …_bb087d42 (n=20) | **0.1600** | 0.0483 | 0.0675 | 0.0350 | 3/20 |
| 07-15 | nightly …_1b1bf6b6 | **0.1538** | 0.0575 | 0.0660 | 0.0345 | 1/10 |
| 07-16 | nightly …_b76f0767 | **0.1441** | 0.0570 | 0.0670 | 0.0400 | 1/10 |

**Reading:** on Group A our MAE improved from ~0.12 to ~0.07–0.09 over four days. On Group B it never dropped below 0.10 and has drifted back up to 0.14–0.16. GPT-5's MAE stayed in a 0.03–0.08 band the entire time and Gemini in a 0.04–0.09 band. There is no run in which our aggregate MAE beats the best LLM baseline on either group. Per-question wins vs best-LLM cluster around 10–30%.

The "0.0927 vs GPT-5 0.055, Gemini 0.062, gap closing" line that entered planning appears to be an averaged reading of Group A runs where the numbers were, in fact:

- Ours ≈ 0.09 (best A-day was 0.0709; typical A-day 0.08–0.10)
- GPT-5 ≈ 0.03–0.05
- Gemini ≈ 0.04–0.06

The gap did narrow — because our number moved and theirs didn't — but it never crossed zero.

---

## 4. Engine lineage (code trace)

Which SQL function each production path calls today:

| Path | RPC | File / line |
|---|---|---|
| `benchmark-standoff` → `vote-v7` | `compute_civilization_answer_v4` (or `_v5` when flag set) | `supabase/functions/vote-v7/index.ts:464` |
| `resonate` (SQL-only path) | `compute_civilization_answer_v2` | `supabase/functions/resonate/sql-only-path.ts:429` |
| `predict-with-coherence` | `compute_civilization_answer_v2_agents` | `supabase/functions/predict-with-coherence/index.ts:97` |

Three engines are live in production (`v2`, `v2_agents`, `v4`). Only `v4` was ever benchmarked head-to-head against LLMs via `benchmark-standoff`. Neither `v2` nor `v2_agents` has any row in `quality_benchmark_runs` with an LLM comparison.

---

## 5. What changed between July's standoff numbers and this week's `benchmark-compare`

The comparative benchmark test run this week (`benchmark-compare`, engines A/B/C/D/E/F) showed:

- Engine C (`compute_civilization_answer_v4` direct RPC) — `statement_timeout` on every seed.
- Engine D (`compute_civilization_answer_v4_ablation(true)`) — `statement_timeout` on every seed.

Same SQL as July, same infra tier. Three candidate explanations, each falsifiable with one query:

1. **Payload difference.** The `vote-v7` caller may send a smaller / different embedding payload than the direct RPC used by `benchmark-compare`. Check: log the exact `p_yes_embedding` / `p_no_embedding` shape both callers send and compare.
2. **Table growth.** `souls`, `agent_desires`, `agent_fears` may have grown past the point where v4's per-request budget suffices. Check: `select count(*) from souls`, `agent_desires`, `agent_fears` now vs the row counts on 2026-07-16. If materially larger, v4's inner scan/sort widened past the RPC timeout.
3. **Grounding shortcut.** `vote-v7` runs `ground-question` first, which can short-circuit or narrow the candidate set before v4 is called. If v4 was already marginal on cost, direct calls that skip grounding would tip over. Check: run `v4` from `benchmark-compare` with a pre-narrowed candidate set and see if the timeout goes away.

Whichever hypothesis holds, the fact that `benchmark-standoff` was hitting v4 through `vote-v7` — and that path still returns — is what kept the July numbers reportable. The direct-RPC compare test exposed that v4 is not currently callable at RPC scope.

---

## 6. Reconciliation table

| Historical claim | Supporting rows in `quality_benchmark_runs` | Verdict |
|---|---|---|
| "Early May benchmarks beat Claude and Gemini." | None. All May rows have `mae_l1 = NULL`, `prediction = NULL`. No LLM baselines were ever recorded in May. | **Unsupported.** |
| "Standoff MAE 0.0927 vs GPT-5 0.055 / Gemini 0.062." | `standoff_pre_expansion_grounded_v2` A: ours 0.0934, GPT-5 0.0310, Gemini 0.0540. Numbers ballpark match but the framing is reversed: this is a **loss**, not a win. | **Misread.** |
| "Gap is closing." | Our A-MAE 0.1229 → 0.0709 across 07-12 → 07-15. LLM MAE flat 0.02–0.05. | **Half true.** Our number improved; LLM numbers did not degrade. Absolute gap narrowed on A but stayed open. |
| "Beating LLMs on forward territory (Group B)." | On every scored B run, ours ≥ 0.096 while best LLM ≤ 0.068. Per-question wins vs best LLM: 1–3 out of 10. | **Contradicted.** |
| "vote-v7 / v4 is the certified production engine." | vote-v7 does call v4 (`vote-v7/index.ts:464`). But direct-RPC v4 currently times out (see §5), and only one of three production engines (`v2`, `v2_agents`, `v4`) has ever been benchmarked against LLMs. | **Partially true, load-bearing on `vote-v7`'s grounding.** |

---

## Appendix — SQL used

```sql
-- May coverage check
select run_label, kind, count(*) as n,
       count(mae_l1) as scored, count(prediction) as with_payload
from quality_benchmark_runs
where created_at::date between '2026-05-01' and '2026-05-31'
group by 1,2 order by 1;

-- Standoff head-to-head aggregation
select run_label, kind, min(created_at)::date as day, count(*) as n,
  round(avg((prediction->'errors'->>'earthlings')::float)::numeric,4) as our_mae,
  round(avg((prediction->'errors'->>'gpt5')::float)::numeric,4) as gpt5,
  round(avg((prediction->'errors'->>'gemini')::float)::numeric,4) as gemini,
  round(avg((prediction->'errors'->>'best_llm')::float)::numeric,4) as best_llm,
  sum(case when (prediction->'errors'->>'earthlings')::float
             < (prediction->'errors'->>'best_llm')::float
           then 1 else 0 end) as wins_vs_best
from quality_benchmark_runs
where kind like 'standoff%' and prediction ? 'errors'
group by 1,2 order by min(created_at), 1, 2;

-- Sample standoff payload shape
select jsonb_pretty(prediction) from quality_benchmark_runs
where run_label='standoff_pre_expansion_grounded_v2' and prediction is not null limit 1;
```
