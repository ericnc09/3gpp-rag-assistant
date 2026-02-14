"""
Comprehensive tests for document processor
"""
import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch

# Adjust import based on actual location
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.document_processor import DocumentProcessor, DocumentChunk


class TestDocumentChunk:
    """Test DocumentChunk dataclass"""
    
    def test_chunk_creation(self):
        """Test creating a chunk"""
        metadata = {"source": "test.pdf", "page": 1}
        chunk = DocumentChunk(
            text="This is a test chunk",
            metadata=metadata,
            chunk_id=0
        )
        
        assert chunk.text == "This is a test chunk"
        assert chunk.metadata == metadata
        assert chunk.chunk_id == 0
    
    def test_chunk_to_dict(self):
        """Test converting chunk to dictionary"""
        chunk = DocumentChunk(
            text="Test text",
            metadata={"source": "test.pdf"},
            chunk_id=5
        )
        
        chunk_dict = chunk.to_dict()
        
        assert chunk_dict["text"] == "Test text"
        assert chunk_dict["metadata"]["source"] == "test.pdf"
        assert chunk_dict["chunk_id"] == 5


class TestDocumentProcessor:
    """Test DocumentProcessor class"""
    
    def test_processor_init_defaults(self):
        """Test processor initialization with defaults"""
        processor = DocumentProcessor()
        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 200
        assert processor.min_chunk_size == 100
    
    def test_processor_init_custom(self):
        """Test processor initialization with custom values"""
        processor = DocumentProcessor(
            chunk_size=500,
            chunk_overlap=100,
            min_chunk_size=50
        )
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 100
        assert processor.min_chunk_size == 50
    
    def test_clean_text_whitespace(self):
        """Test cleaning excessive whitespace"""
        processor = DocumentProcessor()
        
        dirty_text = "Hello    world\n\n\n\nThis  is   a    test"
        clean_text = processor.clean_text(dirty_text)
        
        assert "    " not in clean_text
        assert "\n\n\n" not in clean_text
    
    def test_clean_text_special_chars(self):
        """Test cleaning special characters"""
        processor = DocumentProcessor()
        
        dirty_text = "Test™ text© with® special§ chars¶"
        clean_text = processor.clean_text(dirty_text)
        
        # Should keep basic text and punctuation
        assert "Test" in clean_text
        assert "text" in clean_text
        # Should remove special symbols
        assert "™" not in clean_text
        assert "©" not in clean_text
    
    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        processor = DocumentProcessor(
            chunk_size=50,
            chunk_overlap=10,
            min_chunk_size=20
        )
        
        text = "This is a test sentence. " * 10  # ~250 chars
        metadata = {"source": "test.pdf"}
        
        chunks = processor.chunk_text(text, metadata)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.metadata["source"] == "test.pdf" for chunk in chunks)
    
    def test_chunk_text_overlap(self):
        """Test that chunks have correct overlap"""
        processor = DocumentProcessor(
            chunk_size=100,
            chunk_overlap=20
        )
        
        text = "A" * 200  # Simple text for testing
        metadata = {"source": "test.pdf"}
        
        chunks = processor.chunk_text(text, metadata)
        
        # Check overlap exists between chunks
        if len(chunks) >= 2:
            # Last part of chunk 0 should overlap with first part of chunk 1
            chunk0_end = chunks[0].text[-20:]
            chunk1_start = chunks[1].text[:20]
            
            # There should be some similarity due to overlap
            assert len(chunk0_end) > 0
            assert len(chunk1_start) > 0
    
    def test_chunk_text_metadata(self):
        """Test that chunk metadata is properly set"""
        processor = DocumentProcessor()
        
        text = "Test text. " * 200  # ~2000 chars
        metadata = {"source": "test.pdf", "title": "Test Document"}
        
        chunks = processor.chunk_text(text, metadata)
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == i
            assert chunk.metadata["source"] == "test.pdf"
            assert chunk.metadata["title"] == "Test Document"
            assert chunk.metadata["chunk_index"] == i
            assert "start_char" in chunk.metadata
            assert "end_char" in chunk.metadata
    
    def test_chunk_text_min_size(self):
        """Test that chunks below minimum size are filtered out"""
        processor = DocumentProcessor(
            chunk_size=100,
            min_chunk_size=50
        )
        
        text = "Short text only 30 chars long"
        metadata = {"source": "test.pdf"}
        
        chunks = processor.chunk_text(text, metadata)
        
        # Should not create chunk if below minimum
        assert len(chunks) == 0
    
    def test_save_chunks(self):
        """Test saving chunks to JSON file"""
        processor = DocumentProcessor()
        
        chunks = [
            DocumentChunk(
                text="Test chunk 1",
                metadata={"source": "test.pdf"},
                chunk_id=0
            ),
            DocumentChunk(
                text="Test chunk 2",
                metadata={"source": "test.pdf"},
                chunk_id=1
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_chunks.json"
            processor.save_chunks(chunks, output_path)
            
            assert output_path.exists()
            
            # Load and verify
            with open(output_path, 'r') as f:
                loaded_chunks = json.load(f)
            
            assert len(loaded_chunks) == 2
            assert loaded_chunks[0]["text"] == "Test chunk 1"
            assert loaded_chunks[1]["chunk_id"] == 1


class TestDocumentProcessorPDF:
    """Test PDF-specific functionality"""
    
    @patch('core.document_processor.PdfReader')
    def test_load_pdf_success(self, mock_pdf_reader):
        """Test successful PDF loading"""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test page content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_instance.metadata = {
            "/Title": "Test PDF",
            "/Author": "Test Author"
        }
        
        mock_pdf_reader.return_value = mock_reader_instance
        
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            text, metadata = processor.load_pdf(tmp_path)
            
            assert "Test page content" in text
            assert metadata["title"] == "Test PDF"
            assert metadata["author"] == "Test Author"
            assert metadata["num_pages"] == 1
        finally:
            tmp_path.unlink()
    
    def test_load_pdf_file_not_found(self):
        """Test error when PDF file doesn't exist"""
        processor = DocumentProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.load_pdf(Path("nonexistent.pdf"))
    
    @patch('core.document_processor.PdfReader')
    def test_process_pdf(self, mock_pdf_reader):
        """Test complete PDF processing pipeline"""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content. " * 100  # Enough for multiple chunks
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_reader_instance.metadata = None
        
        mock_pdf_reader.return_value = mock_reader_instance
        
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            chunks = processor.process_pdf(tmp_path)
            
            assert len(chunks) > 0
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        finally:
            tmp_path.unlink()


class TestDocumentProcessorIntegration:
    """Integration tests requiring actual files"""
    
    def test_process_directory_empty(self):
        """Test processing empty directory"""
        processor = DocumentProcessor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            chunks = processor.process_directory(Path(tmpdir))
            assert chunks == []
    
    def test_process_directory_not_found(self):
        """Test error when directory doesn't exist"""
        processor = DocumentProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.process_directory(Path("nonexistent_dir"))


# Fixtures for test data
@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return """
    This is a sample document for testing.
    It contains multiple sentences.
    Each sentence adds to the total length.
    We need enough text to create multiple chunks.
    This helps test the chunking functionality.
    More text means more thorough testing.
    Additional sentences ensure proper coverage.
    The document processor should handle this well.
    """ * 5


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        "source": "test_document.pdf",
        "title": "Test Document",
        "num_pages": 10
    }


def test_end_to_end_with_fixtures(sample_text, sample_metadata):
    """End-to-end test using fixtures"""
    processor = DocumentProcessor(chunk_size=200, chunk_overlap=50)
    
    chunks = processor.chunk_text(sample_text, sample_metadata)
    
    assert len(chunks) > 0
    assert all(chunk.metadata["source"] == "test_document.pdf" for chunk in chunks)
    assert all(len(chunk.text) >= processor.min_chunk_size for chunk in chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
