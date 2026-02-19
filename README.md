# 3GPP Technical Specification RAG Assistant 🚀

Supported by Claude Code, this is an AI-powered Retrieval-Augmented Generation (RAG) system that makes navigating 3GPP technical specifications effortless. Ask questions in natural language and get accurate, cited answers from 5G/LTE documentation — **completely free, fully local, no API keys required.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-152%20passing-brightgreen.svg)](#testing)

---

## Table of Contents

1. [Project Overview](#-project-overview)
2. [Problem Statement & Research](#-problem-statement--research)
3. [User Stories](#-user-stories)
4. [Architecture](#-architecture)
5. [Features](#-features)
6. [Quick Start](#-quick-start)
7. [Configuration](#-configuration)
8. [Project Structure](#-project-structure)
9. [Testing](#-testing)
10. [Performance Metrics](#-performance-metrics)
11. [Product Development Roadmap](#-product-development-roadmap)
12. [Deployment](#-deployment)
13. [Contributing](#-contributing)
14. [License](#-license)
14. [Contact](#-contact)

---

## 🎯 Project Overview

During my work on 5G network deployments at Rogers Communications, I noticed engineers spending hours manually searching through 3GPP specifications to answer basic architecture questions. A single query could mean skimming through hundreds of pages across multiple documents. Traditional searches often lead to answers which are not valid - old blog posts etc. I wanted to build a system which can provide converasational answers. Almost everything we built is based on open-source systems, we do stand on the shoulder of giants to make it possible!

This RAG system automates that process using:

- **Local vector embeddings** for semantic search across thousands of spec pages
- **Open-source LLMs via Ollama** for natural language answer generation
- **Citation tracking** to ensure every answer is grounded in the source documents
- **Zero API costs** — the entire pipeline runs on your machine

---

## 🔬 Problem Statement & Research

### The Problem

3GPP specifications are the authoritative reference for all cellular standards (4G LTE, 5G NR, 6G). Engineers, researchers, and standards professionals must constantly reference these documents to:

- Understand protocol architecture and interfaces
- Verify compliance requirements
- Resolve implementation ambiguities
- Onboard new team members to complex standards

**Pain points identified:**

| Problem | Impact |
|---|---|
| Documents are hundreds to thousands of pages each | Hours lost per query |
| Terminology is dense and highly specialized | Steep learning curve for new engineers |
| Answers often span multiple documents (e.g. TS 38.300 + 38.401) | Manual cross-referencing required |
| No semantic search — only keyword/text search in PDFs | Low recall on conceptual questions |
| No conversational interface | Each query starts from scratch |

### Research Findings

**Domain:** 3GPP releases thousands of technical specifications. The most critical for 5G NR include:

| Spec | Title | Relevance |
|---|---|---|
| TS 38.300 | NR Overall Description | Core NR architecture |
| TS 38.401 | NG-RAN Architecture Description | RAN architecture & interfaces |
| TS 38.104 | NR Base Station Radio Transmission | RF requirements |
| TS 23.501 | 5G System Architecture | Core network architecture |
| TS 38.211–38.215 | NR Physical Layer | Physical layer specs |

**RAG vs. Fine-tuning for this domain:**

RAG was chosen over fine-tuning for the following reasons:

- Specs are updated every 3GPP release cycle — RAG allows instant updates by re-indexing
- Fine-tuning requires labelled Q&A pairs which don't exist publicly for 3GPP
- RAG provides citations — critical for standards work where traceability matters
- RAG works well on highly structured technical text with consistent terminology

**Embedding model selection research:**

| Model | Dim | Size | Technical Doc Perf | Decision |
|---|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | 80MB | Good | Baseline |
| `all-mpnet-base-v2` | 768 | 420MB | Better | Evaluated |
| `BAAI/bge-small-en-v1.5` | 384 | 130MB | Best small | **Selected** |
| `BAAI/bge-base-en-v1.5` | 768 | 440MB | Best overall | Recommended for prod |

BGE (BAAI General Embeddings) models consistently outperform others on technical/scientific text retrieval benchmarks (MTEB leaderboard). The `bge-small` model offers the best accuracy-to-size ratio for this use case.

**LLM selection research:**

All models run locally via [Ollama](https://ollama.com):

| Model | Size | Strengths | Notes |
|---|---|---|---|
| `llama3.2` | 2GB | General purpose, instruction-following | Default — best balance |
| `mistral` | 4GB | Strong on technical text | Good alternative |
| `phi3` | 2.2GB | Fast, efficient | Good for constrained hardware |
| `deepseek-r1` | 4.7GB | Reasoning tasks | Best for complex queries |

**Chunking strategy research:**

- Chunk size: **1000 characters** with **200 character overlap**
- Sentence-boundary aware splitting to avoid mid-sentence cuts
- 3GPP-specific header/footer stripping (removes page numbers, revision markers)
- Tables extracted and included as structured text rows

---

## 👤 User Stories

### Primary Users

#### 1. Telecom Engineer (Core User)

> *"As a 5G RAN engineer, I want to ask natural language questions about 3GPP specs and get cited answers, so that I can resolve implementation questions in minutes instead of hours."*

**Acceptance Criteria:**
- [ ] Can ask a question in plain English about 5G/NR/LTE
- [ ] Receives an answer with specific source document citations
- [ ] Answer is generated in under 5 seconds on standard hardware
- [ ] Can follow up with clarifying questions in the same session
- [ ] Can filter queries to a specific specification document

---

#### 2. Standards Researcher

> *"As a telecom researcher, I want to search across multiple 3GPP releases simultaneously, so that I can track how a feature has evolved across specification versions."*

**Acceptance Criteria:**
- [ ] Can query across all indexed documents at once
- [ ] Can filter results to a specific spec version or document
- [ ] Source citations include document name and approximate location
- [ ] Can export answers and sources for documentation purposes

---

#### 3. New Engineer Onboarding

> *"As a new team member, I want a conversational interface to ask 'dumb questions' about 5G architecture without bothering senior engineers, so that I can learn faster and independently."*

**Acceptance Criteria:**
- [ ] Conversational multi-turn interface (remembers context of prior questions)
- [ ] Answers are technically accurate but explained clearly
- [ ] System gracefully handles questions outside the indexed documents
- [ ] Interactive CLI or web UI available

---

#### 4. Technical Writer / Documentation Team

> *"As a technical writer, I want to quickly find authoritative spec text for a given feature, so that I can write accurate documentation with proper 3GPP references."*

**Acceptance Criteria:**
- [ ] Returns verbatim or near-verbatim spec excerpts
- [ ] Clearly identifies which document and section the text comes from
- [ ] Can retrieve multiple relevant passages for a single topic

---

### Secondary Users

#### 5. DevOps / Platform Engineer

> *"As a DevOps engineer, I want performance metrics and health endpoints, so that I can monitor the RAG system in production."*

**Acceptance Criteria:**
- [ ] `/health` endpoint returns system status
- [ ] Per-query timing metrics (retrieve time, generate time)
- [ ] Metrics persisted and exportable as JSON
- [ ] Structured logging with configurable log level

---

#### 6. Telecom Student / Academic

> *"As a grad student studying 5G, I want free access to a spec assistant that doesn't require expensive API subscriptions, so that I can use it for my research without cost barriers."*

**Acceptance Criteria:**
- [ ] Fully local — no API keys or cloud services required
- [ ] Works offline once models are downloaded
- [ ] Clear setup documentation for non-DevOps users
- [ ] Open source and self-hostable

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                             │
│            (CLI / Streamlit UI / REST API)              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   RAG Chain                             │
│              src/core/rag_chain.py                      │
│   • Conversation history (multi-turn)                   │
│   • Prompt construction                                 │
│   • Streaming support                                   │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐   ┌───────────────────────────────┐
│  Document Retriever │   │         Local LLM             │
│  src/core/          │   │      src/core/llm.py          │
│  retriever.py       │   │   Ollama (llama3.2/mistral)   │
│                     │   │   • generate() blocking       │
│  1. Embed query     │   │   • stream() token-by-token   │
│  2. Vector search   │   │   • No API key needed         │
│  3. Return top-k    │   └───────────────────────────────┘
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐   ┌───────────────────────────────┐
│   Vector Store      │   │   Embedding Generator         │
│ src/core/           │◀──│   src/core/embeddings.py      │
│ vector_store.py     │   │   sentence-transformers       │
│ ChromaDB persistent │   │   bge-small-en-v1.5 (default) │
└─────────────────────┘   └───────────────────────────────┘
           ▲
           │  (index build time)
           │
┌─────────────────────────────────────────────────────────┐
│              Document Processor                         │
│          src/core/document_processor.py                 │
│   PDF (.pdf) │ Word (.docx) │ Legacy Word (.doc)        │
│   • Clean text  • Chunk (1000 chars, 200 overlap)       │
│   • Extract metadata  • Sentence-boundary aware         │
└─────────────────────────────────────────────────────────┘
           ▲
           │
┌─────────────────────────────────────────────────────────┐
│                  data/raw/                              │
│        3GPP Specification Files                         │
│   TS 38.300, TS 38.401, TS 23.501 ...                  │
└─────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **No cloud dependencies** — ChromaDB persists locally, Ollama runs locally
- **Streaming first** — `rag_chain.stream_query()` yields tokens as they generate
- **Modular components** — each layer is independently testable and swappable
- **Graceful degradation** — clear error messages if Ollama isn't running

---

## ✨ Features

- 🔍 **Semantic Search** — finds conceptually relevant spec sections, not just keyword matches
- 💬 **Natural Language Queries** — ask questions like "What is the gNB-CU/DU split?"
- 📚 **Citation Tracking** — every answer includes source document name and similarity score
- 💰 **Zero Cost** — fully local, no API keys, no subscriptions
- 🔄 **Conversation Memory** — multi-turn conversations with context retention (configurable history depth)
- 📡 **Streaming Responses** — answers stream token-by-token for instant feedback
- 🗂️ **Multi-format Support** — indexes PDF, DOCX, and legacy DOC files
- 🔎 **Source Filtering** — restrict queries to a specific spec document
- 📊 **Performance Metrics** — per-query timing, aggregated stats, JSON export
- 🧪 **82 Unit Tests** — fully mocked test suite that runs without any live services

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com) (for LLM answer generation)
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ericnc09/3gpp-rag-assistant.git
cd 3gpp-rag-assistant

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment config
cp .env.example .env
```

### Set Up Ollama (Local LLM)

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.com for Windows/Linux

# Pull the default model (2GB, one-time download)
ollama pull llama3.2

# Start the Ollama server (keep running in background)
ollama serve
```

### Build the Index

```bash
# Place your 3GPP spec files in data/raw/
# Supports .pdf, .docx, .doc

# Process documents into chunks
python src/core/document_processor.py

# Build the vector index (embeds all chunks)
python scripts/build_index.py
```

### Query the Assistant

```bash
# Single question
python scripts/query.py "What is the gNB-CU architecture?"

# Stream answer token-by-token
python scripts/query.py --stream "Explain the F1 interface"

# Show source documents
python scripts/query.py --show-sources "How does handover work in 5G?"

# Filter to a specific spec
python scripts/query.py --source 38300 "What are the NR frequency bands?"

# Interactive multi-turn REPL
python scripts/query.py
```

Visit `http://localhost:8501` for the Streamlit UI (Week 2).

---

## 📖 Example Queries

```
You: What is the difference between SA and NSA 5G deployment?
You: Explain the NG-RAN architecture
You: What are the key features of the NR physical layer?
You: How does handover work in 5G networks?
You: What protocols run between gNB-CU and gNB-DU?
You: Describe the Xn interface
You: What is the role of the AMF in 5G core?
```

---

## 🔧 Configuration

Key settings in `.env`:

```env
# Local LLM (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2         # or: mistral, phi3, deepseek-r1

# Embeddings (local, free)
EMBEDDING_MODEL=bge-small   # or: mini, mpnet, bge-base

# Vector Database
VECTOR_DB_PATH=./data/vectordb
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# API
API_PORT=8000
LOG_LEVEL=INFO

# RAG Settings
MAX_HISTORY_LENGTH=5
TOP_K_RESULTS=5
```

### Available Embedding Models

All models run **completely free** and locally:

| Model | Size | Dimensions | Speed | Best For |
|---|---|---|---|---|
| `mini` | 80MB | 384 | ⚡ Fastest | Quick prototyping |
| `mpnet` | 420MB | 768 | 🔄 Medium | Balanced |
| `bge-small` | 130MB | 384 | ⚡ Fast | **Technical docs (default)** |
| `bge-base` | 440MB | 768 | 🔄 Medium | Maximum accuracy |

### Available LLM Models (Ollama)

| Model | Size | Notes |
|---|---|---|
| `llama3.2` | 2GB | Default — best balance of speed and quality |
| `mistral` | 4GB | Strong on technical text |
| `phi3` | 2.2GB | Fastest, good for constrained hardware |
| `deepseek-r1` | 4.7GB | Best for complex reasoning queries |

---

## 📁 Project Structure

```
3gpp-rag-assistant/
├── src/
│   ├── api/                        # FastAPI backend (Week 2)
│   │   ├── main.py                 # API endpoints
│   │   └── models.py               # Pydantic schemas
│   ├── core/                       # Core RAG logic
│   │   ├── document_processor.py   # Entry point: PDF/DOCX/DOC → chunks
│   │   ├── embeddings.py           # Local embedding generation
│   │   ├── vector_store.py         # ChromaDB wrapper
│   │   ├── retriever.py            # Semantic search
│   │   ├── llm.py                  # Ollama LLM client (stream + blocking)
│   │   └── rag_chain.py            # Full RAG pipeline + conversation memory
│   ├── utils/
│   │   ├── logger.py               # Structured logging
│   │   └── metrics.py              # Per-query timing + aggregated stats
│   └── frontend/                   # Streamlit UI (Week 2)
│       └── app.py
├── scripts/
│   ├── build_index.py              # Build ChromaDB vector index
│   ├── query.py                    # CLI query interface
│   └── eval_retrieval.py           # Retrieval + answer quality evaluation
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── test_embeddings.py          # 14 tests
│   ├── test_vector_store.py        # 11 tests
│   ├── test_retriever.py           # 15 tests
│   ├── test_llm.py                 # 9 tests
│   ├── test_rag_chain.py           # 14 tests
│   ├── test_metrics.py             # 21 tests
│   └── test_integration.py         # Integration tests (requires live index)
├── data/
│   ├── raw/                        # 3GPP specification files (.pdf/.docx/.doc)
│   └── processed/                  # Chunked documents (chunks.json)
├── docs/
│   └── GETTING_STARTED.md
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧪 Testing

```bash
# Run all unit tests (82 tests, no live services needed)
pytest tests/ --ignore=tests/test_integration.py

# Run with coverage report
pytest tests/ --ignore=tests/test_integration.py --cov=src --cov-report=term-missing

# Run integration tests (requires populated vector store)
pytest -m integration tests/test_integration.py

# Run evaluation script (retrieval quality)
python scripts/eval_retrieval.py

# Run full evaluation including answer quality (requires Ollama)
python scripts/eval_retrieval.py --full --output data/eval_results.json
```

**Current test coverage:**

| Module | Tests | Coverage |
|---|---|---|
| `embeddings.py` | 14 | 63% |
| `vector_store.py` | 11 | 88% |
| `retriever.py` | 15 | 53% |
| `llm.py` | 9 | 61% |
| `rag_chain.py` | 14 | 75% |
| `metrics.py` | 21 | 77% |
| **Total** | **82** | — |

---

## 📊 Performance Metrics

Benchmarks on Apple M2 (CPU only) — run `python scripts/eval_retrieval.py [--full]` to refresh:

### Retrieval Quality (10 representative 3GPP queries)

| Metric | Value |
|---|---|
| Pass rate | 6/10 (60%) |
| Avg context precision | 100% |
| Avg context recall | 80% |
| Avg cosine similarity | 0.510 |
| Retrieve latency p50 / p95 | 0.050s / 0.390s |

### Answer Quality (RAGAS-style, with Ollama llama3.2)

| Metric | Description |
|---|---|
| Answer relevance | Fraction of expected keywords in the answer |
| Faithfulness | Grounding signals + content overlap with retrieved context |
| Composite score | Relevance 40% + Faithfulness 40% + Substantive 20% |

Run `python scripts/eval_retrieval.py --full` to generate answer quality scores.
Latest results are served by the API at `GET /eval`.

### System Latency

| Metric | Value |
|---|---|
| Retrieve p50 | ~0.05s |
| Generate p50 | ~2–4s (llama3.2 on CPU) |
| Total query p50 | ~2–4s |
| Cost per query | **$0.00** |

---

## 🛣️ Product Development Roadmap

### Overview

This project follows a 3-week sprint structure from a working RAG prototype to a production-ready, deployable assistant.

```
Week 1: Core RAG Pipeline     ████████████████████  ✅ Complete
Week 2: API & Frontend        ████████████████████  ✅ Complete
Week 3: Polish & Deploy       ████████████████░░░░  🔄 In Progress
```

---

### ✅ Week 1 (Days 1–7): Core RAG Pipeline — COMPLETE

#### Day 1: Document Processing
- [x] `DocumentProcessor` — unified PDF / DOCX / DOC ingestion
- [x] Sentence-boundary-aware chunking (1000 chars, 200 overlap)
- [x] 3GPP-specific text cleaning (headers, footers, page numbers)
- [x] Metadata extraction (source filename, chunk index, format)
- [x] `data/raw/` → `data/processed/chunks.json` pipeline

#### Days 2–3: Vector Database & Embeddings
- [x] `LocalEmbeddingGenerator` — sentence-transformers, 4 model options
- [x] `VectorStore` — ChromaDB persistent client wrapper
- [x] Batched embedding generation with progress bar
- [x] `scripts/build_index.py` — end-to-end index build pipeline
- [x] Migrated from OpenAI embeddings → fully local (zero cost)

#### Days 4–5: LLM Integration & RAG Chain
- [x] `OllamaLLM` — local LLM client with `generate()` + `stream()`
- [x] `RAGChain` — full pipeline: retrieve → prompt → generate
- [x] Multi-turn conversation history (configurable depth)
- [x] Streaming support (token-by-token via `stream_query()`)
- [x] `scripts/query.py` — CLI with single, interactive, and stream modes
- [x] `src/utils/logger.py` — structured logging
- [x] `src/utils/metrics.py` — per-query timing + JSON persistence
- [x] Replaced OpenAI/LangChain deps with `ollama` (zero cost)

#### Days 6–7: Testing & Refinement
- [x] `tests/conftest.py` — shared fixtures for all test modules
- [x] `tests/test_embeddings.py` — 14 unit tests
- [x] `tests/test_vector_store.py` — 11 unit tests (real ChromaDB, temp dir)
- [x] `tests/test_retriever.py` — 15 unit tests
- [x] `tests/test_llm.py` — 9 unit tests (fully mocked)
- [x] `tests/test_rag_chain.py` — 14 unit tests
- [x] `tests/test_metrics.py` — 21 unit tests (incl. persistence)
- [x] `tests/test_integration.py` — parametrized retrieval quality tests
- [x] Fixed `document_processor.py` stub → delegates to unified processor
- [x] Extended `eval_retrieval.py` — answer quality scoring (keyword coverage, grounding, composite 0–1 score), `--full` and `--output` flags

---

### ✅ Week 2 (Days 8–14): API & Frontend — COMPLETE

#### Days 8–9: FastAPI Backend
- [x] `src/api/main.py` — REST API with lifespan startup, CORS, timing middleware
- [x] `POST /query` — submit a question, get answer + sources (blocking)
- [x] `POST /query/stream` — SSE streaming endpoint (token-by-token)
- [x] `GET /history/{id}` — per-session conversation history
- [x] `DELETE /history/{id}` — clear session history
- [x] `GET /health` — health check with per-component status
- [x] `GET /stats` — vector store and session stats
- [x] `GET /metrics` — aggregated query performance stats
- [x] `src/api/models.py` — Pydantic v2 request/response schemas
- [x] OpenAPI docs auto-generated at `/docs`
- [x] `tests/test_api.py` — 30 unit tests (FastAPI TestClient, all mocked)

#### Days 10–11: Cost Tracking & Observability
- [x] `X-Process-Time` timing header on every response
- [x] `src/utils/metrics.py` — per-query timing + JSON persistence
- [x] `GET /metrics` — mean/median/min/max total, retrieve, generate times
- [x] Per-session history isolation via server-side sessions dict
- [x] Configurable log level via `LOG_LEVEL` environment variable

#### Days 12–14: Streamlit UI
- [x] `src/frontend/app.py` — full Streamlit chat application
- [x] Streaming chat display (tokens appear as they are generated)
- [x] Source document expander (retrieved chunk previews with scores)
- [x] Sidebar: API health indicator, top-k slider, source filter input
- [x] Session management (reuses `session_id` across turns)
- [x] Runtime fixes: pyproject.toml editable install, Pydantic v2 ConfigDict,
      chromadb>=0.5.0 migration, httpx pin, streamlit headless config

---

### 🔄 Week 3 (Days 15–21): Polish & Deploy — IN PROGRESS

#### Days 15–16: Evaluation Metrics ✅
- [x] RAGAS-inspired evaluation framework (`scripts/eval_retrieval.py`)
- [x] Context precision: fraction of retrieved chunks from relevant source docs
- [x] Context recall: expected keyword coverage across top-3 chunks
- [x] Answer relevance: expected answer keyword hits in generated response
- [x] Faithfulness: grounding signals + content overlap with retrieved context
- [x] Composite answer quality score (relevance 40% + faithfulness 40% + substantive 20%)
- [x] p50/p95 latency benchmarks for retrieve and generate steps
- [x] 10 test cases covering gNB, handover, QoS, F1/E1/Xn interfaces, SA/NSA
- [x] `GET /eval` API endpoint serving latest `data/eval_results.json`
- [x] `tests/test_eval.py` — 40 new unit tests for all eval helpers + /eval endpoint

#### Days 17–18: Code Documentation ✅
- [x] Full module-level docstrings for all `src/` modules
- [x] `src/core/retriever.py` — class/method docs, return type annotations
- [x] `src/core/embeddings.py` — model comparison table, Args/Raises docs
- [x] `src/core/vector_store.py` — ChromaDB compatibility note
- [x] `src/config.py` — per-field attribute docs, `.env` usage guide
- [x] Removed 5 redundant/duplicate source files from `src/core/`

#### Day 19: Cleanup & README ✅
- [x] Removed redundant files: `document_processor_COMPLETE/DOC/DOCX.py`,
      `embeddings_LOCAL.py`, `test_document_processor_COMPLETE.py`
- [x] Updated test badge: 82 → 152 passing
- [x] Updated roadmap progress bars
- [x] Updated performance metrics with real eval results

#### Days 20–21: Deployment Prep
- [ ] `Dockerfile` for the API service
- [ ] `docker-compose.yml` (API + Ollama sidecar)
- [ ] `.env.example` with all configurable variables
- [ ] `scripts/start.sh` convenience startup script
- [ ] Git tag `v1.0.0`

---

### Phase Roadmap (Post-Sprint)

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Core RAG pipeline (local, zero cost) | ✅ Complete |
| Phase 2 | REST API + Streamlit UI | ✅ Complete |
| Phase 3 | Evaluation metrics & code quality | ✅ Complete |
| Phase 4 | Docker deployment | 🔄 In Progress |
| Phase 5 | Expand document coverage (LTE, more 5G series) | 📅 Planned |
| Phase 6 | Fine-tune embedding model on telecom domain | 📅 Planned |
| Phase 7 | Cloud deployment (AWS/GCP) | 📅 Planned |

---

## 🐳 Deployment

### Option A — Local (recommended for development)

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# 2. Start Ollama and pull a model
ollama serve &
ollama pull llama3.2

# 3. Build the vector index (once, or after adding new docs)
python src/core/document_processor.py
python scripts/build_index.py

# 4. Start both services with one command
./scripts/start.sh          # starts API on :8000 and UI on :8501

# Or start individually
./scripts/start.sh api      # API only
./scripts/start.sh ui       # UI only
./scripts/start.sh stop     # stop both
./scripts/start.sh status   # check status
```

### Option B — Docker Compose (recommended for deployment)

```bash
# 1. Copy and edit environment config
cp .env.example .env

# 2. Start all services (API + UI + Ollama)
docker compose up -d

# 3. Pull an LLM model (first time only)
docker compose exec ollama ollama pull llama3.2

# 4. Build the vector index (first time only)
docker compose run --rm api python src/core/document_processor.py
docker compose run --rm api python scripts/build_index.py

# 5. Open the UI
open http://localhost:8501
```

### Services

| Service | URL | Description |
|---|---|---|
| Streamlit UI | http://localhost:8501 | Chat interface |
| FastAPI | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive OpenAPI docs |
| Health | http://localhost:8000/health | Component health check |
| Eval Results | http://localhost:8000/eval | Latest retrieval evaluation |

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

When adding features, please include:
- Unit tests (mock external dependencies)
- Docstrings on public methods
- An entry in this README if it affects the roadmap or architecture

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **3GPP** for providing open access to technical specifications
- **BAAI** for the BGE embedding models optimised for technical text
- **Sentence Transformers** for the embedding framework
- **Ollama** for making local LLM serving simple and accessible
- **Hugging Face** for model hosting and the open-source ML community
- **Rogers Communications** for inspiring this project
- Open source community for making AI accessible to everyone 💙

---

## 📧 Contact

**Eric Costa**
Email: ericcosta.public@gmail.com
LinkedIn: [linkedin.com/in/niloyericcosta](https://linkedin.com/in/ericcostanil)
GitHub: [github.com/ericnc09](https://github.com/ericnc09)

---

> **Note**: This is a portfolio project demonstrating AI product engineering skills applied to the telecom domain. It is not affiliated with or endorsed by 3GPP or Rogers Communications.
