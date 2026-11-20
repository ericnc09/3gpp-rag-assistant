"""
Semantic document retrieval for the 3GPP RAG pipeline.

Given a natural language query this module:
  1. Embeds the query using the same model used at index time (bge-small by default)
  2. Performs approximate nearest-neighbour search in the ChromaDB vector store
  3. Applies an optional source-document filter
  4. Returns the top-k most similar chunks with similarity scores

The retriever is intentionally stateless (no caching) so it can be safely
shared across concurrent sessions via the FastAPI app_state.

Example:
    retriever = DocumentRetriever(top_k=5)
    docs = retriever.retrieve("What is the F1 interface?")
    context = retriever.format_context(docs)
"""

from typing import List, Dict, Optional
import logging

from src.config import settings
from src.core.embeddings import LocalEmbeddingGenerator
from src.core.retrieval_fusion import fused_retrieve, rrf_merge
from src.core.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Semantic retriever that embeds queries and searches the vector store.

    Attributes:
        vector_store: ChromaDB-backed store holding all indexed spec chunks.
        embedding_generator: Sentence-transformer model for query encoding.
        top_k: Default number of chunks to return per query.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_generator: Optional[LocalEmbeddingGenerator] = None,
        top_k: int = 5,
        hybrid: Optional[bool] = None,
        rerank: Optional[bool] = None,
        expand: Optional[bool] = None,
        decompose: Optional[bool] = None,
    ) -> None:
        """
        Args:
            vector_store: VectorStore instance. A new default instance is
                created if not provided (connects to ./data/vectordb).
            embedding_generator: LocalEmbeddingGenerator instance. Defaults
                to bge-small which must match the model used at index time.
            top_k: Default number of chunks to return. Can be overridden
                per-query via the top_k parameter of retrieve().
            hybrid, rerank, expand, decompose: Per-instance overrides of the
                matching ``settings`` flags (None = use settings). The eval
                ablation uses these to compare pipeline variants in-process.
        """
        self.vector_store = vector_store or VectorStore()
        self.embedding_generator = embedding_generator or LocalEmbeddingGenerator(
            model_name="bge-small"
        )
        self.top_k = top_k
        # None = defer to settings at call time (so runtime config changes
        # and test monkeypatches of `settings` take effect).
        self._overrides = {
            "hybrid_search": hybrid,
            "rerank": rerank,
            "query_expansion": expand,
            "query_decomposition": decompose,
        }
        self._reranker = None
        logger.info(
            f"Initialized DocumentRetriever (top_k={top_k}, hybrid={self.hybrid}, "
            f"rerank={self.rerank})"
        )

    def _flag(self, name: str) -> bool:
        override = self._overrides[name]
        return getattr(settings, name) if override is None else override

    @property
    def hybrid(self) -> bool:
        return self._flag("hybrid_search")

    @property
    def rerank(self) -> bool:
        return self._flag("rerank")

    @property
    def expand(self) -> bool:
        return self._flag("query_expansion")

    @property
    def decompose(self) -> bool:
        return self._flag("query_decomposition")

    @property
    def reranker(self):
        """Lazily constructed cross-encoder (model itself is process-cached)."""
        if self._reranker is None:
            from src.core.reranker import CrossEncoderReranker

            self._reranker = CrossEncoderReranker(settings.rerank_model)
        return self._reranker

    def _bm25_index(self):
        from src.core.bm25 import get_index_for_collection

        collection = self.vector_store.collection
        key = (str(getattr(self.vector_store, "persist_directory", "")),
               collection.name, collection.count())
        return get_index_for_collection(collection, cache_key=key)

    @staticmethod
    def _build_where_filter(
        domain: Optional[str] = None,
        generation: Optional[str] = None,
    ) -> Optional[Dict]:
        """Build a ChromaDB ``where`` clause from domain/generation filters.

        Returns None when no filters are requested (search entire collection).
        """
        conditions = []
        if domain:
            conditions.append({"domain": domain})
        if generation:
            conditions.append({"generation": generation})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None,
        domain: Optional[str] = None,
        generation: Optional[str] = None,
    ) -> List[Dict]:
        """Retrieve the most semantically similar chunks for a query.

        Args:
            query: Natural language question or search string.
            top_k: Override the default number of results for this call.
            source_filter: If set, only return chunks whose source filename
                contains this string (e.g. "38401"). Applied post-retrieval.
            domain: If set, restrict retrieval to "RAN" or "CORE" chunks.
                Applied via ChromaDB metadata filter (pre-retrieval).
            generation: If set, restrict retrieval to "5G" or "LTE" chunks.
                Applied via ChromaDB metadata filter (pre-retrieval).

        Returns:
            List of chunk dicts, each with keys:
                - text        (str)   : chunk content
                - source      (str)   : filename of the source document
                - chunk_index (int)   : position of the chunk in its document
                - similarity  (float) : cosine similarity in [0, 1]
                - domain      (str)   : "RAN" | "CORE" | "unknown"
                - generation  (str)   : "5G" | "LTE" | "unknown"
                - spec_number (str)   : e.g. "38.300"
                - spec_title  (str)   : human-readable spec title
            Sorted descending by similarity, length <= top_k.
        """
        k = top_k or self.top_k

        logger.info(
            f"Retrieving documents for query: '{query[:50]}...' "
            f"[domain={domain}, generation={generation}]"
        )

        where_filter = self._build_where_filter(domain=domain, generation=generation)

        # Bind this call's filters into a search primitive, then delegate the
        # query-rewriting rank fusion to the shared, embedding-agnostic
        # orchestration (also used by the Streamlit Cloud path).
        search = self._hybrid_search if self.hybrid else self._search

        def search_fn(text: str, n: int) -> List[Dict]:
            return search(text, n, where_filter, source_filter)

        retrieved_docs = fused_retrieve(
            query,
            search_fn,
            k,
            expand=self.expand,
            decompose=self.decompose,
            rerank_fn=self.reranker if self.rerank else None,
            rerank_depth=settings.rerank_depth,
        )

        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        return retrieved_docs

    def _search(
        self,
        embed_text: str,
        n: int,
        where_filter: Optional[Dict],
        source_filter: Optional[str],
    ) -> List[Dict]:
        """Embed one query string and return up to n matching chunk dicts.

        Over-fetches when a post-retrieval ``source_filter`` is active so
        that up to n survive the filter.
        """
        query_embedding = self.embedding_generator.generate_embedding(embed_text)
        return self._dense(query_embedding, n, where_filter, source_filter)

    def _dense(
        self,
        query_embedding: List[float],
        n: int,
        where_filter: Optional[Dict],
        source_filter: Optional[str],
    ) -> List[Dict]:
        """Vector-store ANN search for an already-embedded query."""
        n_fetch = n * 2 if source_filter else n
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_fetch,
            where_filter=where_filter,
        )
        ids = (results.get("ids") or [[]])[0] or [None] * len(results["documents"][0])

        retrieved_docs = []
        for chunk_id, doc, metadata, distance in zip(
            ids,
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if source_filter and source_filter not in metadata.get("source", ""):
                continue

            retrieved_docs.append(self._to_doc(chunk_id, doc, metadata, 1 - distance))

            if len(retrieved_docs) >= n:
                break

        return retrieved_docs

    def _hybrid_search(
        self,
        embed_text: str,
        n: int,
        where_filter: Optional[Dict],
        source_filter: Optional[str],
    ) -> List[Dict]:
        """Dense + BM25 search fused with Reciprocal Rank Fusion.

        Both rankings are fetched n deep and RRF-merged (the same fusion as
        query expansion, ADR-009). Chunks found only by BM25 get their
        ``similarity`` computed from their stored embedding, in the same
        units the vector store reports, so every returned doc carries a
        comparable cosine-derived similarity — the refusal threshold and the
        calibrated pass threshold depend on that.
        """
        query_embedding = self.embedding_generator.generate_embedding(embed_text)
        dense = self._dense(query_embedding, n, where_filter, source_filter)

        hits = self._bm25_index().search(embed_text, n, where_filter, source_filter)
        dense_by_id = {d.get("id"): d for d in dense}
        missing = [h["id"] for h in hits if h["id"] not in dense_by_id]
        sims = self._similarities_for_ids(query_embedding, missing)

        keyword = [
            dense_by_id.get(hit["id"])
            or self._to_doc(hit["id"], hit["text"], hit["metadata"], sims.get(hit["id"], 0.0))
            for hit in hits
        ]

        return rrf_merge([dense, keyword])[:n]

    def _similarities_for_ids(
        self, query_embedding: List[float], ids: List[str]
    ) -> Dict[str, float]:
        """Similarity (1 - distance, in the collection's metric) for given ids."""
        if not ids:
            return {}
        collection = self.vector_store.collection
        got = collection.get(ids=ids, include=["embeddings"])
        space = (getattr(collection, "metadata", None) or {}).get("hnsw:space", "l2")
        q = list(query_embedding)
        sims: Dict[str, float] = {}
        for chunk_id, emb in zip(got["ids"], got["embeddings"]):
            dot = sum(a * b for a, b in zip(q, emb))
            if space == "cosine":
                qn = sum(a * a for a in q) ** 0.5
                en = sum(b * b for b in emb) ** 0.5
                distance = 1 - dot / (qn * en or 1.0)
            elif space == "ip":
                distance = 1 - dot
            else:  # ChromaDB "l2" reports squared Euclidean distance
                distance = sum((a - b) ** 2 for a, b in zip(q, emb))
            sims[chunk_id] = 1 - distance
        return sims

    @staticmethod
    def _to_doc(chunk_id, text: str, metadata: Dict, similarity: float) -> Dict:
        return {
            "id": chunk_id,
            "text": text,
            "source": metadata.get("source", "unknown"),
            "chunk_index": metadata.get("chunk_index", 0),
            "similarity": similarity,
            "domain": metadata.get("domain", "unknown"),
            "generation": metadata.get("generation", "unknown"),
            "spec_number": metadata.get("spec_number", "unknown"),
            "spec_title": metadata.get("spec_title", "unknown"),
        }

    def format_context(self, documents: List[Dict]) -> str:
        """Format retrieved chunks into a numbered context block for the LLM prompt.

        Each chunk is prefixed with its index, source filename, and similarity
        score so the LLM can cite the right document in its answer.

        Args:
            documents: List of chunk dicts as returned by retrieve().

        Returns:
            Multi-line string ready to be inserted into PROMPT_TEMPLATE.
            Returns an empty string if documents is empty.
        """
        context_parts = []

        for i, doc in enumerate(documents, 1):
            spec_info = ""
            if doc.get("spec_number") and doc["spec_number"] != "unknown":
                spec_info = f", Spec: TS {doc['spec_number']}"
            context_parts.append(
                f"[Document {i}] (Source: {doc['source']}{spec_info}, Similarity: {doc['similarity']:.3f})\n"
                f"{doc['text']}\n"
            )

        return "\n".join(context_parts)


if __name__ == "__main__":
    # Test the retriever
    import sys

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print("Document Retriever Test")
    print("=" * 60 + "\n")

    # Check if vector store has data
    store = VectorStore()
    stats = store.get_stats()

    if stats["total_chunks"] == 0:
        print("❌ Error: Vector store is empty!")
        print("Please run: python scripts/build_index.py")
        sys.exit(1)

    print(f"Vector store has {stats['total_chunks']} chunks\n")

    # Initialize retriever
    retriever = DocumentRetriever(top_k=3)

    # Test query
    query = "What is the 5G protocol architecture?"
    docs = retriever.retrieve(query)

    print(f"Query: {query}")
    print("=" * 60)

    for i, doc in enumerate(docs, 1):
        print(f"\nResult {i} (similarity: {doc['similarity']:.3f}):")
        print(f"Source: {doc['source']}")
        print(f"Text: {doc['text'][:200]}...")

    print("\n" + "=" * 60)
    print("Context for LLM:")
    print("=" * 60)
    print(retriever.format_context(docs))
    print("\n" + "=" * 60 + "\n")
