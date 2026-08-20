"""THE ONE-PRODUCTION-EARTH GATE — Phase 0.5.

Legacy code may explain history. Legacy code may not define present
Earth. This module is the machine-enforced form of that sentence: it
scans the PRODUCTION import surface and refuses any path to the
retired engine family.

Production surface = everything that serves, evolves, persists or
brands the canonical world:
    the daemon, the API package, the canonical modules themselves.

Quarantined family = the old opinion engine and its exclusive organs.
They remain in the tree as historical comparators (benchmarks that
graded them are scientific record), reachable ONLY by explicit,
non-production imports.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The retired family. Importing any of these from a production module
# is a release-refusing violation.
QUARANTINED = {
    "earth1.engine", "earth1.tick", "earth1.living", "earth1.advance",
    "earth1.diffusion", "earth1.forces", "earth1.dynamics",
    "earth1.coupling", "earth1.graph_dynamics", "earth1.event_generation",
    "earth1.perishability",
}

# The production import surface: the canonical world and everything
# that serves it. tests/ and scripts/ may import legacy explicitly
# (comparators, archaeology); production may not.
PRODUCTION = [
    "earth1/__init__.py", "earth1/alive.py", "earth1/persistence.py",
    "earth1/provenance.py", "earth1/rebirth.py", "earth1/rehome.py",
    "earth1/release_gate.py", "earth1/calibration.py", "earth1/chaos.py",
    "earth1/life.py", "earth1/health.py", "earth1/institutions.py",
    "earth1/knowledge.py", "earth1/weather.py", "earth1/flourishing.py",
    "earth1/contagion.py", "earth1/mobility.py", "earth1/feed.py",
    "earth1/memory.py", "earth1/influence.py", "earth1/susceptibility.py",
    "earth1/fabric.py", "earth1/genesis.py", "earth1/types.py",
    "earth1/thresholds.py", "earth1/timeline.py", "earth1/branch.py",
    "earth1/assimilate.py", "earth1/observe.py", "earth1/observer.py",
    # answer.py: audited orphan (zero importers) awaiting its
    # Benchmark-A rebuild on the living readout; re-enters this list
    # the moment it serves a production path
    "earth1/integration.py",
    "scripts/world_alive.py",
    # the whole product API package, enumerated at scan time
    "earth1/api",
]


def _imports_of(path: Path):
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield node.lineno, a.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.lineno, node.module
            for a in node.names:
                yield node.lineno, f"{node.module}.{a.name}"


def scan() -> list:
    """Every production import of a quarantined module, as violations."""
    files = []
    for entry in PRODUCTION:
        p = ROOT / entry
        if p.is_dir():
            files.extend(f for f in sorted(p.rglob("*.py"))
                         if "routes_legacy" not in f.parts)
        elif p.exists():
            files.append(p)
    violations = []
    for f in files:
        for lineno, mod in _imports_of(f):
            root = ".".join(mod.split(".")[:2])
            if root in QUARANTINED or mod in QUARANTINED:
                try:
                    rel = f.relative_to(ROOT)
                except ValueError:
                    rel = f
                violations.append(f"{rel}:{lineno} imports {mod}")
    return violations


def assert_one_production_earth() -> None:
    v = scan()
    if v:
        raise RuntimeError(
            "ONE-PRODUCTION-EARTH VIOLATED — production paths import the "
            "retired engine family:\n  " + "\n  ".join(v)
            + "\nLegacy code may explain history; it may not define "
              "present Earth.")


if __name__ == "__main__":
    bad = scan()
    if bad:
        print("VIOLATIONS:")
        for b in bad:
            print(" ", b)
        raise SystemExit(1)
    print("one production Earth: no production path reaches the retired "
          "family")
