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

from src.core.embeddings import LocalEmbeddingGenerator
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
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None,
    ) -> List[Dict]:
        """Retrieve the most semantically similar chunks for a query.

        Args:
            query: Natural language question or search string.
            top_k: Override the default number of results for this call.
            source_filter: If set, only return chunks whose source filename
                contains this string (e.g. "38401" to limit to TS 38.401).
                Extra results are fetched internally to compensate for
                filtered-out items.

        Returns:
            List of chunk dicts, each with keys:
                - text        (str)   : chunk content
                - source      (str)   : filename of the source document
                - chunk_index (int)   : position of the chunk in its document
                - similarity  (float) : cosine similarity in [0, 1]
            Sorted descending by similarity, length <= top_k.
        """
        k = top_k or self.top_k
        
        logger.info(f"Retrieving documents for query: '{query[:50]}...'")
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Search vector store (get extra for filtering)
        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=k * 2 if source_filter else k
        )
        
        # Format results
        retrieved_docs = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            # Apply source filter if specified
            if source_filter and source_filter not in metadata.get('source', ''):
                continue
            
            # Calculate similarity score (1 - distance)
            similarity = 1 - distance
            
            retrieved_docs.append({
                'text': doc,
                'source': metadata.get('source', 'unknown'),
                'chunk_index': metadata.get('chunk_index', 0),
                'similarity': similarity
            })
            
            if len(retrieved_docs) >= k:
                break
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        
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
            context_parts.append(
                f"[Document {i}] (Source: {doc['source']}, Similarity: {doc['similarity']:.3f})\n"
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
