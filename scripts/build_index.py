"""
Build vector database index from processed chunks
"""
import json
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

#from src.core.embeddings import EmbeddingGenerator
from src.core.vector_store import VectorStore
from src.core.embeddings import LocalEmbeddingGenerator


def main():
    """Build the vector database index"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print(f"\n{'='*60}")
    print("Building Vector Database Index")
    print(f"{'='*60}\n")
    
    # Load processed chunks
    chunks_file = Path("data/processed/chunks.json")
    
    if not chunks_file.exists():
        print(f"Error: {chunks_file} not found")
        print("Please run document processor first:")
        print("  python src/core/document_processor.py")
        sys.exit(1)
    
    print(f"Loading chunks from {chunks_file}...")
    with open(chunks_file, 'r') as f:
        chunks = json.load(f)
    
    print(f"Loaded {len(chunks)} chunks\n")
    
    # Generate embeddings
    print("Step 1: Generating embeddings...")
    print("-" * 60)
    
    generator = LocalEmbeddingGenerator(model_name="bge-small")
    embedded_chunks = generator.embed_chunks(chunks)
    
    print(f"\n✅ Generated {len(embedded_chunks)} embeddings")
    print(f"   Embedding dimensions: {len(embedded_chunks[0]['embedding'])}\n")
    
    # Create vector store and add chunks
    print("Step 2: Building vector database...")
    print("-" * 60)
    
    store = VectorStore()
    
    # Clear existing data (optional - comment out to append)
    # store.clear()
    
    store.add_chunks(embedded_chunks)
    
    # Get stats
    stats = store.get_stats()
    
    print(f"\n{'='*60}")
    print("Index Build Complete!")
    print(f"{'='*60}")
    print(f"Collection: {stats['collection_name']}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Location: {stats['persist_directory']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()