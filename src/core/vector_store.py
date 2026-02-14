"""
Vector database operations using ChromaDB
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Manage vector database operations with ChromaDB"""
    
    def __init__(
        self,
        persist_directory: str = "data/vectordb",
        collection_name: str = "3gpp_specs"
    ):
        """
        Initialize vector store
        
        Args:
            persist_directory: Directory to store the database
            collection_name: Name of the collection
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "3GPP technical specifications"}
        )
        
        logger.info(f"Initialized VectorStore: {collection_name}")
        logger.info(f"Persist directory: {self.persist_directory}")
    
    def add_chunks(self, chunks: List[Dict]) -> None:
        """
        Add chunks with embeddings to the vector store
        
        Args:
            chunks: List of chunks with 'text', 'embedding', and 'metadata' fields
        """
        logger.info(f"Adding {len(chunks)} chunks to vector store")
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Generate unique ID
            #chunk_id = f"chunk_{chunk.get('chunk_id', i)}"
            #ids.append(chunk_id)
            chunk_id = f"id_{i}" 
            ids.append(chunk_id)
            # Add embedding
            embeddings.append(chunk['embedding'])
            
            # Add document text
            documents.append(chunk['text'])
            
            # Add metadata (ChromaDB requires dict, not nested dicts)
            metadata = {
                "source": chunk['metadata'].get('source', 'unknown'),
                "chunk_index": chunk['metadata'].get('chunk_index', i),
                "chunk_size": chunk['metadata'].get('chunk_size', len(chunk['text']))
            }
            metadatas.append(metadata)
        
        # Add to collection in batches (ChromaDB has limits)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            
            self.collection.add(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )
            
            logger.info(f"Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
        
        logger.info(f"Successfully added {len(chunks)} chunks")
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5
    ) -> Dict:
        """
        Query the vector store
        
        Args:
            query_embedding: Embedding vector of the query
            n_results: Number of results to return
            
        Returns:
            Dictionary with 'documents', 'metadatas', and 'distances'
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        count = self.collection.count()
        
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "persist_directory": str(self.persist_directory)
        }
    
    def clear(self) -> None:
        """Clear all data from the collection"""
        logger.warning("Clearing all data from vector store")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name
        )


if __name__ == "__main__":
    # Test the vector store
    logging.basicConfig(level=logging.INFO)
    
    # Initialize
    store = VectorStore()
    
    # Get stats
    stats = store.get_stats()
    print("\nVector Store Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")