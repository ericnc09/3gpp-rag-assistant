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
from src.core.query_decomposition import decompose_query
from src.core.query_expansion import expand_query
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
    ) -> None:
        """
        Args:
            vector_store: VectorStore instance. A new default instance is
                created if not provided (connects to ./data/vectordb).
            embedding_generator: LocalEmbeddingGenerator instance. Defaults
                to bge-small which must match the model used at index time.
            top_k: Default number of chunks to return. Can be overridden
                per-query via the top_k parameter of retrieve().
        """
        self.vector_store = vector_store or VectorStore()
        self.embedding_generator = embedding_generator or LocalEmbeddingGenerator(
            model_name="bge-small"
        )
        self.top_k = top_k
        logger.info(f"Initialized DocumentRetriever (top_k={top_k})")
    
    @staticmethod
    def _rrf_merge(ranked_lists: List[List[Dict]], k_const: int = 60) -> List[Dict]:
        """Merge ranked doc lists via Reciprocal Rank Fusion.

        RRF score(doc) = sum over lists of 1 / (k_const + rank), so a doc
        ranked well in several lists beats a doc ranked well in only one.
        Chunks are identified by (source, chunk_index); the first-seen doc
        dict (with its own cosine similarity) is kept for each chunk.

        Why fusion: replacing the query with its vocabulary-expanded form
        fixed vocabulary-divergent misses but regressed previously-good
        queries (measured 2026-07-02: hit-rate@5 0.88 -> 0.80). Fusing the
        raw and expanded rankings keeps the raw ranking's signal while the
        expanded ranking rescues queries whose phrasing diverges from spec
        terminology.
        """
        scores: Dict = {}
        docs_by_key: Dict = {}
        for ranked in ranked_lists:
            for rank, doc in enumerate(ranked, start=1):
                key = (doc.get("source"), doc.get("chunk_index"))
                scores[key] = scores.get(key, 0.0) + 1.0 / (k_const + rank)
                docs_by_key.setdefault(key, doc)
        ordered = sorted(scores, key=lambda key: scores[key], reverse=True)
        return [docs_by_key[key] for key in ordered]

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

        # Fetch extra results when post-retrieval source_filter is also active
        n_fetch = k * 2 if source_filter else k

        retrieved_docs = self._search(query, n_fetch, where_filter, source_filter, k)

        # Query rewriting. Two rewriters, two merge strategies:
        #
        # 1. Vocabulary expansion (TR 21.905 full forms) — RRF-fused with
        #    the raw ranking. The raw ranking is never discarded: replacing
        #    it was measured to regress previously-good queries (see
        #    _rrf_merge).
        # 2. Comparison decomposition — a "difference between X and Y"
        #    question gets one sub-query per side. RRF is deliberately NOT
        #    used to merge the sides: RRF rewards consensus across lists,
        #    and a comparison's per-side evidence appears in exactly one
        #    list, so it always loses to consensus noise (measured: global
        #    RRF left both comparison misses at hit-rate 0). Sides get
        #    round-robin slot allocation instead (_interleave_sides), with
        #    the fused base ranking as backfill.
        #
        # Queries that trigger neither rewriter skip the extra searches.
        expanded: Optional[str] = None
        if settings.query_expansion:
            candidate = expand_query(query)
            if candidate != query:
                expanded = candidate

        subqueries: List[str] = []
        if settings.query_decomposition:
            subqueries = decompose_query(query)

        if expanded or subqueries:
            base_lists = [retrieved_docs]
            if expanded:
                base_lists.append(
                    self._search(expanded, n_fetch, where_filter, source_filter, k)
                )
            base = self._rrf_merge(base_lists)

            if subqueries:
                # Each side is itself a raw+expanded RRF fusion — the same
                # never-discard-the-raw-text principle as the main path
                # (searching only the expanded side text was measured to
                # push the relevant spec out of the side's own top-10).
                # Sides search deeper (2k) so per-source dedup has room.
                side_lists = []
                for sub in subqueries:
                    sub_lists = [
                        self._search(sub, k * 2, where_filter, source_filter, k * 2)
                    ]
                    if settings.query_expansion:
                        sub_expanded = expand_query(sub)
                        if sub_expanded != sub:
                            sub_lists.append(
                                self._search(
                                    sub_expanded, k * 2, where_filter,
                                    source_filter, k * 2,
                                )
                            )
                    side_lists.append(
                        self._rrf_merge(sub_lists) if len(sub_lists) > 1 else sub_lists[0]
                    )
                logger.info(f"Comparison query: interleaving {len(side_lists)} sides")
                retrieved_docs = self._interleave_sides(side_lists, base, k)
            else:
                retrieved_docs = self._cap_per_source(base, k)

        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        return retrieved_docs

    @staticmethod
    def _interleave_sides(
        side_lists: List[List[Dict]], backfill: List[Dict], k: int
    ) -> List[Dict]:
        """Allocate top-k slots round-robin across a comparison's sides.

        Each side's list is walked in rank order; a chunk is taken only if
        its source document is not yet represented (a comparison needs
        breadth across specs, not depth in one). Remaining slots backfill
        from the fused base ranking.
        """
        selected: List[Dict] = []
        seen_chunks: set = set()
        seen_sources: set = set()

        cursors = [0] * len(side_lists)
        exhausted = [False] * len(side_lists)
        while len(selected) < k and not all(exhausted):
            for i, side in enumerate(side_lists):
                if len(selected) >= k:
                    break
                while cursors[i] < len(side):
                    doc = side[cursors[i]]
                    cursors[i] += 1
                    key = (doc.get("source"), doc.get("chunk_index"))
                    if doc.get("source") in seen_sources or key in seen_chunks:
                        continue
                    selected.append(doc)
                    seen_chunks.add(key)
                    seen_sources.add(doc.get("source"))
                    break
                else:
                    exhausted[i] = True

        for doc in backfill:
            if len(selected) >= k:
                break
            key = (doc.get("source"), doc.get("chunk_index"))
            if key in seen_chunks:
                continue
            selected.append(doc)
            seen_chunks.add(key)
        return selected[:k]

    # Maximum chunks from a single source document in a fused top-k. Multi-
    # spec questions need evidence from more than one spec; without a cap a
    # single strong document can fill every slot. Value chosen so a
    # dominant source keeps a clear majority (3 of 5) while up to two slots
    # stay open for other sources; effects are measured by the eval harness.
    MAX_CHUNKS_PER_SOURCE = 3

    @classmethod
    def _cap_per_source(cls, docs: List[Dict], k: int) -> List[Dict]:
        """Take the top-k of a ranked list, limiting chunks per source.

        Walks the ranking in order, deferring chunks beyond
        MAX_CHUNKS_PER_SOURCE from the same source document; deferred
        chunks backfill only if fewer than k others exist.
        """
        selected: List[Dict] = []
        deferred: List[Dict] = []
        counts: Dict = {}
        for doc in docs:
            source = doc.get("source")
            if counts.get(source, 0) < cls.MAX_CHUNKS_PER_SOURCE:
                selected.append(doc)
                counts[source] = counts.get(source, 0) + 1
            else:
                deferred.append(doc)
            if len(selected) >= k:
                break
        for doc in deferred:
            if len(selected) >= k:
                break
            selected.append(doc)
        return selected[:k]

    def _search(
        self,
        embed_text: str,
        n_fetch: int,
        where_filter: Optional[Dict],
        source_filter: Optional[str],
        k: int,
    ) -> List[Dict]:
        """Embed one query string and return up to k matching chunk dicts."""
        query_embedding = self.embedding_generator.generate_embedding(embed_text)

        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=n_fetch,
            where_filter=where_filter,
        )

        retrieved_docs = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0],
        ):
            if source_filter and source_filter not in metadata.get('source', ''):
                continue

            retrieved_docs.append({
                'text':        doc,
                'source':      metadata.get('source', 'unknown'),
                'chunk_index': metadata.get('chunk_index', 0),
                'similarity':  1 - distance,
                'domain':      metadata.get('domain', 'unknown'),
                'generation':  metadata.get('generation', 'unknown'),
                'spec_number': metadata.get('spec_number', 'unknown'),
                'spec_title':  metadata.get('spec_title', 'unknown'),
            })

            if len(retrieved_docs) >= k:
                break

        return retrieved_docs
    
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
    
    print("\n" + "="*60)
    print("Document Retriever Test")
    print("="*60 + "\n")
    
    # Check if vector store has data
    store = VectorStore()
    stats = store.get_stats()
    
    if stats['total_chunks'] == 0:
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
    print("\n" + "="*60 + "\n")
