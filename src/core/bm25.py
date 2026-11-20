"""
Okapi BM25 keyword index for hybrid retrieval (Sprint 1, ADR-012).

Why a keyword index next to the dense one: 3GPP questions are full of exact
identifiers — message names (``RRCReconfiguration``), timers (``T310``),
interfaces (``N2``, ``F1-C``), IEs and clause numbers (``5.3.5.4``). A
384-dim sentence embedding blurs these into "something about RRC"; a lexical
index matches them exactly. Dense and BM25 rankings are fused with the same
Reciprocal Rank Fusion already used for query expansion (ADR-009).

Design constraints:
  * **Pure Python, stdlib only.** Like ``retrieval_fusion``, this module must
    be importable on the torch-free Streamlit Cloud path.
  * **Compact postings.** 43k chunks produce millions of postings; storing
    them as ``array`` pairs instead of tuples keeps the index in tens of MB.
  * **Built from the vector store.** The index is derived from the ChromaDB
    collection's stored documents, so there is no second artifact to ship or
    keep in sync. It is built once per process and cached by
    (path, collection, count).
"""

from __future__ import annotations

import heapq
import logging
import math
import re
import time
from array import array
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Compound tokens keep their separators so identifiers survive intact:
# "gnb-cu", "5.3.5.4", "f1-c", "ng-ran", "rel-17". Each compound also emits
# its parts (see tokenize) so "gNB-CU" still matches a query for "gNB".
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-._/][a-z0-9]+)*")
_SPLIT_RE = re.compile(r"[-._/]")

# Deliberately small: technical vocabulary ("and", "or" aside) is signal.
STOPWORDS = frozenset(
    """a an and are as at be been but by can do does for from has have how
    in into is it its may of on or shall should that the their then there
    these this to was were what when where which while who why will with
    within without would between used use""".split()
)


def tokenize(text: str) -> List[str]:
    """Lower-case, identifier-preserving tokenizer.

    ``"The gNB-CU sends RRCReconfiguration (clause 5.3.5.4)"`` →
    ``["gnb-cu", "gnb", "cu", "sends", "rrcreconfiguration",
    "clause", "5.3.5.4"]``. Dotted numbers are kept whole only (their parts
    are meaningless digits); other compounds also emit their parts.
    """
    tokens: List[str] = []
    for match in _TOKEN_RE.finditer(text.lower()):
        tok = match.group(0)
        if tok in STOPWORDS:
            continue
        tokens.append(tok)
        if _SPLIT_RE.search(tok) and not tok.replace(".", "").isdigit():
            for part in _SPLIT_RE.split(tok):
                if part and part not in STOPWORDS and len(part) > 1:
                    tokens.append(part)
    return tokens


def matches_where(metadata: Dict, where: Optional[Dict]) -> bool:
    """Evaluate the subset of ChromaDB ``where`` syntax the retriever emits.

    Supports ``{"field": value}`` equality and ``{"$and": [...]}`` — exactly
    the shapes built by ``DocumentRetriever._build_where_filter``.
    """
    if not where:
        return True
    if "$and" in where:
        return all(matches_where(metadata, clause) for clause in where["$and"])
    return all(metadata.get(key) == value for key, value in where.items())


