import hashlib
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL = ("https://datasets-server.huggingface.co/rows?dataset="
       "Anthropic%2Fllm_global_opinions&config=default&split=train"
       "&offset={o}&length=100")
rows, o = [], 0
while True:
    raw = subprocess.run(["curl", "-s", "--max-time", "40", URL.format(o=o)],
                         capture_output=True, text=True).stdout
    try:
        d = json.loads(raw)
    except Exception:
        print("bad page at", o); break
    batch = d.get("rows", [])
    if not batch:
        break
    rows.extend(r["row"] for r in batch)
    o += 100
    if o >= d.get("num_rows_total", 10**9):
        break
print("fetched rows:", len(rows))
p = os.path.join(ROOT, "data", "goqa_full.json")
json.dump({"source": "HF datasets-server Anthropic/llm_global_opinions",
           "n": len(rows), "rows": rows}, open(p, "w"))
print("sha256", hashlib.sha256(open(p, "rb").read()).hexdigest()[:16])
