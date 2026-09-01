"""GROUND LADDER v1 (EARTH1_GROUND_LADDER=v1; founder orders 2026-09-01).

Earth-1's port of the VNF ground-question ladder, with the ruled
constraints baked into the TYPES:

  rung 1  seed_exact      registered ground file for this entity
  rung 2  seed_neighbour  ground file for the same entity under another
                          question (entity index)
  rung 3  live_ledger     URL-grounded structured fetch -> NewsItems
                          written to the hash-chained ground ledger
                          (url + snippet sha256); force position via the
                          REGISTERED deterministic extractor map. No
                          LLM anywhere on this path.
  rung 4  forward_estimate  returns Abstain — the type has no
                          force_position field, so emitting a
                          probability from it is impossible.
  rung 5  no_grounding    Abstain.

Relevance rule (adopted verbatim from VNF): no seed match => R = 0 for
every force. Silence beats a uniform offset.

No cron may call this module until it has a XI.A.2 report.
"""
import hashlib
import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, Union

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GROUND_DIR = os.path.join(_ROOT, "data", "ground")
LEDGER = os.path.join(GROUND_DIR, "ledger.jsonl")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")


@dataclass
class Grounded:
    rung: str
    entity: str
    force_position: dict          # force name -> [-1, 1]
    sources: list                 # [{url, snippet_sha256, retrieved}]
    matched_keywords: list


@dataclass
class Abstain:
    rung: str                     # "forward_estimate" | "no_grounding"
    entity: str
    reason: str
    # NOTE: no force_position field exists on this type — by ruling.


GroundResult = Union[Grounded, Abstain]


def _extractor():
    return json.load(open(os.path.join(GROUND_DIR, "extractor_map.v1.json")))


def _ledger_append(record: dict) -> str:
    os.makedirs(GROUND_DIR, exist_ok=True)
    prev = "GENESIS"
    if os.path.exists(LEDGER):
        for line in open(LEDGER):
            prev = json.loads(line)["_hash"]
    body = dict(record)
    body["_prev"] = prev
    h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    body["_hash"] = h
    with open(LEDGER, "a") as f:
        f.write(json.dumps(body, sort_keys=True) + "\n")
    return h


def _slug(s):
    return re.sub(r"[^A-Za-z0-9_-]", "_", s)[:80]


def _seed_path(question_id, entity):
    return os.path.join(GROUND_DIR, f"{_slug(question_id)}.json")


def _entity_index():
    idx = {}
    if not os.path.isdir(GROUND_DIR):
        return idx
    for f in os.listdir(GROUND_DIR):
        if f.endswith(".json") and f not in ("extractor_map.v1.json",):
            try:
                d = json.load(open(os.path.join(GROUND_DIR, f)))
                for e, g in d.get("entities", {}).items():
                    idx.setdefault(e.lower(), g)
            except Exception:
                continue
    return idx


def _fetch_wikipedia(entity: str):
    url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
           + urllib.request.quote(entity.replace(" ", "_")))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    extract = d.get("extract", "")
    if not extract:
        return None
    return {"url": d.get("content_urls", {}).get("desktop", {}).get(
        "page", url), "text": extract}


def _extract_forces(text: str):
    emap = _extractor()
    pos = {}
    hits = []
    t = " " + text.lower() + " "
    for row in emap["rules"]:
        for kw in row["keywords"]:
            if kw in t:
                hits.append(kw)
                for f, v in row["forces"].items():
                    pos[f] = pos.get(f, 0.0) + v
    if not pos:
        return None, []
    m = max(abs(v) for v in pos.values())
    if m > 1.0:
        pos = {f: v / m for f, v in pos.items()}
    return {f: round(v, 3) for f, v in pos.items()}, sorted(set(hits))


def ground(question_id: str, entity: str,
           allow_live: bool = True) -> GroundResult:
    if os.environ.get("EARTH1_GROUND_LADDER", "off") != "v1":
        return Abstain("no_grounding", entity, "EARTH1_GROUND_LADDER off")
    # rung 1 — registered ground file for this question
    p = _seed_path(question_id, entity)
    if os.path.exists(p):
        d = json.load(open(p))
        g = d.get("entities", {}).get(entity) or \
            d.get("entities", {}).get(entity.lower())
        if g:
            return Grounded("seed_exact", entity, g["force_position"],
                            g.get("sources", []),
                            g.get("matched_keywords", []))
    # rung 2 — same entity grounded under another question
    g = _entity_index().get(entity.lower())
    if g:
        return Grounded("seed_neighbour", entity, g["force_position"],
                        g.get("sources", []), g.get("matched_keywords", []))
    # rung 3 — live structured fetch -> ledger -> deterministic extractor
    if allow_live:
        try:
            page = _fetch_wikipedia(entity)
        except Exception as e:
            page = None
        if page:
            snip_sha = hashlib.sha256(page["text"].encode()).hexdigest()
            _ledger_append({"kind": "ground_newsitem",
                            "question_id": question_id, "entity": entity,
                            "url": page["url"],
                            "snippet_sha256": snip_sha,
                            "retrieved": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            forces, hits = _extract_forces(page["text"])
            if forces:
                g = {"force_position": forces,
                     "sources": [{"url": page["url"],
                                  "snippet_sha256": snip_sha}],
                     "matched_keywords": hits}
                d = (json.load(open(p)) if os.path.exists(p)
                     else {"question_id": question_id, "entities": {}})
                d["entities"][entity] = g
                json.dump(d, open(p, "w"), indent=1, sort_keys=True)
                return Grounded("live_ledger", entity, forces,
                                g["sources"], hits)
            # rung 4 — a page exists but the registered extractor maps
            # nothing: the ONLY continuation would be a model guess.
            return Abstain("forward_estimate", entity,
                           "URL-grounded text carries no registered "
                           "extractor keywords; refusing to estimate")
    # rung 5
    return Abstain("no_grounding", entity, "no seed, no neighbour, "
                   "no reachable grounded source")
