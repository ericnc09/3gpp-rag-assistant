"""
Cross-encoder reranking stage (Sprint 1, ADR-012).

A bi-encoder (bge-small) embeds query and chunk independently, so it can only
compare two fixed vectors. A cross-encoder reads the (query, chunk) pair
together and scores relevance directly — much more accurate, but far too
slow to run over 43k chunks. The standard compromise: retrieve a candidate
pool cheaply (dense + BM25), then rerank only the top ``depth`` candidates.

Default model: ``cross-encoder/ms-marco-MiniLM-L-6-v2`` (~90 MB, 6 layers),
chosen for CPU latency. It is trained on MS MARCO web queries, not telecom
text — whether it helps on 3GPP is an empirical question the eval answers.

The model is loaded lazily and cached per process (the API builds a
``DocumentRetriever`` per session; the model must not be reloaded each time).
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List

logger = logging.getLogger(__name__)

DEFAULT_RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_MODEL_CACHE: Dict[str, object] = {}
_LOCK = threading.Lock()


def _load_cross_encoder(model_name: str):
    with _LOCK:
        model = _MODEL_CACHE.get(model_name)
        if model is None:
            from sentence_transformers import CrossEncoder

            logger.info(f"Loading cross-encoder reranker: {model_name}")
            model = CrossEncoder(model_name, max_length=512, device="cpu")
            _MODEL_CACHE[model_name] = model
        return model


class CrossEncoderReranker:
    """Rerank retrieved chunks by cross-encoder relevance.

    Usable as the ``rerank_fn`` callback of ``fused_retrieve``:
    ``reranker(query, docs) -> docs`` sorted by ``rerank_score`` descending.
    The original cosine ``similarity`` is preserved on each doc, so
    similarity-based thresholds (refusal, calibrated pass) keep their meaning.
    """

    def __init__(self, model_name: str = DEFAULT_RERANK_MODEL, batch_size: int = 32) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = _load_cross_encoder(self.model_name)
        return self._model

    def score(self, query: str, texts: List[str]) -> List[float]:
        if not texts:
            return []
        pairs = [(query, text) for text in texts]
        scores = self.model.predict(pairs, batch_size=self.batch_size, show_progress_bar=False)
        return [float(s) for s in scores]

    def __call__(self, query: str, docs: List[Dict]) -> List[Dict]:
        if not docs:
            return []
        scores = self.score(query, [d.get("text", "") for d in docs])
        reranked = [{**doc, "rerank_score": round(s, 4)} for doc, s in zip(docs, scores)]
        reranked.sort(key=lambda d: d["rerank_score"], reverse=True)
        return reranked
