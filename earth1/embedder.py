"""SEMANTIC EMBEDDINGS for the grounding cascade.

The old engine used GTE (gte_embed.ts). Earth-1's corpus embedder is
hashed TF-IDF — still lexical, so 'is euthanasia justifiable' cannot
find 'is homosexuality justifiable' despite them being neighbours in
the same WVS justifiability family. This wires a real sentence
embedder into the cascade so Path B's lowered floor catches semantic
neighbours instead of token-overlap coincidences.

Model: thenlper/gte-base (the GTE family the old engine used),
loaded lazily, cached on disk. Falls back to the lexical Jaccard when
the model is unavailable — the fallback is CONSERVATIVE (it
under-matches, routing questions DOWN the cascade to lower-confidence
tiers, never up).

CRITICAL ORDERING (and the reason the stem guard matters MORE here):
embeddings score 'confidence in the press' and 'confidence in the
army' at 0.85+ because the stem dominates the sentence. The cascade
must therefore run, in this order:
    1. similarity score  (semantic)
    2. stem-collision check  (stem_family.classify_pair)
    3. dampening cap  (0.30 for a collision, whatever the similarity)
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np

MODEL_NAME = os.environ.get("EARTH1_EMBED_MODEL", "thenlper/gte-base")
CACHE = Path(__file__).resolve().parents[1] / "data" / "seed_corpus" / \
    "embeddings.npz"
_model = None
_cache: dict = {}


def available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _key(text: str) -> str:
    return hashlib.sha1((MODEL_NAME + "|" + (text or "")).encode()).hexdigest()


def load_cache() -> dict:
    global _cache
    if _cache:
        return _cache
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=False)
        _cache = {k: z[k] for k in z.files}
    return _cache


def save_cache() -> None:
    if _cache:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(CACHE, **_cache)


def embed(texts: list, use_cache: bool = True) -> np.ndarray | None:
    """Unit-normalized embeddings, or None when the model is absent."""
    if not available():
        return None
    cache = load_cache() if use_cache else {}
    missing = [t for t in texts if _key(t) not in cache]
    if missing:
        vecs = _get_model().encode(missing, normalize_embeddings=True,
                                   show_progress_bar=False)
        for t, v in zip(missing, np.asarray(vecs, dtype=np.float32)):
            cache[_key(t)] = v
        if use_cache:
            globals()["_cache"] = cache
    return np.stack([cache[_key(t)] for t in texts])


def similarity(a: str, b: str) -> float | None:
    v = embed([a, b])
    return None if v is None else float(np.dot(v[0], v[1]))


def build_corpus_embeddings(corpus: list) -> int:
    """Precompute and cache embeddings for every distinct seed question."""
    texts = sorted({s["question_text"] for s in corpus})
    if embed(texts) is None:
        return 0
    save_cache()
    return len(texts)