class BM25Index:
    """In-memory Okapi BM25 over a fixed document collection.

    Args:
        ids: Stable document ids (ChromaDB ids), parallel to texts.
        texts: Document texts.
        metadatas: Per-document metadata dicts (returned with hits and used
            for ``where`` filtering).
        k1, b: Standard BM25 parameters (Robertson defaults).
    """

    def __init__(
        self,
        ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        k1: float = 1.2,
        b: float = 0.75,
    ) -> None:
        if len(ids) != len(texts):
            raise ValueError("ids and texts must be the same length")
        self.ids = list(ids)
        self.texts = list(texts)
        self.metadatas = list(metadatas) if metadatas is not None else [{} for _ in ids]
        self.k1 = k1
        self.b = b

        t0 = time.time()
        self._postings: Dict[str, Tuple[array, array]] = {}
        self._doc_len = array("I")
        for doc_idx, text in enumerate(self.texts):
            counts = Counter(tokenize(text or ""))
            self._doc_len.append(sum(counts.values()))
            for term, tf in counts.items():
                entry = self._postings.get(term)
                if entry is None:
                    entry = (array("I"), array("H"))
                    self._postings[term] = entry
                entry[0].append(doc_idx)
                entry[1].append(min(tf, 65535))

        self.n_docs = len(self.texts)
        self.avg_doc_len = (sum(self._doc_len) / self.n_docs) if self.n_docs else 0.0
        self._idf = {
            term: math.log(1.0 + (self.n_docs - len(docs) + 0.5) / (len(docs) + 0.5))
            for term, (docs, _) in self._postings.items()
        }
        logger.info(
            f"Built BM25 index: {self.n_docs} docs, {len(self._postings)} terms "
            f"in {time.time() - t0:.1f}s"
        )

    def __len__(self) -> int:
        return self.n_docs

    def score(self, query: str) -> Dict[int, float]:
        """Return {doc_idx: bm25_score} for every doc matching any query term."""
        scores: Dict[int, float] = {}
        if not self.n_docs:
            return scores
        k1, b, avg = self.k1, self.b, self.avg_doc_len or 1.0
        doc_len = self._doc_len
        # Repeated query terms count once: expansion can repeat a term and
        # BM25 query-term frequency would otherwise over-weight it.
        for term in dict.fromkeys(tokenize(query)):
            entry = self._postings.get(term)
            if entry is None:
                continue
            idf = self._idf[term]
            docs, tfs = entry
            for doc_idx, tf in zip(docs, tfs):
                norm = k1 * (1.0 - b + b * doc_len[doc_idx] / avg)
                scores[doc_idx] = scores.get(doc_idx, 0.0) + idf * tf * (k1 + 1.0) / (tf + norm)
        return scores

    def search(
        self,
        query: str,
        n: int,
        where: Optional[Dict] = None,
        source_filter: Optional[str] = None,
    ) -> List[Dict]:
        """Top-n documents by BM25 score, after metadata filtering.

        Returns dicts with ``id``, ``text``, ``metadata`` and ``bm25_score``.
        """
        scores = self.score(query)
        if not scores or n <= 0:
            return []

        def allowed(doc_idx: int) -> bool:
            meta = self.metadatas[doc_idx]
            if source_filter and source_filter not in meta.get("source", ""):
                return False
            return matches_where(meta, where)

        candidates: Iterable[Tuple[int, float]] = scores.items()
        if where or source_filter:
            candidates = ((i, s) for i, s in candidates if allowed(i))
        top = heapq.nlargest(n, candidates, key=lambda item: item[1])
        return [
            {
                "id": self.ids[i],
                "text": self.texts[i],
                "metadata": self.metadatas[i],
                "bm25_score": round(s, 4),
            }
            for i, s in top
        ]


# ---------------------------------------------------------------------------
# Building from a ChromaDB collection (cached per process)
# ---------------------------------------------------------------------------

_INDEX_CACHE: Dict[Tuple, BM25Index] = {}


def build_from_collection(collection, batch_size: int = 5000) -> BM25Index:
    """Read every stored document from a ChromaDB collection into BM25."""
    total = collection.count()
    ids: List[str] = []
    texts: List[str] = []
    metas: List[Dict] = []
    for offset in range(0, total, batch_size):
        page = collection.get(include=["documents", "metadatas"], limit=batch_size, offset=offset)
        ids.extend(page["ids"])
        texts.extend(page["documents"])
        metas.extend(page["metadatas"])
    return BM25Index(ids, texts, metas)


def get_index_for_collection(collection, cache_key: Optional[Tuple] = None) -> BM25Index:
    """Return a cached BM25 index for a collection, building it on first use.

    The key includes the collection count, so re-indexing invalidates it.
    """
    key = cache_key or (getattr(collection, "name", "collection"), collection.count())
    index = _INDEX_CACHE.get(key)
    if index is None:
        index = build_from_collection(collection)
        _INDEX_CACHE[key] = index
    return index


def clear_cache() -> None:
    """Drop all cached indexes (tests, or after a rebuild in-process)."""
    _INDEX_CACHE.clear()
