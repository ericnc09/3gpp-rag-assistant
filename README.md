# 3GPP Technical Specification RAG Assistant 🚀

An AI-powered Retrieval-Augmented Generation (RAG) system that makes navigating 3GPP technical specifications effortless. Ask questions in natural language and get accurate, cited answers from 5G/LTE documentation.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 Project Overview

During my work on 5G network deployments at Rogers Communications, I noticed engineers spending hours searching through 3GPP specifications. This RAG system automates that process using:

- **Vector embeddings** for semantic search across technical documents
- **Large Language Models** for natural language understanding
- **Citation tracking** to ensure answer accuracy and traceability
- **Production-ready architecture** with FastAPI backend and monitoring

## ✨ Features

- 🔍 **Semantic Search**: Find relevant information across 1000+ pages of specs using local embeddings
- 💬 **Natural Language Queries**: Ask questions like "What is the gNB architecture?"
- 📚 **Citation Tracking**: Every answer includes source document references
- 💰 **No API Costs**: Fully local embeddings - no external API dependencies or costs
- 🔄 **Conversation Memory**: Multi-turn conversations with context retention
- 📊 **Analytics Dashboard**: Query patterns, performance metrics, and usage stats
- 🚀 **Open Source Models**: Built entirely on open source embedding models (sentence-transformers)

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  FastAPI     │─────▶│  Vector DB  │
│  (Streamlit)│      │   Backend    │      │  (Chroma)   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Local LLM    │
                     │ (Open Source)│
                     └──────────────┘
```

**Embeddings**: Local models (sentence-transformers) - no API required ✨

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- (Optional) CUDA/GPU for faster embedding generation

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/3gpp-rag-assistant.git
cd 3gpp-rag-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up environment variables for advanced configuration
cp .env.example .env
```

**Note**: No API keys required! All embeddings are generated locally using open source models.

### Running the Application

```bash
# 1. Download and process 3GPP specifications
python src/core/document_processor.py

# 2. Start the FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# 3. Launch the Streamlit frontend (in a new terminal)
streamlit run src/frontend/app.py
```

Visit `http://localhost:8501` to start asking questions!

## 📖 Example Queries

Try asking:
- "What is the difference between SA and NSA 5G deployment?"
- "Explain the NG-RAN architecture"
- "What are the key features of NR physical layer?"
- "How does handover work in 5G networks?"

## 📁 Project Structure

```
3gpp-rag-assistant/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # API endpoints
│   │   └── models.py     # Pydantic schemas
│   ├── core/             # Core RAG logic
│   │   ├── embeddings.py # Vector embedding generation
│   │   ├── retriever.py  # Document retrieval
│   │   ├── llm.py        # LLM interaction
│   │   └── document_processor.py  # PDF parsing
│   ├── utils/            # Utility functions
│   │   ├── logger.py     # Logging configuration
│   │   └── metrics.py    # Cost and performance tracking
│   └── frontend/         # Streamlit UI
│       └── app.py
├── data/
│   ├── raw/              # Original 3GPP PDFs
│   └── processed/        # Parsed and chunked documents
├── tests/                # Unit and integration tests
├── notebooks/            # Jupyter notebooks for exploration
├── docs/                 # Additional documentation
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md
```

## 🔧 Configuration

Key configuration options in `.env`:

```env
# Embedding Configuration (Local Models - No API Key Needed!)
# Options: "mini" (fast), "mpnet" (better), "bge-small" (technical docs), "bge-base" (best quality)
EMBEDDING_MODEL=mini

# Vector Database
VECTOR_DB_PATH=./data/vectordb
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# API Configuration
API_PORT=8000
LOG_LEVEL=INFO
```

### Available Embedding Models

All models are **completely free** and run locally:

| Model | Size | Dimensions | Speed | Best For |
|-------|------|-----------|-------|----------|
| `mini` | 80MB | 384 | ⚡ Fast | Quick prototyping |
| `mpnet` | 420MB | 768 | 🔄 Medium | Balanced performance |
| `bge-small` | 130MB | 384 | ⚡ Fast | Technical documents |
| `bge-base` | 440MB | 768 | 🚀 Best | Maximum accuracy |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_retriever.py
```

## 📊 Performance Metrics

Current benchmarks (based on 3GPP TS 38.300 with all-MiniLM-L6-v2 model):
- **Average query time**: ~1.5-2s (CPU), <0.5s (GPU)
- **Retrieval accuracy**: 90%+ (top-5 chunks contain answer)
- **Cost per query**: **Free** (completely local) 🎉
- **Document processing**: ~50-100 PDFs/minute (CPU)
- **Memory footprint**: ~200MB (model + overhead)

## 🛣️ Roadmap

- [ ] Phase 1: Core RAG functionality with 3GPP specs ✅
- [ ] Phase 2: Add evaluation metrics (answer quality scoring)
- [ ] Phase 3: Support for multiple document formats (Word, HTML)
- [ ] Phase 4: Fine-tune embedding model on telecom domain
- [ ] Phase 5: Deploy to cloud (AWS/GCP)
- [ ] Phase 6: Multi-user authentication and query history

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **3GPP** for providing open access to technical specifications
- **Sentence Transformers** for excellent open source embedding models
- **Hugging Face** for model hosting and community
- **LangChain** community for RAG best practices
- **Rogers Communications** for inspiring this project
- Open source community for making AI accessible to everyone 💙

## 📧 Contact

**Eric Costa**  
Email: ericcosta.public@gmail.com  
LinkedIn: [linkedin.com/in/niloyericcosta](https://linkedin.com/in/niloyericcosta)

---

**Note**: This is a portfolio project demonstrating AI product engineering skills. It is not affiliated with or endorsed by 3GPP or Rogers Communications.
