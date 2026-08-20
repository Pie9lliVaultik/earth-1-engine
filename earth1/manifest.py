"""Reproducibility manifests — every experiment on prime records enough
to be re-run by a stranger. Phase 0.7.

The contract: no result is admissible because it ran somewhere; it is
admissible because its manifest pins WHAT ran — code, world, config,
data, seeds, machine — and WHERE the artifact lives. Prime pulls code
and data from canonical sources (origin git, Storage Box backups); no
unique scientific state may exist only on prime, so the manifest (and
the small result artifacts it points at) are committed to the repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          cwd=ROOT).stdout.strip()


def config_hash(config: dict) -> str:
    """Stable hash of a parameter dict (sorted-key JSON)."""
    blob = json.dumps(config, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def file_sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def machine_spec() -> dict:
    spec = {"hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count()}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                spec["mem_total_kb"] = int(line.split()[1])
                break
    except OSError:
        pass
    return spec


def snapshot_identity(snapshot_dir: Path) -> dict:
    """Pin the world this experiment starts from. The sidecar sha256 is
    authoritative; state.json supplies day/alive/schema."""
    d = Path(snapshot_dir)
    ident = {"path": str(d)}
    side = d / "world.pkl.sha256"
    if side.exists():
        ident["world_pkl_sha256"] = side.read_text().split()[0]
    else:
        ident["world_pkl_sha256"] = file_sha256(d / "world.pkl")
    st_path = d / "state.json"
    if st_path.exists():
        st = json.loads(st_path.read_text())
        for k in ("day", "alive", "schema_version"):
            if k in st:
                ident[k] = st[k]
    return ident


class Manifest:
    """Open at experiment start, close at the end; write() both times so
    a crashed run still leaves its identity on disk."""

    def __init__(self, out_dir: Path, *, experiment: str,
                 snapshot_dir: Path | None = None,
                 config: dict | None = None,
                 dataset_hashes: dict | None = None,
                 seeds: dict | None = None,
                 workers: int | None = None,
                 threads_per_worker: int | None = None):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.data = {
            "experiment": experiment,
            "git_sha": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "snapshot": (snapshot_identity(snapshot_dir)
                         if snapshot_dir else None),
            "config": config,
            "config_hash": config_hash(config) if config else None,
            "dataset_hashes": dataset_hashes or {},
            "seeds": seeds or {},
            "machine": machine_spec(),
            "workers": workers,
            "threads_per_worker": threads_per_worker,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                         time.gmtime()),
            "ended_utc": None,
            "wall_clock_s": None,
            "artifacts": [],
        }
        self._t0 = time.monotonic()
        self.write()

    def add_artifact(self, path) -> None:
        self.data["artifacts"].append(str(path))

    def close(self) -> None:
        self.data["ended_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                               time.gmtime())
        self.data["wall_clock_s"] = round(time.monotonic() - self._t0, 1)
        self.write()

    def write(self) -> None:
        (self.out_dir / "manifest.json").write_text(
            json.dumps(self.data, indent=1))
