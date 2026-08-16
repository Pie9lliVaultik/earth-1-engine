"""The world reads today's news — the live perception channel (§14 + 5.8).

Every daily tick, a rotating cohort of countries gets its top headlines
from the last 48h (GDELT DOC artlist), each headline is perceived by the
one-call-per-item LLM boundary (news_perception), and the perceived
force events enter the event log — the same validated path that passed
the G5 event leg (run #7, ratio 1.01).

Discipline (inherited from news_perception):
  - No key -> channel OFF, loudly. Never a silent fallback.
  - Perceptions are clipped, confidence-floored, source-tagged.
  - Abstentions are ledgered (data/living/earth1/abstentions.jsonl),
    never scored, never silently dropped.
  - The country rotation is deterministic in the day number, so a
    reloaded world reads the same countries it would have.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from earth1.news_perception import NewsItem, perceive_item

# The read rotation: population-weighted major countries. 10 read per
# day -> full cycle every 3 days.
READ_COUNTRIES = [
    ("IN", "india"), ("CN", "china"), ("US", "unitedstates"),
    ("ID", "indonesia"), ("PK", "pakistan"), ("NG", "nigeria"),
    ("BR", "brazil"), ("BD", "bangladesh"), ("RU", "russia"),
    ("MX", "mexico"), ("JP", "japan"), ("PH", "philippines"),
    ("EG", "egypt"), ("VN", "vietnam"), ("TR", "turkey"),
    ("DE", "germany"), ("IR", "iran"), ("TH", "thailand"),
    ("GB", "unitedkingdom"), ("FR", "france"), ("IT", "italy"),
    ("ZA", "southafrica"), ("KR", "southkorea"), ("ES", "spain"),
    ("AR", "argentina"), ("PL", "poland"), ("UA", "ukraine"),
    ("SA", "saudiarabia"), ("AU", "australia"), ("NL", "netherlands"),
]
PER_DAY = 10
PER_COUNTRY = 3
PACE_SECONDS = 8.0


def _resolve_ip() -> Optional[str]:
    out = subprocess.run(
        ["dig", "+short", "@1.1.1.1", "api.gdeltproject.org"],
        capture_output=True, text=True,
    ).stdout.strip().splitlines()
    return out[0] if out else None


def fetch_headlines_for(
    name: str, ip: str, hours: float = 48.0, retries: int = 3,
) -> List[dict]:
    """Top PER_COUNTRY recent headlines for one GDELT sourcecountry."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=hours)).strftime("%Y%m%d%H%M%S")
    end = now.strftime("%Y%m%d%H%M%S")
    url = (f"https://api.gdeltproject.org/api/v2/doc/doc?"
           f"query=sourcecountry:{name}&mode=artlist&maxrecords=25"
           f"&sort=hybridrel&STARTDATETIME={start}&ENDDATETIME={end}"
           f"&format=json")
    for attempt in range(retries):
        r = subprocess.run(
            ["curl", "-s", "--max-time", "60",
             "--resolve", f"api.gdeltproject.org:443:{ip}",
             "-A", "Earth1-Engine/1.0 research", url],
            capture_output=True, text=True,
        )
        try:
            arts = json.loads(r.stdout).get("articles", [])
            seen, out = set(), []
            for a in arts:
                t = (a.get("title") or "").strip()
                if len(t) > 25 and t[:40] not in seen:
                    seen.add(t[:40])
                    out.append({"title": t,
                                "date": a.get("seendate", "")[:8],
                                "url": a.get("url", "")})
                if len(out) >= PER_COUNTRY:
                    break
            return out
        except json.JSONDecodeError:
            time.sleep(15 * (attempt + 1))
    return []


def read_todays_news(
    day: int,
    t: float,
    ledger_path: Optional[Path] = None,
    perceiver=perceive_item,
    fetcher=None,
    progress: bool = True,
) -> List:
    """Fetch + perceive today's headlines for the day's country cohort.

    Returns WorldEvents ready for the event log. Ledger records every
    item with its outcome (perceived / abstained / fetch_empty)."""
    from earth1.event_log import WorldEvent
    from earth1.types import Force

    cohort = [READ_COUNTRIES[(day * PER_DAY + i) % len(READ_COUNTRIES)]
              for i in range(PER_DAY)]

    ip = None
    if fetcher is None:
        ip = _resolve_ip()
        if ip is None:
            if progress:
                print("  news: DNS resolution failed — no read today")
            return []

    force_names = [f.name.lower() for f in Force]
    events, ledger = [], []
    stamp = datetime.now(timezone.utc).isoformat()

    for cc, name in cohort:
        arts = (fetcher(name) if fetcher
                else fetch_headlines_for(name, ip))
        if fetcher is None:
            time.sleep(PACE_SECONDS)
        if not arts:
            ledger.append({"ts": stamp, "day": day, "country": cc,
                           "outcome": "fetch_empty"})
            continue
        for art in arts:
            item = NewsItem(title=art["title"], country=cc,
                            date=art.get("date", ""), url=art.get("url", ""))
            ev = perceiver(item)
            if ev is None:
                ledger.append({"ts": stamp, "day": day, "country": cc,
                               "title": art["title"], "outcome": "abstained"})
                continue
            deltas = {force_names[i]: float(v)
                      for i, v in ev.force_deltas.items()}
            events.append(WorldEvent.create(
                timestamp=t,
                force_deltas=deltas,
                region_pattern=f"{cc}-*",
                decay_half_life=ev.decay_half_life,
                source="perception:llm",
            ))
            ledger.append({"ts": stamp, "day": day, "country": cc,
                           "title": art["title"], "outcome": "perceived",
                           "deltas": deltas,
                           "confidence": ev.confidence})
        if progress:
            n_ev = sum(1 for l in ledger
                       if l.get("country") == cc and l["outcome"] == "perceived")
            print(f"  news {cc}: {len(arts)} headlines -> {n_ev} events")

    if ledger_path is not None:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger_path, "a") as f:
            for row in ledger:
                f.write(json.dumps(row) + "\n")

    return events
