"""Stem-family detection — the anchor collision guard.

Direct port of the old engine's `_shared/stem_family.ts` (verified in
vivid-node-forge, 2026-08-18). Its reason for existing, in the
original author's words: many survey stems share prompt shape across
wildly different objects, the embedder scores them 0.82-0.90 similar
because the stem dominates the sentence, and six different
institutions all end up pulling the same solved weights.

Without this guard, "confidence in the press" borrows the calibration
of "confidence in the army" and the population predicts identical
shares for both. With it, a stem match plus an object mismatch forces
`stem_collision`, and the caller caps borrowing at 0.30.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

STEM_PATTERNS = [
    ("justifiable_scale",
     re.compile(r"^\s*(?:is\s+|please\s+tell\s+me\s+whether\s+)?(.+?)"
                r"\s*[—\-:,]?\s*(?:ever\s+|always\s+)?(?:be\s+)?"
                r"justifiab(?:le|ly)\b", re.I)),
    ("confidence_in",
     re.compile(r"\bconfidence\b[^?.!]{0,40}?\bin\s+(.+?)\s*[?.!]*\s*$",
                re.I)),
    ("importance_of",
     re.compile(r"\b(?:how\s+important\s+is|importance\s+of)\s+(.+?)"
                r"(?:\s+in\s+your\s+life)?\s*[?.!]*\s*$", re.I)),
    ("interest_in",
     re.compile(r"\b(?:how\s+interested\s+are\s+you\s+in|interest\s+in)"
                r"\s+(.+?)\s*[?.!]*\s*$", re.I)),
    ("satisfaction_with",
     re.compile(r"\b(?:how\s+satisfied\s+are\s+you\s+with|"
                r"satisfaction\s+with)\s+(.+?)\s*[?.!]*\s*$", re.I)),
    ("proud_of",
     re.compile(r"\b(?:how\s+)?proud\s+(?:are\s+you\s+)?of\s+(.+?)"
                r"\s*[?.!]*\s*$", re.I)),
]

STOP = {"the", "a", "an", "of", "in", "on", "for", "to", "your", "our",
        "my", "this", "that", "these", "those", "some", "any", "all"}


def _normalize(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", s.lower(), flags=re.UNICODE)
    return " ".join(w for w in s.split() if w and w not in STOP)


@dataclass
class StemMatch:
    family: str
    object: str
    object_normalized: str


def detect_stem(text: str) -> StemMatch | None:
    """First matching family wins (order is significant, as in the TS)."""
    for family, pattern in STEM_PATTERNS:
        m = pattern.search(text or "")
        if m:
            obj = m.group(1).strip()
            return StemMatch(family=family, object=obj,
                             object_normalized=_normalize(obj))
    return None


def classify_pair(a: str, b: str) -> str:
    """'stem_collision' | 'same_stem_same_object' | 'no_stem_signal'."""
    sa, sb = detect_stem(a), detect_stem(b)
    if not sa or not sb or sa.family != sb.family:
        return "no_stem_signal"
    if sa.object_normalized == sb.object_normalized:
        return "same_stem_same_object"
    return "stem_collision"


# dampening caps, ported from the old cascade
CAPS = {"same_question": 1.00, "same_pole": 0.85,
        "different_question": 0.60, "stem_collision": 0.30}


def dampening_factor(similarity: float, classification: str) -> float:
    """factor = min(cap, (sim - 0.50) / 0.35), floored at 0."""
    cap = CAPS.get(classification, 0.60)
    return max(0.0, min(cap, (similarity - 0.50) / 0.35))
