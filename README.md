# 3GPP RAG Assistant

A production RAG system over 37 3GPP technical specifications — 43,121 chunks, dual-deploy (local Ollama or cloud Groq), citation-grounded answers for engineers who spend hours lost in 1,000-page regulated specs.

**Live demo:** [3gpp-rag-assistant.streamlit.app](https://3gpp-rag-assistant.streamlit.app/) — animated walkthrough coming soon (see [docs/portfolio-upgrade/assets/DEMO_CAPTURE.md](docs/portfolio-upgrade/assets/DEMO_CAPTURE.md))
<!-- demo GIF — drop the recording at docs/portfolio-upgrade/assets/demo.gif and replace the line above with: ![Demo](docs/portfolio-upgrade/assets/demo.gif) -->

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-300%20passing-brightgreen.svg)](#testing)
[![Specs](https://img.shields.io/badge/3GPP%20specs-37%20indexed-blue.svg)](#architecture)
[![Chunks](https://img.shields.io/badge/chunks-43%2C121-blue.svg)](#architecture)

---

## Table of Contents

1. [What this is](#what-this-is)
2. [Evaluation](#evaluation)
3. [Security and regulated-domain readiness](#security-and-regulated-domain-readiness)
4. [Architecture](#architecture)
5. [Generalize to your corpus](#generalize-to-your-corpus)
6. [Quick start](#quick-start)
7. [Configuration](#configuration)
8. [Project structure](#project-structure)
9. [Testing](#testing)
10. [Roadmap](#roadmap)
11. [Deployment details](#deployment-details)
12. [Contributing](#contributing)
13. [License](#license)
14. [Contact](#contact)

---

## What this is

3GPP specifications are the authoritative source for all cellular standards (4G LTE, 5G NR). They are also notoriously hard to navigate: documents run 500–2,000 pages each, answers routinely span two or three specs, and there is no semantic search — only Ctrl+F inside a PDF.

This system closes that gap. An engineer types a question in plain English; the assistant retrieves the relevant spec excerpts, grounds the answer in the source text, and cites the document and section. Every answer is traceable.

**Who uses it:** telecom engineers, standards researchers, and engineers onboarding to 5G. A few colleagues at Rogers began using the public deploy voluntarily — it is a personal side project, not a Rogers program.

**What it demonstrates (for a hiring manager):** production RAG on a dense, regulated corpus — dual-deploy architecture, an eval harness with reproducible metrics, security controls verified by a personal audit, and a corpus-agnostic design that generalizes beyond 3GPP.

---

## Evaluation

> Eval report with full methodology: [`docs/portfolio-upgrade/EVAL_REPORT.md`](docs/portfolio-upgrade/EVAL_REPORT.md)
> Reproduce: `python scripts/eval_retrieval.py --output data/eval_results.json`

Current results from `data/eval_results.json` (run 2026-06-24, full index of 43,121 chunks, 30-query golden set, top-k=5). The golden set splits into 25 answerable (in-corpus) queries and 5 deliberately out-of-corpus probes; retrieval metrics are reported over the 25, the refusal axis over the 5.

**Retrieval quality — in-corpus (N=25), standard IR metrics:**

| Metric | Value | Notes |
|---|---|---|
| Hit-rate@5 | 0.88 | a relevant source appears in top-5 for 88% of queries |
| nDCG@5 | 0.729 | rank-weighted; "GOOD" band in the harness |
| MRR | 0.679 | first relevant hit lands high on average |
| Recall@5 | 0.64 | fraction of all expected source specs surfaced |
| Avg context precision | 0.44 | heuristic (keyword); supplementary, not IR-standard |
| Avg context recall | 0.71 | heuristic keyword coverage across top-3 |
| Legacy pass rate | 18/25 (72%) | keyword recall ≥0.5 AND avg sim ≥0.50 |
| Retrieve latency p50 / p95 | 0.021s / 0.048s | Apple M2 CPU, local ChromaDB |

**Refusal axis — out-of-corpus probes (N=5):** 4/5 (80%) correctly stay below the relevance threshold (no confident match surfaced); avg out-of-corpus similarity 0.331 vs 0.557 in-corpus. The LLM-judged refusal rate (did the *generated answer* actually decline?) needs `--full` + a live model and is marked `[RUN REQUIRED]`.

**Reading the gap between 88% hit-rate and 72% legacy pass.** Of the 7 in-corpus queries that miss the legacy pass bar, 4 (gNB, HARQ, X2, SDAP) actually retrieve the correct source (nDCG 1.0) and miss only because bge-small's cosine similarity runs just under the 0.50 threshold. Only 3 are genuine retrieval misses — E1 interface, SA-vs-NSA, NR-vs-LTE physical layer — all comparison/interface queries where the question phrasing diverges from spec terminology. That cluster, plus the strict similarity threshold, are the concrete next targets (see [roadmap](#roadmap)).

**Heuristic vs IR-standard.** Context precision/recall are keyword-based heuristics (RAGAS-inspired), kept as supplementary signals. Hit-rate/Recall@k/MRR/nDCG are the standard IR metrics. **Still `[RUN REQUIRED]`:** LLM-judge faithfulness/answer-correctness and the LLM-judged refusal rate — these need `--full` + a live model and are not fabricated here.

---

## Security and regulated-domain readiness

> Disclosure policy and reporting: [`SECURITY.md`](SECURITY.md)
> Threat model with code-level control mapping: [`docs/portfolio-upgrade/THREAT_MODEL.md`](docs/portfolio-upgrade/THREAT_MODEL.md)

The live deploy is public-facing. The following controls are in the codebase — the threat model links each to its file and line:

| Threat | Control | Location |
|---|---|---|
| DoS / rate abuse | Per-IP rate limiting (LRU store, bounded size) | `src/api/main.py` |
| SSRF via Ollama URL | Allowlist validator (localhost / docker hosts only) | `src/config.py` |
| SSRF via vectordb download | Domain allowlist + redirect limit | `streamlit_app.py` |
| Path traversal (tar extract) | Safe-extract guard, rejects `../` members | `streamlit_app.py` |
| Prompt injection / output XSS | HTML-escaping of source text before render | `streamlit_app.py` |
| Oversized / malformed input | Pydantic bounds (min/max length, Literal enums) | `src/api/models.py` |
| Clickjacking / MIME sniffing | Security headers (X-Frame-Options, X-Content-Type-Options, CSP) | `src/api/main.py` |

A personal-project security audit surfaced 42 issues resolved across two hardening rounds. The individual findings are not reproduced here; the threat model maps the control categories that are verifiable in the repository.

---

## Architecture

The system has two deploy modes that share the same retrieval stack but differ in the LLM and embedding path:

```
                        User query
                            |
            ┌───────────────┴───────────────┐
            │           RAG Chain           │
            │       src/core/rag_chain.py   │
            │  multi-turn history, prompt,  │
            │  streaming                    │
            └──────────┬────────────────────┘
                       |
          ┌────────────┴────────────┐
          |                         |
   ┌──────▼───────┐         ┌───────▼────────────────────────┐
   │   Retriever  │         │           LLM                  │
   │  top-k chunk │         │                                │
   │  search with │         │  LOCAL: Ollama (llama3.2,      │
   │  domain /    │         │  mistral, phi3) — no API key   │
   │  generation  │         │                                │
   │  filters     │         │  CLOUD: Groq llama-3.3-70b-    │
   └──────┬───────┘         │  versatile — GROQ_API_KEY      │
          |                 │  required                      │
   ┌──────▼───────┐         └────────────────────────────────┘
   │  Vector Store│
   │  ChromaDB    │
   │              │
   │  LOCAL: full │  sentence-transformers bge-small-en-v1.5
   │  persist DB  │  (local, no API key)
   │              │
   │  CLOUD: ONNX │  ChromaDB built-in ONNX runtime
   │  embeddings, │  (no torch), DB pulled from
   │  DB from     │  GitHub Release asset at startup
   │  GH Release  │
   └──────┬───────┘
          |
   ┌──────▼───────────────────────────────────────────────┐
   │  Document Processor  +  Spec Catalog                  │
   │  37 specs × (5G/LTE) × (RAN/CORE)                    │
   │  PDF / DOCX / DOC → 1000-char chunks, 200 overlap     │
   │  3GPP-specific cleaning, metadata per chunk           │
   └──────────────────────────────────────────────────────┘
```

**Key decisions** (full ADR log: [`docs/portfolio-upgrade/DECISIONS.md`](docs/portfolio-upgrade/DECISIONS.md)):

- **RAG over fine-tuning.** 3GPP specs update every release cycle; RAG re-indexes without retraining. Citations are non-negotiable for standards work.
- **bge-small-en-v1.5.** Best accuracy-to-size ratio on technical/scientific text (MTEB). 130MB, 384-dim, runs on CPU.
- **Chunk size 1000 / overlap 200.** Large enough to preserve context around a protocol definition; overlap prevents boundary splits from losing cross-sentence references.
- **Ollama (local) + Groq (cloud) as a toggle.** `src/config.py` `llm_provider` field selects the path. The cloud deploy uses Groq because Streamlit Cloud has no GPU; Ollama is the local-dev default. Both paths are real.
- **ChromaDB ONNX on cloud.** Avoids a PyTorch dependency on the Streamlit Cloud runtime. The pre-built vectordb is attached to a GitHub Release and downloaded at app startup.

---

## Generalize to your corpus

> Full guide: [`docs/portfolio-upgrade/GENERALIZE.md`](docs/portfolio-upgrade/GENERALIZE.md)

3GPP is the reference corpus; the architecture is not 3GPP-specific. The retrieval stack (document processor, ChromaDB, filtered retrieval, RAG chain) works on any technical or regulated document set. 3GPP-specific logic is contained in `src/core/spec_catalog.py` (the spec registry) and the 3GPP-aware text cleaner in `document_processor.py`.

To point the system at a different corpus — medical device standards, financial regulations, internal engineering wikis — you replace the catalog and cleaning logic. GENERALIZE.md documents the seam: what to implement, what to leave unchanged, and the 3GPP catalog as a worked example.

---

## Quick start

### Option A — Local (Ollama, no API key needed)

```bash
# 1. Clone and install
git clone https://github.com/ericnc09/3gpp-rag-assistant.git
cd 3gpp-rag-assistant
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 2. Install Ollama and pull a model
brew install ollama          # or: https://ollama.com for Windows/Linux
ollama pull llama3.2
ollama serve &

# 3. Download specs and build the vector index
python scripts/download_specs.py          # all 37 specs from 3GPP FTP
python scripts/build_index.py

# 4. Run the assistant
python scripts/query.py "What is the gNB-CU/DU split?"   # single query
python scripts/query.py                                    # interactive REPL
streamlit run src/frontend/app.py                          # web UI
```

### Option B — Cloud deploy (Groq API key required)

The live app at [3gpp-rag-assistant.streamlit.app](https://3gpp-rag-assistant.streamlit.app/) runs Groq `llama-3.3-70b-versatile` with a pre-built ChromaDB vectordb. To self-host the same configuration:

1. Get a free Groq API key at [console.groq.com/keys](https://console.groq.com/keys).
2. Upload a pre-built vectordb tarball to a GitHub Release; set `VECTORDB_URL` to the asset URL.
3. Set Streamlit secrets: `GROQ_API_KEY`, `VECTORDB_URL`.
4. Deploy `streamlit_app.py` via [share.streamlit.io](https://share.streamlit.io).

For local development with Groq instead of Ollama, set `LLM_PROVIDER=groq` and `GROQ_API_KEY=<key>` in `.env`.

```bash
# Install cloud dependencies only
pip install -r requirements-cloud.txt
```

---

## Configuration

Key `.env` settings:

```env
# LLM provider: "ollama" (local, no API key) or "groq" (cloud, key required)
LLM_PROVIDER=ollama

# Ollama (local path)
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.2            # or: mistral, phi3, deepseek-r1

# Groq (cloud path)
GROQ_API_KEY=                 # get at https://console.groq.com/keys
# groq_model is set in src/config.py: llama-3.3-70b-versatile

# Embeddings (local sentence-transformers, applies to local path only)
EMBEDDING_MODEL=bge-small     # or: mini, mpnet, bge-base

# Vector database
VECTOR_DB_PATH=./data/vectordb
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# API
API_PORT=8000
LOG_LEVEL=INFO

# RAG
MAX_HISTORY_LENGTH=5
TOP_K_RESULTS=5
```

### Embedding models (local path)

| Key | Model | Size | Dimensions | Notes |
|---|---|---|---|---|
| `bge-small` | BAAI/bge-small-en-v1.5 | 130MB | 384 | Default — best technical-doc accuracy at this size |
| `bge-base` | BAAI/bge-base-en-v1.5 | 440MB | 768 | Higher accuracy, more RAM |
| `mini` | all-MiniLM-L6-v2 | 80MB | 384 | Faster, slightly lower accuracy |
| `mpnet` | all-mpnet-base-v2 | 420MB | 768 | Good balance |

### LLM options (local path via Ollama)

| Model | Size | Notes |
|---|---|---|
| `llama3.2` | 2GB | Default |
| `mistral` | 4GB | Strong on technical text |
| `phi3` | 2.2GB | Fastest, good for constrained hardware |
| `deepseek-r1` | 4.7GB | Best for multi-step reasoning queries |

---

## Project structure

```
3gpp-rag-assistant/
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI: query, catalog, eval, health; rate limiting; security headers
│   │   └── models.py           # Pydantic v2 schemas with input bounds
│   ├── core/
│   │   ├── document_processor.py
│   │   ├── embeddings.py       # sentence-transformers, 4 model options
│   │   ├── vector_store.py     # ChromaDB wrapper with metadata where-filters
│   │   ├── retriever.py        # Semantic search, domain/generation filtering
│   │   ├── llm.py              # Ollama client (local path)
│   │   ├── groq_llm.py         # Groq client (cloud path)
│   │   ├── rag_chain.py        # Full pipeline + conversation memory
│   │   └── spec_catalog.py     # 37-spec registry (5G/LTE × RAN/CORE) + FTP URLs
│   ├── utils/
│   │   ├── logger.py
│   │   └── metrics.py          # Per-query timing + JSON persistence
│   └── frontend/
│       └── app.py              # Streamlit chat UI (connects to FastAPI)
├── streamlit_app.py            # Self-contained Streamlit Cloud entry point (Groq + ONNX)
├── scripts/
│   ├── download_specs.py       # Fetch latest specs from 3GPP FTP
│   ├── build_index.py          # Build ChromaDB index
│   ├── build_index_cpu.py      # CPU-only build (avoids MPS stalls on large files)
│   ├── query.py                # CLI query interface
│   └── eval_retrieval.py       # Retrieval + answer-quality eval harness
├── tests/
│   ├── conftest.py
│   ├── test_embeddings.py      # 14 tests
│   ├── test_vector_store.py    # 11 tests
│   ├── test_retriever.py       # 15 tests
│   ├── test_llm.py             # 9 tests
│   ├── test_rag_chain.py       # 14 tests
│   ├── test_metrics.py         # 21 tests
│   ├── test_api.py             # 30 tests
│   ├── test_eval.py            # 40 tests
│   └── test_integration.py     # Requires live index (excluded from unit run)
├── data/
│   ├── raw/                    # 3GPP spec files (PDF / DOCX / DOC)
│   └── eval_results.json       # Latest retrieval eval output
├── docs/
│   ├── GETTING_STARTED.md
│   ├── portfolio-upgrade/
│   │   ├── PLAN.md
│   │   ├── EVAL_REPORT.md      # Eval methodology + results (Stream B)
│   │   ├── THREAT_MODEL.md     # STRIDE threat model with file:line control map (Stream C)
│   │   ├── DECISIONS.md        # Architecture decision log (Stream E)
│   │   ├── METRICS.md          # Product + eval metrics (Stream E)
│   │   ├── ROADMAP.md          # Canonical product roadmap (Stream E)
│   │   ├── GENERALIZE.md       # How to use this with a non-3GPP corpus (Stream D)
│   │   └── assets/
│   │       └── demo.gif        # Demo recording (see capture instructions in assets/)
│   ├── demo_qa.md
│   └── demo_slide.md
├── requirements.txt            # Full local deps (Ollama path)
├── requirements-cloud.txt      # Cloud deps (Groq + ONNX, no torch)
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Testing

```bash
# Run all unit tests (no live services needed)
pytest tests/ --ignore=tests/test_integration.py

# With coverage
pytest tests/ --ignore=tests/test_integration.py --cov=src --cov-report=term-missing

# Integration tests (requires populated vector store)
pytest -m integration tests/test_integration.py

# Run the eval harness (retrieval metrics only, no LLM needed)
python scripts/eval_retrieval.py --output data/eval_results.json

# Run full eval including answer quality (requires Ollama running with a model)
python scripts/eval_retrieval.py --full --output data/eval_results.json
```

**300 tests, all mocked — no live services required. 308 including integration tests (which need a populated vector store).** `pytest tests/ --ignore=tests/test_integration.py` collects 300 and passes all of them in a clean virtual environment with the mocked dependencies in `conftest.py`. (In a dev venv that has drifted to starlette ≥0.36, 35 FastAPI route tests error on a known `on_startup` incompatibility — `requirements.txt` pins `starlette>=0.35,<0.36` to keep the suite green.)

CI runs on Python 3.9, 3.10, 3.11 (GitHub Actions). Checks: flake8, black, pytest --cov, Codecov.

---

## Roadmap

<!-- Stream E: canonical roadmap in docs/portfolio-upgrade/ROADMAP.md; reconcile if divergent -->

The phases below track outcome-oriented milestones, not calendar sprints.

```
M1: Working RAG pipeline         ████████████████  SHIPPED
M2: REST API + Streamlit UI      ████████████████  SHIPPED
M3: Eval harness + Docker        ████████████████  SHIPPED
M4: Multi-spec + domain filter   ████████████████  SHIPPED
M5: Full 37-spec coverage        ████████████████  SHIPPED
M6: Eval rigor + security docs   ████████████░░░░  IN PROGRESS
M7: Multi-document reasoning     ░░░░░░░░░░░░░░░░  PLANNED
M8: Hosted team version          ░░░░░░░░░░░░░░░░  PLANNED
```

**M1 — Working RAG pipeline (shipped)**
Unified PDF/DOCX/DOC ingestion, sentence-boundary chunking (1000 chars / 200 overlap), local bge-small embeddings, ChromaDB persistence, Ollama LLM client, multi-turn RAG chain with conversation memory. Decision: RAG over fine-tuning — 3GPP specs update every release cycle; re-indexing is instant, retraining is not.

**M2 — REST API + Streamlit UI (shipped)**
FastAPI with per-session history, SSE streaming, OpenAPI docs. Streamlit chat UI with domain/generation filter panel. Decision: streaming-first design — token-by-token output matters more than raw throughput for interactive use.

**M3 — Eval harness + Docker deployment (shipped)**
RAGAS-inspired eval (`scripts/eval_retrieval.py`): standard IR metrics (hit-rate@k, Recall@k, MRR, nDCG@k) plus heuristic context precision/recall, cosine similarity, latency p50/p95, and a regression gate. Docker + docker-compose for reproducible local deploy. Multi-stage Dockerfile (non-root user, HEALTHCHECK). Full-index eval (43,121 chunks, 25 in-corpus queries): hit-rate@5 0.88, nDCG@5 0.729, MRR 0.679.

**M4 — Multi-spec domain filtering (shipped)**
37-spec catalog across 5G NR RAN, LTE RAN, 5G Core, LTE Core. Metadata-tagged chunks (domain, generation, spec_number). Pre-retrieval ChromaDB `where` filters. Decision: metadata filtering over post-retrieval scoring — filtering before retrieval scales better and is more predictable.

**M5 — Full 37-spec coverage (shipped)**
All 37 specs downloaded and indexed (43,121 chunks in the local/API index; the hosted Streamlit demo loads a 41,429-chunk subset sized for free-tier deployment). CPU-only index builder to avoid Apple MPS stalls on large files. macOS `textutil` as first-choice `.doc` extractor. Fixed ID collision bug in multi-file indexing.

**M6 — Eval rigor + security documentation (shipped)**
Eval harness now reports Recall@k, MRR, nDCG, hit-rate over a versioned 30-query golden dataset (`data/eval/golden_set.jsonl`, 25 in-corpus + 5 out-of-corpus refusal probes), with a committed regression baseline and CI gate. LLM-judge faithfulness/answer-correctness is coded and `[RUN REQUIRED]`. Added `SECURITY.md` + a STRIDE-style threat model, and made the corpus-agnostic seam explicit in code (`scripts/build_index.py` consumes `DEFAULT_CORPUS`).

**M7 — Multi-document reasoning (planned)**
Answers that explicitly synthesize across spec boundaries (e.g. TS 38.300 + 38.401 + 23.501). Success metric: eval cases requiring cross-spec synthesis pass at the same rate as single-spec cases.

**M8 — Hosted team version (planned)**
Auth layer, shared session management, team-scoped history. Decision pending: evaluate managed auth (Clerk, Auth0) vs. custom session tokens.

---

## Deployment details

### Docker Compose (local, all services)

```bash
cp .env.example .env
docker compose up -d
docker compose exec ollama ollama pull llama3.2
docker compose run --rm api python scripts/build_index.py
open http://localhost:8501
```

### Services

| Service | URL | Notes |
|---|---|---|
| Streamlit UI | http://localhost:8501 | Chat UI with domain/generation filter |
| FastAPI | http://localhost:8000 | REST API |
| API docs | http://localhost:8000/docs | OpenAPI |
| Health | http://localhost:8000/health | Component status |
| Catalog | http://localhost:8000/catalog | 37 specs with indexed status |
| Eval | http://localhost:8000/eval | Latest eval results |

---

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Add unit tests for new logic (mock external dependencies).
4. Run `black .` and `flake8` before opening a PR.
5. For changes that affect the architecture or eval methodology, update the relevant doc in `docs/portfolio-upgrade/`.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contact

**Eric Costa**
Email: ericcosta.public@gmail.com
LinkedIn: [linkedin.com/in/niloyericcosta](https://www.linkedin.com/in/niloyericcosta/)
GitHub: [github.com/ericnc09](https://github.com/ericnc09)

---

> This is a personal side project demonstrating AI product engineering applied to a regulated technical domain. It is not affiliated with or endorsed by 3GPP or Rogers Communications.

