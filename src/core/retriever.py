"""
Document retrieval for RAG system
"""
from typing import List, Dict, Optional
import logging
from src.core.embeddings import LocalEmbeddingGenerator
from src.core.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Retrieve relevant documents for queries"""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_generator: Optional[LocalEmbeddingGenerator] = None,
        top_k: int = 5
    ):
        """
        Initialize retriever
        
        Args:
            vector_store: VectorStore instance (creates new if None)
            embedding_generator: EmbeddingGenerator instance (creates new if None)
            top_k: Number of documents to retrieve
        """
        self.vector_store = vector_store or VectorStore()
        self.embedding_generator = embedding_generator or LocalEmbeddingGenerator(model_name="mini")
        self.top_k = top_k
        
        logger.info(f"Initialized DocumentRetriever (top_k={top_k})")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of results (overrides default)
            source_filter: Filter by source document name
            
        Returns:
            List of relevant chunks with scores
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
        """
        Format retrieved documents into context string
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
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
