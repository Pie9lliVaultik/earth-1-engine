#!/usr/bin/env python3
"""Post-cutoff backtest: score the engine on RECENTLY-resolved markets.

Pietro's law: understand what force fields worked on resolved readings
before trusting forward ones. The honest window: markets resolved within
the last 14 days resolved AFTER the perception LLM's training cutoff —
the LLM cannot have seen the outcomes. (VNF proved the pattern with its
mode=resolved nightly backfill; this is the disciplined redo.)

Rules:
  - LABELED BACKTEST — separate report, never pooled with the
    pre-committed standing record.
  - Same pipeline as live arming: perceive -> rehearse -> read.
  - Three-way score per market: engine vs raw-LLM (same question, one
    Haiku call) vs market price ~24h before resolution.
  - Anatomy grouping on results: which dominant forces hit.

Output: data/backtest_resolved.json + printed scoreboard.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "backtest_resolved.json"
WINDOW_DAYS = 14          # post-LLM-cutoff safety window
MAX_SCORED = 80
PRICE_LEAD_HOURS = 24     # score vs price this long before resolution


def _get(url: str):
    r = subprocess.run(["curl", "-s", "--max-time", "60",
                        "-A", "Earth1-Engine/1.0", url],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


def fetch_resolved_manifold(pages: int = 6) -> list:
    """Recently-resolved binary markets, newest-created first."""
    cutoff_ms = (datetime.now(timezone.utc)
                 - timedelta(days=WINDOW_DAYS)).timestamp() * 1000
    out, before = [], None
    for _ in range(pages):
        url = "https://api.manifold.markets/v0/markets?limit=1000"
        if before:
            url += f"&before={before}"
        batch = _get(url)
        if not batch:
            break
        before = batch[-1]["id"]
        for m in batch:
            if (m.get("isResolved")
                    and m.get("outcomeType") == "BINARY"
                    and m.get("resolution") in ("YES", "NO")
                    and (m.get("resolutionTime") or 0) >= cutoff_ms):
                out.append(m)
        time.sleep(0.5)
    return out


def price_before_resolution(market_id: str, resolution_ms: float):
    """Market probability ~PRICE_LEAD_HOURS before resolution, from the
    bet stream. None if no bet history exists that early."""
    try:
        bets = _get(f"https://api.manifold.markets/v0/bets"
                    f"?contractId={market_id}&limit=1000")
    except Exception:
        return None
    target = resolution_ms - PRICE_LEAD_HOURS * 3600 * 1000
    best = None
    for b in bets:                       # newest first
        t = b.get("createdTime", 0)
        p = b.get("probAfter")
        if p is None:
            continue
        if t <= target and (best is None or t > best[0]):
            best = (t, float(p))
    return best[1] if best else None


def llm_baseline(question: str):
    """Raw-Haiku probability for the same question — the head-to-head
    VNF ran (engine vs naked LLM on identical resolved markets)."""
    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    import anthropic
    client = anthropic.Anthropic()
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=16,
            messages=[{"role": "user", "content":
                       f"Probability this resolves YES (reply with only a "
                       f"number 0.00-1.00):\n{question}"}],
        )
        txt = resp.content[0].text.strip().rstrip("%")
        p = float(txt)
        return p / 100.0 if p > 1.0 else p
    except Exception:
        return None


def main():
    from earth1.genesis import genesis
    from earth1.corpus import QuestionCorpus
    from earth1.arming import perceive
    from earth1.multiverse import rehearse_question
    from earth1.markets import is_belief_causal
    from earth1.types import NUM_FORCES, Force

    print(f"Fetching markets resolved in the last {WINDOW_DAYS} days...")
    resolved = fetch_resolved_manifold()
    causal = [m for m in resolved if is_belief_causal(m.get("question", ""))]
    print(f"{len(resolved)} resolved binary markets, "
          f"{len(causal)} belief-causal, scoring up to {MAX_SCORED}")

    civ = genesis(50_000, seed=42)
    corpus_path = ROOT / "data" / "corpus" / "goqa_seed"
    corpus = (QuestionCorpus.load(corpus_path)
              if corpus_path.exists() else None)

    rows, abstained = [], 0
    for m in causal[:MAX_SCORED * 2]:
        if len(rows) >= MAX_SCORED:
            break
        question = m["question"]
        outcome = 1.0 if m["resolution"] == "YES" else 0.0

        q = perceive(question, corpus)
        if q is None:
            abstained += 1
            continue
        reh = rehearse_question(q, civ, k=4, attention_frac=0.35)
        present = reh.present

        price = price_before_resolution(m["id"], m["resolutionTime"])
        llm_p = llm_baseline(question)

        rows.append({
            "question": question,
            "market_id": m["id"],
            "resolved": m["resolution"],
            "outcome": outcome,
            "engine_p": round(present.yes_pct, 4),
            "market_p_24h": round(price, 4) if price is not None else None,
            "llm_p": round(llm_p, 4) if llm_p is not None else None,
            "dominant_force": present.dominant.name.lower(),
            "fragility": round(present.fragility, 4),
            "regime": present.regime,
        })
        if len(rows) % 10 == 0:
            print(f"  scored {len(rows)}...")

    # ── scoreboard ──
    def brier(key):
        vals = [(r[key] - r["outcome"]) ** 2 for r in rows
                if r.get(key) is not None]
        return (round(sum(vals) / len(vals), 5), len(vals)) if vals else (None, 0)

    eng_b, n_eng = brier("engine_p")
    mkt_b, n_mkt = brier("market_p_24h")
    llm_b, n_llm = brier("llm_p")

    by_force = {}
    for r in rows:
        d = by_force.setdefault(r["dominant_force"],
                                {"n": 0, "brier_sum": 0.0, "hits": 0})
        d["n"] += 1
        d["brier_sum"] += (r["engine_p"] - r["outcome"]) ** 2
        d["hits"] += int((r["engine_p"] > 0.5) == (r["outcome"] > 0.5))
    for f, d in by_force.items():
        d["brier"] = round(d.pop("brier_sum") / d["n"], 5)
        d["hit_rate"] = round(d["hits"] / d["n"], 3)

    report = {
        "label": "POST-CUTOFF BACKTEST — never pool with standing record",
        "generated": datetime.now(timezone.utc).isoformat(),
        "window_days": WINDOW_DAYS,
        "n_scored": len(rows), "n_abstained": abstained,
        "engine_brier": eng_b,
        "market_brier_24h": mkt_b,
        "llm_baseline_brier": llm_b,
        "by_force": by_force,
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, indent=1))

    print(f"\n{'='*56}")
    print(f"POST-CUTOFF BACKTEST — {len(rows)} resolved markets "
          f"({abstained} abstained)")
    print(f"  engine Brier:      {eng_b}  (n={n_eng})")
    print(f"  market 24h Brier:  {mkt_b}  (n={n_mkt})")
    print(f"  raw-LLM Brier:     {llm_b}  (n={n_llm})")
    print(f"  anatomy:")
    for f, d in sorted(by_force.items(), key=lambda kv: kv[1]["brier"]):
        print(f"    {f:<12} n={d['n']:<4} brier={d['brier']:.4f} "
              f"hit={d['hit_rate']:.0%}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
