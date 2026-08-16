#!/usr/bin/env python3
"""A5 blind partition: EVENT-RESPONSIVE vs SECULAR-DRIFT, from text only.

One Haiku call per WVS question, temperature 0, question text ONLY —
no run results, no country data, no deltas. Committed BEFORE run #8.
The procedure was designed after the 2026-08-16 diagnosis (declared in
A5); the partition itself cannot see outcomes. If it disagrees with the
inspected screen, the blind partition WINS — no manual overrides.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from earth1.wvs_paired import WVS_PAIRED

OUT = ROOT / "data" / "temporal_partition.json"

PROMPT = (
    "Does aggregate opinion on this survey question change primarily "
    "through discrete news-visible events (crises, rulings, attacks, "
    "policy shocks) or through slow generational/developmental drift? "
    "Reply with exactly one token: EVENT or SECULAR.\n\n"
    "Question: {text}"
)


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY — the partition must be authored, "
                 "never defaulted.")
    import anthropic
    client = anthropic.Anthropic()

    partition = {}
    for pq in WVS_PAIRED:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=8,
            temperature=0,
            messages=[{"role": "user",
                       "content": PROMPT.format(text=pq.text)}],
        )
        token = resp.content[0].text.strip().upper()
        if token not in ("EVENT", "SECULAR"):
            sys.exit(f"Malformed classification for {pq.id}: {token!r} — "
                     "aborting, nothing written.")
        partition[pq.id] = token
        print(f"  {pq.id:<20} {token}")

    OUT.write_text(json.dumps({
        "registered_under": "A5",
        "authored": datetime.now(timezone.utc).isoformat(),
        "model": "claude-haiku-4-5-20251001",
        "temperature": 0,
        "prompt": PROMPT,
        "inputs": "question text ONLY — no run results, no country data, no deltas",
        "partition": partition,
    }, indent=2))
    n_event = sum(1 for v in partition.values() if v == "EVENT")
    print(f"\n{n_event} EVENT / {len(partition) - n_event} SECULAR -> {OUT}")


if __name__ == "__main__":
    main()
