"""Retrieval corpus — Phase 3 perception (bible §19.1).

The LLM fires only at the novelty frontier: when a near-neighbour exists
in the corpus (cosine similarity ≥ min_sim), retrieval supplies the solved
force loadings and no model call happens. The LLM footprint therefore
shrinks as the corpus grows.

Embeddings are hashed TF-IDF vectors computed in pure numpy — deterministic,
no network, no model download. Good at what the corpus needs: recognising
near-duplicate and closely-paraphrased survey questions. Novel phrasings
fall below the threshold and route to the LLM, which is the intended design.
"""
from __future__ import annotations

import json
import re
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np

from earth1.types import Question, NUM_FORCES

EMBED_DIM = 4096
DEFAULT_MIN_SIM = 0.85

_STOPWORDS = frozenset(
    "a an and are as at be by do does for from has have how i in is it its of on "
    "or that the this to was what when where which who will with would you your".split()
)

_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokenize(text: str) -> List[str]:
    words = [w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS]
    bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def _token_slot(token: str) -> tuple[int, float]:
    """Stable hash → (dimension, sign). crc32 is deterministic across runs."""
    h = zlib.crc32(token.encode("utf-8"))
    return h % EMBED_DIM, 1.0 if (h >> 31) & 1 == 0 else -1.0


def _term_counts(text: str) -> dict:
    counts: dict = {}
    for tok in _tokenize(text):
        counts[tok] = counts.get(tok, 0) + 1
    return counts


class _Vectorizer:
    """Hashed TF-IDF. IDF is learned at build time and frozen thereafter."""

    def __init__(self, idf: Optional[dict] = None):
        self.idf = idf or {}
        self.n_docs = 0

    def fit(self, texts: List[str]) -> None:
        df: dict = {}
        for t in texts:
            for tok in set(_tokenize(t)):
                df[tok] = df.get(tok, 0) + 1
        self.n_docs = len(texts)
        self.idf = {
            tok: float(np.log((1 + self.n_docs) / (1 + d)) + 1.0)
            for tok, d in df.items()
        }

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(EMBED_DIM, dtype=np.float64)
        for tok, tf in _term_counts(text).items():
            slot, sign = _token_slot(tok)
            idf = self.idf.get(tok, 1.0)
            vec[slot] += sign * (1.0 + np.log(tf)) * idf
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec


@dataclass
class CorpusHit:
    id: str
    text: str
    baseline: float          # logit-space
    weights: np.ndarray      # (NUM_FORCES,)
    domain: str
    lens: str
    source: str
    similarity: float
    response_profile: Optional[np.ndarray] = None   # ONE LAW: temporal coupling

    def to_question(self, qid: Optional[str] = None) -> Question:
        return Question(
            id=qid or self.id, text=self.text, domain=self.domain,
            baseline=self.baseline, weights=self.weights.copy(), lens=self.lens,
            response_profile=(self.response_profile.copy()
                              if self.response_profile is not None else None),
        )


