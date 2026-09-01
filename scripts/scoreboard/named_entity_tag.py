"""B2-c3: named-entity abstention (founder order 2026-09-01 item 3).

Rule: an item referencing a named person, party, or specific foreign
institution/leader that the scored world's news ledger has not exposed
-> abstain. Cold benchmark worlds have an empty ledger, so every tagged
item abstains there; a production world that has lived through events
exposes entities via chronicle memory labels and answers accordingly.

Detector (conservative, auditable — every match recorded):
  * institution list (EU, UN, NATO, IMF, World Bank, WHO, ...)
  * person heuristic: >=2 consecutive capitalized tokens not at
    sentence start and not country/demonym/continent words
Writes data/concordance/named_entity_tags.json, then recomputes the
three estates' aggregate MAE and coverage with abstention ON, straight
from the committed per-item tables (no re-simulation involved; the
per-item numbers are seed-averaged already).
"""
import json
import os
import re
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

INSTITUTIONS = [
    "european union", " eu ", "(eu)", "united nations", " un ", "(un)",
    "nato", "imf", "international monetary fund", "world bank",
    "world health organization", "(who)", "world trade",
    " wto", "african union", "arab league", "opec", "asean",
    "al qaeda", "al-qaeda", "isis", "hamas", "hezbollah", "taliban",
    "congress", "parliament of", "white house", "kremlin",
    "communist party", "muslim brotherhood",
]
NON_NAMES = set("""january february march april may june july august
september october november december africa america asia europe latin
western eastern northern southern middle east united states britain
british american french german russian chinese iraqi iranian israeli
palestinian islam islamic muslim christian catholic protestant jewish
buddhist hindu arab europeans americans internet television nations
department government military should would could country countries
region world war state states press bank""".split())


def detect(text):
    t = " " + text.lower() + " "
    hits = [i.strip("() ") for i in INSTITUTIONS if i in t]
    for m in re.finditer(r"(?<![.?!]\s)(?<!^)\b([A-Z][a-z]{2,})\s+"
                         r"([A-Z][a-z]{2,})\b", text):
        a, b = m.group(1).lower(), m.group(2).lower()
        if a not in NON_NAMES and b not in NON_NAMES:
            hits.append(f"{m.group(1)} {m.group(2)}")
    return sorted(set(hits))


def exposed_entities(world=None):
    """Entities the world's news ledger has exposed (chronicle memory
    labels). Benchmark worlds are cold: empty set."""
    if world is None:
        return set()
    out = set()
    for mem in getattr(world.chronicle, "memories", []) or []:
        out.update(w.lower() for w in re.findall(r"[A-Za-z]{3,}",
                                                 getattr(mem, "label", "")))
    return out


def main():
    tags = {}
    tables = {}
    for e in ("wvs_heldout", "wvs_extended", "goqa_dev"):
        d = json.load(open(os.path.join(ROOT, f"data/cycles/sb1_items_{e}.json")))
        tables[e] = d["items"]
        for r in d["items"]:
            ents = detect(r["text"] or "")
            if ents:
                tags[r["item"]] = {"named_entity": True, "entities": ents,
                                   "estate": e}
    p = os.path.join(ROOT, "data/concordance/named_entity_tags.json")
    json.dump({"rule": "abstain when entity not in world news ledger; "
                       "cold benchmark worlds => all tagged items abstain",
               "n_tagged": len(tags), "tags": tags},
              open(p, "w"), indent=1, sort_keys=True)
    print("TAGGED", len(tags), "items ->", p)
    exposed = exposed_entities(None)   # cold worlds
    res = {}
    for e, items in tables.items():
        def agg(rows):
            num = sum(r["earth1_mae_pp"] * r["n_countries"] for r in rows)
            den = sum(r["n_countries"] for r in rows)
            return num / max(den, 1), den
        keep = [r for r in items
                if not (r["item"] in tags
                        and not set(x.lower() for x in
                                    tags[r["item"]]["entities"]) & exposed)]
        m0, n0 = agg(items)
        m1, n1 = agg(keep)
        res[e] = {"mae_before": round(m0, 2), "mae_after": round(m1, 2),
                  "items_before": len(items), "items_after": len(keep),
                  "coverage_pairs": f"{n1}/{n0}",
                  "abstained_items": len(items) - len(keep)}
        print(f"{e:14s} MAE {m0:.2f} -> {m1:.2f}pp | items {len(items)} -> "
              f"{len(keep)} | pair coverage {n1}/{n0}")
    json.dump(res, open(os.path.join(
        ROOT, "data/cycles/b2c3_abstention.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
