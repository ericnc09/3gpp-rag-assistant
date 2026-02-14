"""
Document processing module for parsing and chunking 3GPP PDFs

This module handles:
- PDF text extraction
- Text cleaning and preprocessing
- Intelligent chunking with overlap
- Metadata extraction
"""

from pathlib import Path
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass
import re

try:
    from pypdf import PdfReader
except ImportError:
    print("Warning: pypdf not installed. Run: pip install pypdf")
    PdfReader = None

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document"""
    text: str
    metadata: Dict
    chunk_id: int
    
    def to_dict(self) -> Dict:
        """Convert chunk to dictionary format"""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id
        }


class DocumentProcessor:
    """Process 3GPP PDF documents into chunks for RAG"""
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """
        Initialize document processor
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size for a valid chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        if not PdfReader:
            raise ImportError("pypdf is required. Install with: pip install pypdf")
    
    def load_pdf(self, file_path: Path) -> tuple[str, Dict]:
        """
        Load and extract text from a PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        logger.info(f"Loading PDF: {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            reader = PdfReader(str(file_path))
            
            # Extract metadata
            metadata = {
                "source": str(file_path.name),
                "num_pages": len(reader.pages),
                "file_path": str(file_path)
            }
            
            # Try to get PDF metadata
            if reader.metadata:
                metadata.update({
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", "")
                })
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        # Add page number marker
                        text_parts.append(f"\n[Page {page_num}]\n{page_text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    continue
            
            full_text = "\n".join(text_parts)
            
            logger.info(f"Extracted {len(full_text)} characters from {len(reader.pages)} pages")
            
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers patterns (common in 3GPP specs)
        text = re.sub(r'\n\d+\s+3GPP.*?\n', '\n', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:()\[\]\-/\n]', '', text)
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: Dict) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full document text
            metadata: Document metadata
            
        Returns:
            List of DocumentChunk objects
        """
        # Clean the text first
        text = self.clean_text(text)
        
        chunks = []
        chunk_id = 0
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                search_start = max(start, end - 100)
                search_text = text[search_start:end + 100]
                
                # Find the last sentence ending
                sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', search_text)]
                
                if sentence_endings:
                    # Adjust end to the sentence boundary
                    last_sentence = sentence_endings[-1]
                    end = search_start + last_sentence
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            # Only create chunk if it meets minimum size
            if len(chunk_text) >= self.min_chunk_size:
                # Create chunk metadata
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": chunk_id,
                    "start_char": start,
                    "end_char": end,
                    "chunk_size": len(chunk_text)
                })
                
                chunk = DocumentChunk(
                    text=chunk_text,
                    metadata=chunk_metadata,
                    chunk_id=chunk_id
                )
                chunks.append(chunk)
                chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start <= 0:
                start = 1
        
        logger.info(f"Created {len(chunks)} chunks from document")
        
        return chunks
    
    def process_pdf(self, file_path: Path) -> List[DocumentChunk]:
        """
        Complete pipeline: Load PDF → Extract text → Create chunks
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of document chunks ready for embedding
        """
        # Load PDF
        text, metadata = self.load_pdf(file_path)
        
        # Create chunks
        chunks = self.chunk_text(text, metadata)
        
        return chunks
    
    def process_directory(self, directory: Path) -> List[DocumentChunk]:
        """
        Process all PDFs in a directory
        
        Args:
            directory: Path to directory containing PDFs
            
        Returns:
            List of all chunks from all documents
        """
        logger.info(f"Processing directory: {directory}")
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find all PDF files
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        all_chunks = []
        for pdf_file in pdf_files:
            try:
                chunks = self.process_pdf(pdf_file)
                all_chunks.extend(chunks)
                logger.info(f"Processed {pdf_file.name}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Error processing {pdf_file.name}: {e}")
                continue
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        
        return all_chunks
    
    def save_chunks(self, chunks: List[DocumentChunk], output_path: Path) -> None:
        """
        Save chunks to JSON file
        
        Args:
            chunks: List of document chunks
            output_path: Path to save JSON file
        """
        import json
        
        chunks_dict = [chunk.to_dict() for chunk in chunks]
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_path}")


def main():
    """Example usage of DocumentProcessor"""
    import sys
    from pathlib import Path
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize processor
    processor = DocumentProcessor(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Process documents
    data_dir = Path("data/raw")
    
    if not data_dir.exists():
        print(f"Error: Directory {data_dir} does not exist")
        print("Please create it and add your 3GPP PDF files")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("3GPP Document Processor")
    print(f"{'='*60}\n")
    
    try:
        # Process all PDFs
        chunks = processor.process_directory(data_dir)
        
        if not chunks:
            print("\nNo documents were processed. Please add PDF files to data/raw/")
            sys.exit(1)
        
        # Save processed chunks
        output_file = Path("data/processed/chunks.json")
        processor.save_chunks(chunks, output_file)
        
        # Print summary
        print(f"\n{'='*60}")
        print("Processing Summary:")
        print(f"{'='*60}")
        print(f"Total chunks created: {len(chunks)}")
        print(f"Output saved to: {output_file}")
        
        # Show sample chunk
        if chunks:
            print(f"\nSample chunk:")
            print(f"  Source: {chunks[0].metadata['source']}")
            print(f"  Chunk size: {len(chunks[0].text)} characters")
            print(f"  Preview: {chunks[0].text[:200]}...")
        
        print(f"\n{'='*60}")
        print("✅ Processing complete!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