class QuestionCorpus:
    """Solved-question store with nearest-neighbour retrieval."""

    def __init__(self):
        self.ids: List[str] = []
        self.texts: List[str] = []
        self.baselines: np.ndarray = np.zeros(0)
        self.weights: np.ndarray = np.zeros((0, NUM_FORCES))
        self.domains: List[str] = []
        self.lenses: List[str] = []
        self.sources: List[str] = []
        # ONE LAW: per-entry temporal response profile; NaN row = not
        # yet authored (question is event-inert until authored)
        self.profiles: np.ndarray = np.zeros((0, NUM_FORCES))
        self.matrix: np.ndarray = np.zeros((0, EMBED_DIM))
        self.vectorizer = _Vectorizer()

    def __len__(self) -> int:
        return len(self.ids)

    def build(
        self,
        ids: List[str],
        texts: List[str],
        baselines: np.ndarray,
        weights: np.ndarray,
        domains: Optional[List[str]] = None,
        lenses: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
    ) -> None:
        n = len(ids)
        self.ids = list(ids)
        self.texts = list(texts)
        self.baselines = np.asarray(baselines, dtype=np.float64)
        self.weights = np.asarray(weights, dtype=np.float64)
        self.domains = list(domains) if domains else ["belief_causal"] * n
        self.lenses = list(lenses) if lenses else ["wvs"] * n
        self.sources = list(sources) if sources else ["corpus"] * n
        self.vectorizer.fit(self.texts)
        self.matrix = np.stack([self.vectorizer.embed(t) for t in self.texts])

    def _profile(self, idx: int):
        """Stored response profile, or None while un-authored (NaN)."""
        if idx >= len(self.profiles):
            return None
        row = self.profiles[idx]
        return None if np.isnan(row).any() else row

    def add(
        self, id: str, text: str, baseline: float, weights: np.ndarray,
        domain: str = "belief_causal", lens: str = "wvs", source: str = "llm",
        response_profile: Optional[np.ndarray] = None,
    ) -> None:
        """Append a newly-solved question. IDF stays frozen (build-time)."""
        self.ids.append(id)
        self.texts.append(text)
        self.baselines = np.append(self.baselines, baseline)
        self.weights = np.vstack([self.weights, np.asarray(weights)[np.newaxis, :]])
        prof = (np.asarray(response_profile, dtype=np.float64)
                if response_profile is not None
                else np.full(NUM_FORCES, np.nan))
        self.profiles = np.vstack([self.profiles, prof[np.newaxis, :]])
        self.domains.append(domain)
        self.lenses.append(lens)
        self.sources.append(source)
        vec = self.vectorizer.embed(text)
        self.matrix = np.vstack([self.matrix, vec[np.newaxis, :]])

    def nearest(
        self, text: str, min_sim: float = DEFAULT_MIN_SIM,
        exclude_id: Optional[str] = None,
    ) -> Optional[CorpusHit]:
        if len(self.ids) == 0:
            return None
        qvec = self.vectorizer.embed(text)
        sims = self.matrix @ qvec
        if exclude_id is not None:
            for i, cid in enumerate(self.ids):
                if cid == exclude_id:
                    sims[i] = -1.0
        best = int(np.argmax(sims))
        if sims[best] < min_sim:
            return None
        return CorpusHit(
            id=self.ids[best], text=self.texts[best],
            baseline=float(self.baselines[best]), weights=self.weights[best],
            domain=self.domains[best], lens=self.lenses[best],
            source=self.sources[best], similarity=float(sims[best]),
            response_profile=self._profile(best),
        )

    def retrieve(
        self,
        text: str,
        min_sim: float = DEFAULT_MIN_SIM,
        k: int = 5,
        min_weight_agreement: float = 0.8,
        exact_sim: float = 0.995,
        exclude_id: Optional[str] = None,
    ) -> Optional[CorpusHit]:
        """Weight-safe retrieval. Text similarity alone is not enough:
        survey questions share long stems while the subject flips the
        loadings ("opinion of Russia" vs "opinion of Iran"). Reuse only
        fires when (a) the match is a near-exact duplicate, or (b) the
        neighbourhood's weights agree with each other — a coherent region
        of question-space. Otherwise: novelty frontier, route to the LLM.
        """
        if len(self.ids) == 0:
            return None
        qvec = self.vectorizer.embed(text)
        sims = self.matrix @ qvec
        if exclude_id is not None:
            for i, cid in enumerate(self.ids):
                if cid == exclude_id:
                    sims[i] = -1.0

        order = np.argsort(sims)[::-1]
        best = int(order[0])
        if sims[best] < min_sim:
            return None

        def _hit(idx: int, weights: Optional[np.ndarray] = None) -> CorpusHit:
            return CorpusHit(
                id=self.ids[idx], text=self.texts[idx],
                baseline=float(self.baselines[idx]),
                response_profile=self._profile(idx),
                weights=self.weights[idx] if weights is None else weights,
                domain=self.domains[idx], lens=self.lenses[idx],
                source=self.sources[idx], similarity=float(sims[idx]),
            )

        # (a) near-exact duplicate — same question, safe to reuse directly
        if sims[best] >= exact_sim:
            return _hit(best)

        # (b) neighbourhood consensus
        nbrs = [int(i) for i in order[:k] if sims[i] >= min_sim]
        if len(nbrs) < 2:
            return None
        W = self.weights[nbrs]
        norms = np.linalg.norm(W, axis=1)
        valid = norms > 1e-12
        if valid.sum() < 2:
            return None
        Wn = W[valid] / norms[valid, np.newaxis]
        cos = Wn @ Wn.T
        iu = np.triu_indices(len(Wn), k=1)
        if float(cos[iu].mean()) < min_weight_agreement:
            return None

        sim_w = sims[nbrs][valid]
        sim_w = sim_w / sim_w.sum()
        blended = (W[valid] * sim_w[:, np.newaxis]).sum(axis=0)
        return _hit(best, weights=blended)

    # ── persistence ──

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path.with_suffix(".npz"),
            baselines=self.baselines, weights=self.weights, matrix=self.matrix,
            profiles=self.profiles,
        )
        meta = {
            "ids": self.ids, "texts": self.texts, "domains": self.domains,
            "lenses": self.lenses, "sources": self.sources,
            "idf": self.vectorizer.idf, "n_docs": self.vectorizer.n_docs,
            "embed_dim": EMBED_DIM,
        }
        with open(path.with_suffix(".json"), "w") as f:
            json.dump(meta, f)

    @classmethod
    def load(cls, path: str | Path) -> "QuestionCorpus":
        path = Path(path)
        arrays = np.load(path.with_suffix(".npz"))
        with open(path.with_suffix(".json")) as f:
            meta = json.load(f)
        c = cls()
        c.ids = meta["ids"]
        c.texts = meta["texts"]
        c.domains = meta["domains"]
        c.lenses = meta["lenses"]
        c.sources = meta["sources"]
        c.baselines = arrays["baselines"]
        c.weights = arrays["weights"]
        c.matrix = arrays["matrix"]
        c.profiles = (arrays["profiles"] if "profiles" in arrays
                      else np.full((len(c.ids), NUM_FORCES), np.nan))
        c.vectorizer = _Vectorizer(idf=meta["idf"])
        c.vectorizer.n_docs = meta["n_docs"]
        return c
