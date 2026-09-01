"""Append fetched markets to PROSPECTIVE_REGISTER.jsonl (hash-chained).

Canonicalization (reverse-verified against the existing chain):
line_sha256 = sha256(json.dumps(entry_minus_line_sha, sort_keys=True)).
Entries are registered pre-adapter: p_model null, abstain true with
reason; they will be RE-SIGNED by multiverse_v1 under tag
prospective-2026-09-01b (founder amendment item 5). first_seen_price is
IMMUTABLE: never updated after this write.

usage: append_register.py <snapshot.json> <tag>
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(ROOT, "ops/alive/PROSPECTIVE_REGISTER.jsonl")


def sign(entry):
    e = {k: v for k, v in entry.items() if k != "line_sha256"}
    return hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()


def main(snap_path, tag):
    snap = json.load(open(snap_path))
    lines = [json.loads(l) for l in open(REG)]
    for i, l in enumerate(lines):
        assert sign(l) == l["line_sha256"], f"CHAIN BROKEN at line {i}"
        if i:
            assert l["prev_line_sha256"] == lines[i - 1]["line_sha256"]
    print("existing chain verified:", len(lines), "lines")
    seen_q = {l["question"].strip().lower() for l in lines}
    tree = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True,
                          cwd=ROOT).stdout.strip()
    prev = lines[-1]["line_sha256"]
    added = 0
    with open(REG, "a") as f:
        for mid, m in sorted(snap["markets"].items()):
            if m["question"].strip().lower() in seen_q:
                continue
            entry = {
                "abstain": True,
                "abstain_reason": "registered pre-adapter; to be signed by "
                                  "multiverse_v1 (tag "
                                  "prospective-2026-09-01b)",
                "class": m["class"], "country": None,
                "first_seen_price": m["p_yes"],
                "flag_set_hash": "freeze-0.9",
                "market_ts": snap["fetched_at"],
                "p_market": m["p_yes"], "p_model": None,
                "prev_line_sha256": prev,
                "question": f'{m["question"]} ({m["source"]})',
                "question_id": mid, "resolution_date": m["resolution_date"],
                "sigma": None, "source": m["source"], "tag": tag,
                "tree_hash": tree,
            }
            entry["line_sha256"] = sign(entry)
            f.write(json.dumps(entry, sort_keys=True) + "\n")
            prev = entry["line_sha256"]
            seen_q.add(m["question"].strip().lower())
            added += 1
    lines = [json.loads(l) for l in open(REG)]
    for i, l in enumerate(lines):
        assert sign(l) == l["line_sha256"]
        if i:
            assert l["prev_line_sha256"] == lines[i - 1]["line_sha256"]
    print(f"APPENDED {added} entries (tag {tag}); chain re-verified, "
          f"{len(lines)} total lines, tail {prev[:12]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
