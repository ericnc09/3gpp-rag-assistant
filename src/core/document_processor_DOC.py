"""
Document processing module for legacy .doc files (Microsoft Word 97-2003)

This module handles:
- Legacy .doc file text extraction
- Multiple extraction methods (antiword, textract, win32com)
- Text cleaning and preprocessing
- Intelligent chunking with overlap
- Metadata extraction

Note: .doc is an older binary format. For best results, convert to .docx.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
import re
import sys
import subprocess
import tempfile

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


class LegacyDocProcessor:
    """Process legacy .doc files (Microsoft Word 97-2003) into chunks for RAG"""
    
    def __init__(
        self, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
        extraction_method: str = "auto"
    ):
        """
        Initialize legacy doc processor
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size for a valid chunk
            extraction_method: Method to extract text ('auto', 'antiword', 'textract', 'win32com', 'libreoffice')
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.extraction_method = extraction_method
        
        # Detect available extraction methods
        self.available_methods = self._detect_available_methods()
        logger.info(f"Available extraction methods: {self.available_methods}")
    
    def _detect_available_methods(self) -> List[str]:
        """Detect which extraction methods are available on the system"""
        methods = []
        
        # Check for antiword (Linux/Mac)
        try:
            subprocess.run(['antiword', '-v'], capture_output=True, check=True)
            methods.append('antiword')
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check for textract (Python library)
        try:
            import textract
            methods.append('textract')
        except ImportError:
            pass
        
        # Check for win32com (Windows only)
        if sys.platform == 'win32':
            try:
                import win32com.client
                methods.append('win32com')
            except ImportError:
                pass
        
        # Check for LibreOffice/OpenOffice
        libreoffice_bins = ['libreoffice', 'soffice', 'openoffice']
        for bin_name in libreoffice_bins:
            try:
                subprocess.run([bin_name, '--version'], capture_output=True, check=True)
                methods.append('libreoffice')
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return methods
    
    def _extract_with_antiword(self, file_path: Path) -> Tuple[str, Dict]:
        """
        Extract text using antiword (Linux/Mac)
        
        Best quality for Linux/Mac systems
        Install: sudo apt-get install antiword (Ubuntu) or brew install antiword (Mac)
        """
        logger.info(f"Extracting with antiword: {file_path}")
        
        try:
            result = subprocess.run(
                ['antiword', str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            text = result.stdout
            
            metadata = {
                "source": str(file_path.name),
                "file_path": str(file_path),
                "format": "doc (legacy)",
                "extraction_method": "antiword"
            }
            
            logger.info(f"Extracted {len(text)} characters using antiword")
            return text, metadata
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"antiword extraction failed: {e.stderr}")
    
    def _extract_with_textract(self, file_path: Path) -> Tuple[str, Dict]:
        """
        Extract text using textract library
        
        Cross-platform solution, moderate quality
        Install: pip install textract
        """
        logger.info(f"Extracting with textract: {file_path}")
        
        try:
            import textract
            text_bytes = textract.process(str(file_path))
            text = text_bytes.decode('utf-8', errors='ignore')
            
            metadata = {
                "source": str(file_path.name),
                "file_path": str(file_path),
                "format": "doc (legacy)",
                "extraction_method": "textract"
            }
            
            logger.info(f"Extracted {len(text)} characters using textract")
            return text, metadata
            
        except Exception as e:
            raise RuntimeError(f"textract extraction failed: {e}")
    
    def _extract_with_win32com(self, file_path: Path) -> Tuple[str, Dict]:
        """
        Extract text using win32com (Windows with MS Word installed)
        
        Highest quality on Windows, requires MS Word
        Install: pip install pywin32
        """
        logger.info(f"Extracting with win32com: {file_path}")
        
        try:
            import win32com.client
            
            # Start Word application
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            try:
                # Open document
                doc = word.Documents.Open(str(file_path.resolve()))
                
                # Extract text
                text = doc.Content.Text
                
                # Extract metadata
                metadata = {
                    "source": str(file_path.name),
                    "file_path": str(file_path),
                    "format": "doc (legacy)",
                    "extraction_method": "win32com",
                    "title": doc.BuiltInDocumentProperties("Title").Value or "",
                    "author": doc.BuiltInDocumentProperties("Author").Value or "",
                    "subject": doc.BuiltInDocumentProperties("Subject").Value or "",
                }
                
                # Close document
                doc.Close(False)
                
                logger.info(f"Extracted {len(text)} characters using win32com")
                return text, metadata
                
            finally:
                # Always quit Word
                word.Quit()
                
        except Exception as e:
            raise RuntimeError(f"win32com extraction failed: {e}")
    
    def _extract_with_libreoffice(self, file_path: Path) -> Tuple[str, Dict]:
        """
        Extract text using LibreOffice/OpenOffice conversion
        
        Cross-platform, good quality
        Requires LibreOffice or OpenOffice installed
        """
        logger.info(f"Extracting with LibreOffice: {file_path}")
        
        # Find LibreOffice binary
        libreoffice_bin = None
        for bin_name in ['libreoffice', 'soffice', 'openoffice']:
            try:
                subprocess.run([bin_name, '--version'], capture_output=True, check=True)
                libreoffice_bin = bin_name
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        if not libreoffice_bin:
            raise RuntimeError("LibreOffice not found")
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Convert .doc to .txt
                subprocess.run(
                    [
                        libreoffice_bin,
                        '--headless',
                        '--convert-to', 'txt:Text',
                        '--outdir', tmpdir,
                        str(file_path)
                    ],
                    capture_output=True,
                    check=True
                )
                
                # Read the converted text file
                txt_file = Path(tmpdir) / (file_path.stem + '.txt')
                
                if not txt_file.exists():
                    raise RuntimeError("Conversion produced no output file")
                
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                
                metadata = {
                    "source": str(file_path.name),
                    "file_path": str(file_path),
                    "format": "doc (legacy)",
                    "extraction_method": "libreoffice"
                }
                
                logger.info(f"Extracted {len(text)} characters using LibreOffice")
                return text, metadata
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LibreOffice conversion failed: {e.stderr}")
    
    def load_doc(self, file_path: Path) -> Tuple[str, Dict]:
        """
        Load and extract text from a legacy .doc file
        
        Tries multiple extraction methods in order of quality
        
        Args:
            file_path: Path to the .doc file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        if file_path.suffix.lower() != '.doc':
            raise ValueError(f"Expected .doc file, got {file_path.suffix}")
        
        # Determine which method to use
        if self.extraction_method == "auto":
            # Try methods in order of preference
            if sys.platform == 'win32' and 'win32com' in self.available_methods:
                method = 'win32com'
            elif 'antiword' in self.available_methods:
                method = 'antiword'
            elif 'textract' in self.available_methods:
                method = 'textract'
            elif 'libreoffice' in self.available_methods:
                method = 'libreoffice'
            else:
                self._print_installation_help()
                raise RuntimeError("No extraction method available. See installation instructions above.")
        else:
            method = self.extraction_method
            if method not in self.available_methods:
                raise RuntimeError(f"Requested method '{method}' is not available")
        
        # Extract using selected method
        if method == 'antiword':
            return self._extract_with_antiword(file_path)
        elif method == 'textract':
            return self._extract_with_textract(file_path)
        elif method == 'win32com':
            return self._extract_with_win32com(file_path)
        elif method == 'libreoffice':
            return self._extract_with_libreoffice(file_path)
        else:
            raise RuntimeError(f"Unknown extraction method: {method}")
    
    def _print_installation_help(self):
        """Print helpful installation instructions"""
        print("\n" + "="*60)
        print("❌ No .doc extraction method available!")
        print("="*60)
        print("\nPlease install one of the following:\n")
        
        print("Option 1: antiword (Linux/Mac - Recommended)")
        print("  Ubuntu/Debian: sudo apt-get install antiword")
        print("  macOS:         brew install antiword")
        print()
        
        print("Option 2: textract (Cross-platform)")
        print("  pip install textract")
        print("  Note: May require system dependencies")
        print()
        
        print("Option 3: pywin32 (Windows only - Best quality)")
        print("  pip install pywin32")
        print("  Requires: Microsoft Word installed")
        print()
        
        print("Option 4: LibreOffice (Cross-platform)")
        print("  Download from: https://www.libreoffice.org/download/")
        print()
        
        print("Alternative: Convert .doc to .docx manually")
        print("  1. Open .doc file in Microsoft Word")
        print("  2. File → Save As → Choose .docx format")
        print("  3. Use the .docx processor instead")
        print("="*60 + "\n")
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw text from document
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove page numbers and headers/footers
        text = re.sub(r'\n\d+\s+3GPP.*?\n', '\n', text)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove special Unicode characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:()\[\]\-/\n#|]', '', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
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
    
    def process_document(self, file_path: Path) -> List[DocumentChunk]:
        """
        Complete pipeline: Load .doc → Extract text → Create chunks
        
        Args:
            file_path: Path to .doc file
            
        Returns:
            List of document chunks ready for embedding
        """
        # Load document
        text, metadata = self.load_doc(file_path)
        
        # Create chunks
        chunks = self.chunk_text(text, metadata)
        
        return chunks
    
    def process_directory(self, directory: Path) -> List[DocumentChunk]:
        """
        Process all .doc files in a directory
        
        Args:
            directory: Path to directory containing .doc files
            
        Returns:
            List of all chunks from all documents
        """
        logger.info(f"Processing directory: {directory}")
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Find all .doc files
        doc_files = list(directory.glob("*.doc"))
        
        # Filter out .docx files (they have .doc in the name but are different)
        doc_files = [f for f in doc_files if f.suffix.lower() == '.doc']
        
        if not doc_files:
            logger.warning(f"No .doc files found in {directory}")
            return []
        
        logger.info(f"Found {len(doc_files)} .doc files")
        
        all_chunks = []
        failed_files = []
        
        for doc_file in doc_files:
            try:
                chunks = self.process_document(doc_file)
                all_chunks.extend(chunks)
                logger.info(f"✅ Processed {doc_file.name}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"❌ Error processing {doc_file.name}: {e}")
                failed_files.append(doc_file.name)
                continue
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files: {', '.join(failed_files)}")
        
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
    """Example usage of LegacyDocProcessor"""
    from pathlib import Path
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print(f"\n{'='*60}")
    print("3GPP Legacy .doc Document Processor")
    print(f"{'='*60}\n")
    
    # Initialize processor
    processor = LegacyDocProcessor(
        chunk_size=1000,
        chunk_overlap=200,
        extraction_method="auto"  # Auto-detect best method
    )
    
    # Show available methods
    print("Available extraction methods:")
    for method in processor.available_methods:
        print(f"  ✅ {method}")
    
    if not processor.available_methods:
        print("  ❌ No extraction methods available")
        processor._print_installation_help()
        sys.exit(1)
    
    print()
    
    # Process documents
    data_dir = Path("data/raw")
    
    if not data_dir.exists():
        print(f"Error: Directory {data_dir} does not exist")
        print("Please create it and add your .doc files")
        sys.exit(1)
    
    try:
        # Process all .doc files
        chunks = processor.process_directory(data_dir)
        
        if not chunks:
            print("\nNo .doc files were processed.")
            print("Make sure you have .doc files (not .docx) in data/raw/")
            sys.exit(1)
        
        # Save processed chunks
        output_file = Path("data/processed/chunks_doc.json")
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
            print(f"  Extraction method: {chunks[0].metadata['extraction_method']}")
            print(f"  Chunk size: {len(chunks[0].text)} characters")
            print(f"  Preview: {chunks[0].text[:200]}...")
        
        # Show statistics
        sources = set(chunk.metadata['source'] for chunk in chunks)
        print(f"\nProcessed documents:")
        for source in sorted(sources):
            source_chunks = [c for c in chunks if c.metadata['source'] == source]
            method = source_chunks[0].metadata['extraction_method']
            print(f"  - {source}: {len(source_chunks)} chunks (via {method})")
        
        print(f"\n{'='*60}")
        print("✅ Processing complete!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
