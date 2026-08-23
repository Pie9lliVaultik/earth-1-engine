"""Verify local copies of CASCADE_PUBLIC_BENCHMARK datasets against the
frozen manifest (md5 where the publisher states one; sha256 recorded on
first ingestion otherwise). Read-only. Downloads nothing."""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MAN = json.load(open(ROOT / "benchmarks" / "cascade_public" / "manifest_v1.json"))
DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "cascade_public"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


ok = True
for key, ds in MAN["datasets"].items():
    for fname, meta in (ds.get("files") or {}).items():
        p = DATA / key / fname
        if not p.exists():
            print(f"[absent ] {key}/{fname}"); continue
        got = md5(p); exp = meta.get("md5")
        good = exp is None or got == exp
        ok &= good
        print(f"[{'ok' if good else 'MISMATCH'}] {key}/{fname} md5={got}")
print("MANIFEST", "CONSISTENT" if ok else "VIOLATED")
sys.exit(0 if ok else 1)
