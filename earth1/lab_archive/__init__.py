"""LAB ARCHIVE — the 0.8 laboratory assembly that produced candidate
76a574c (field_lab, conviction_lab, propagation_lab).

PROVENANCE ONLY. Canonicalization (Programs 1–2, PORT_EQUIVALENCE_
REPORT.md) proved the flagless canonical `live_one_day` bitwise
identical to this assembly over 365 days at 200k agents; from that
commit the canonical modules are the ONE authoritative implementation
and this package is quarantined (legacy_gate.QUARANTINED). It is kept
so every 0.8 registration and artifact stays reproducible, and it
refuses to import unless explicitly opted in for archaeology:

    EARTH1_LAB_ARCHIVE=1

Nothing here may define present Earth.
"""
import os as _os

if _os.environ.get("EARTH1_LAB_ARCHIVE") != "1":
    raise ImportError(
        "earth1.lab_archive is PROVENANCE ONLY (the retired 0.8 lab "
        "assembly, superseded bitwise by canonical live_one_day). Set "
        "EARTH1_LAB_ARCHIVE=1 to import it for archaeology/comparison.")
