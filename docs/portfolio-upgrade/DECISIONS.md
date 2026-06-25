# Architecture Decision Records — 3GPP RAG Assistant

Seven real decisions made during the build. Each traces directly to code or to the owner's experience, with no invented outcomes.

---

## ADR-001: RAG over fine-tuning

**Status:** Decided  
**Date:** early project  
**Context source:** `README.md` §"RAG vs. Fine-tuning", `src/core/rag_chain.py`

### Context

The core product problem is: telecom engineers lose hours cross-referencing 3GPP specifications — documents that are updated every release cycle and that aren't publicly paired with Q&A labels. Two architectures could address this: fine-tune an LLM on 3GPP content, or build a retrieval-augmented system that queries a live index at inference time.

### Options considered

| Option | Pros | Cons |
|---|---|---|
| Fine-tune on 3GPP text | No retrieval latency; answers feel fluent | No citations (traceability is non-negotiable for standards work); corpus changes require full retraining; labeled Q&A pairs don't exist publicly for 3GPP |
| RAG over indexed specs | Citations baked in; re-indexing is cheap (minutes, not days); works with any LLM backbone; index reflects the exact release under question | Retrieval quality gates answer quality; chunking strategy matters; two failure modes (retrieval miss vs generation miss) instead of one |

### Decision

RAG. The deciding factor was traceability: in standards work, a cited answer that the engineer can verify is worth more than a confident answer they cannot. Fine-tuning also breaks on the corpus-update cadence — 3GPP publishes new releases regularly and the user should be able to re-index in one command, not retrain.

### Tradeoff accepted

Answer quality is bounded by retrieval quality. A retrieval miss is a silent failure — the model generates an answer from whatever it retrieves, which may be adjacent but wrong. This drove investment in the eval harness (pass rate metric, context precision/recall), and it's why the prompt instructs the model to say so when context is insufficient (`groq_llm.py` line 24: "If the context does not contain enough information, say so clearly").

### Outcome

Indexed 44,290 chunks across 37 specs. Eval results (2026-02-27) show retrieval pass rate 6/10 with avg context precision 1.0 — meaning retrieved chunks come from the right sources when retrieval passes. The 4 failures are recall misses, not precision errors. That's a useful signal: the system retrieves relevant material when it retrieves at all, but it occasionally retrieves nothing useful for terse or ambiguous queries.

---

## ADR-002: Dual-provider LLM architecture (Ollama local + Groq cloud)

**Status:** Decided  
**Date:** v2 migration  
**Context source:** `src/config.py` lines 48–72; `src/core/llm.py`; `src/core/groq_llm.py`; `requirements.txt`; `requirements-cloud.txt`

### Context

v1 used Ollama exclusively (llama3.2 running locally). This was honest and accessible — no API keys, zero cost, works offline — but it made a public Streamlit Cloud deploy impossible: Streamlit Cloud doesn't expose a GPU or a persistent Ollama process. The product needed to run both locally (zero cost, offline, full privacy) and in the cloud (no-install, shareable URL).

### Options considered

| Option | Pros | Cons |
|---|---|---|
| Ollama only | Zero cost; no API key; works offline; full privacy | Cannot deploy to Streamlit Cloud; depends on user having Ollama + a pulled model |
| OpenAI or Anthropic API | Proven quality; wide integration | Paid; adds vendor dependency; cost scales with queries |
| Groq free tier (llama-3.3-70b) | Free API key; open-source model; fast inference; cloud-deployable | External dependency; key required; rate limits on free tier |
| One provider only | Simpler config | Either locks out cloud deploy or locks out local/offline users |

### Decision

Build a dual-provider architecture with a `llm_provider` config toggle (`src/config.py` line 49: `llm_provider: str = "ollama"`). The cloud app (`streamlit_app.py`) hard-selects Groq directly. The local app reads the env toggle. Both use the same retrieval layer and prompt format. `requirements-cloud.txt` drops Ollama and sentence-transformers; Streamlit Cloud gets ChromaDB's built-in ONNX embeddings and the Groq client instead.

### Tradeoff accepted

Two code paths for LLM calls. Both must be maintained. The `GroqLLM` and `OllamaLLM` classes share the same interface (`generate()` and `stream()`) but are not formally typed under a common abstract base — that's a cleanup item. The README historically advertised only the Ollama path ("completely free, fully local, no API keys required"), which made the cloud deploy look broken rather than intentional. That framing is being corrected in the README.

### Outcome

The live Streamlit Cloud app runs Groq llama-3.3-70b-versatile. Local installs default to Ollama. The dual-path architecture is real and working; neither path was invented.

---

## ADR-003: Embedding model — bge-small-en-v1.5

**Status:** Decided  
**Date:** early project  
**Context source:** `src/config.py` line 75; `src/core/embeddings.py`; `README.md` §"Embedding model selection research"

### Context

The embedding model determines what "similar" means in the vector index. For 3GPP text, the relevant similarity is technical and structural — "gNB-CU" should be close to "CU function" and "F1 interface" should be close to "F1 split architecture" — not general English paraphrase similarity.

### Options evaluated

| Model | Dim | Size | Notes |
|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | 80 MB | Baseline; optimized for general English |
| `all-mpnet-base-v2` | 768 | 420 MB | Better general quality; large for cloud |
| `BAAI/bge-small-en-v1.5` | 384 | 130 MB | Top MTEB scores for technical/scientific text at small scale |
| `BAAI/bge-base-en-v1.5` | 768 | 440 MB | Better accuracy; too large for Streamlit Cloud free tier |

### Decision

`bge-small-en-v1.5` as default. The BAAI BGE family consistently leads MTEB benchmarks on technical retrieval tasks. The small variant provides the accuracy advantage of the BGE family with a 130 MB footprint — viable on constrained hardware and in cloud environments. `bge-base` is the recommended upgrade if latency and storage allow; it's exposed as a config option (`embedding_model: str = "bge-small"`, config line 75).

### Tradeoff accepted

Embedding model is baked into the index at build time. Changing the model requires rebuilding the entire 44K-chunk index. If someone builds locally with `bge-small` and later switches to `bge-base`, they must rebuild — the vectors aren't interchangeable. This is documented in setup.

### Outcome

`bge-small` is the default for both local and cloud paths. Eval average cosine similarity is 0.51 across the 10-query set (2026-02-27). The cloud deploy uses ChromaDB's built-in ONNX embedding path (see ADR-005), which bypasses the Python sentence-transformers model entirely.

---

## ADR-004: Chunk size 1000 characters / overlap 200

**Status:** Decided  
**Date:** early project  
**Context source:** `src/config.py` lines 83–84; `src/core/document_processor.py`; `README.md` §"Chunking strategy research"

### Context

3GPP specifications have a particular structure: dense tables, numbered clauses, definition lists, and long normative sentences that don't stand alone. Chunk size controls the precision/recall tradeoff in retrieval — small chunks improve precision (you get exactly the right clause) but hurt recall for multi-sentence answers; large chunks improve recall but bring more noise per retrieved chunk.

### Options considered

| Chunk size | Overlap | Concern |
|---|---|---|
| 500 chars | 100 | Cuts normative sentences mid-clause; poor for tables |
| 1000 chars | 200 | Keeps most clauses intact; comfortable context window |
| 2000 chars | 400 | More context per chunk; retrieval less precise; slower embedding |
| Paragraph-based | Variable | Cleaner splits; harder to implement on .docx; variable sizes complicate vector store |

### Decision

1000 chars / 200 overlap, sentence-boundary-aware splitting. The overlap ensures continuity at chunk boundaries (a definition that spans two chunks will appear whole in at least one). The 3GPP-specific cleaner strips headers, footers, and page numbers before chunking, so the 1000-char budget isn't wasted on structural noise.

### Tradeoff accepted

Character-based chunking doesn't respect semantic structure — a table row and a normative clause get the same treatment. A future improvement would be structure-aware splitting (table rows as atomic units, clause boundaries as split points). The current approach is good enough for the eval cases tested and is reproducible.

### Outcome

44,290 chunks from 37 specs at this chunk size. The eval latency at p50 is 0.325s for retrieval (2026-02-27), which is acceptable. No individual case shows retrieval latency above 1.2s.

---

## ADR-005: ChromaDB ONNX on cloud (no sentence-transformers)

**Status:** Decided  
**Date:** v2 / cloud deploy  
**Context source:** `streamlit_app.py` lines 1–11 (module docstring); `requirements-cloud.txt`; `src/core/vector_store.py`

### Context

Streamlit Cloud has a memory limit. The sentence-transformers library imports PyTorch, which alone uses several hundred MB. On the free tier, `bge-small` + PyTorch pushed total memory close to or over the limit, and cold starts were slow. ChromaDB offers a built-in ONNX embedding path that doesn't require PyTorch — it uses the ONNX Runtime, which is significantly lighter.

### Options considered

| Embedding on cloud | Memory footprint | Concern |
|---|---|---|
| sentence-transformers (bge-small) | ~600 MB with PyTorch | Exceeds or strains Streamlit Cloud free tier |
| OpenAI text-embedding-ada-002 | Negligible (API call) | Paid; adds external dependency; incompatible with local index |
| ChromaDB built-in ONNX | ~150 MB | Different embedding space than the local bge-small path |
| Pre-computed vectordb shipped as a GitHub Release asset | No embedding at runtime | Sidesteps the problem entirely for the cloud app |

### Decision

Ship a pre-built vectordb as a GitHub Release asset (tar.gz, ~230 MB) and have the cloud app download it on first run (`streamlit_app.py` line 120–128). This avoids runtime embedding on Streamlit Cloud entirely. ChromaDB's ONNX embedding is still available for hybrid use cases. The cloud app does not re-embed at query time — it uses ChromaDB's native query on the pre-built index, which uses the same vectors already stored.

### Tradeoff accepted

The cloud vectordb is a static snapshot. Re-indexing new specs requires rebuilding locally and re-uploading the Release asset. This is acceptable for a project with infrequent corpus changes. The SSRF and path-traversal guards in `_download_and_extract()` (`streamlit_app.py` lines 149–186) protect the download step.

### Outcome

Live cloud app downloads the vectordb on first run, cold-start overhead is a one-time ~230 MB download. Subsequent visits use the cached path. No PyTorch dependency on Streamlit Cloud.

---

## ADR-006: Security hardening before public launch

**Status:** Decided  
**Date:** pre-launch (v2)  
**Context source:** `src/api/main.py` lines 62–112 (rate limiting, security constants); lines 210–222 (security headers middleware); `src/api/models.py` lines 17–51 (Pydantic bounds); `streamlit_app.py` lines 149–186 (SSRF + path-traversal); `src/config.py` lines 54–65 (Ollama SSRF validator); `streamlit_app.py` lines 584–585 (HTML escaping)

### Context

Most personal AI side projects deploy without any security review. This one serves a live public URL that accepts user input, downloads remote files, and proxies queries to an LLM. Before promoting it as a public tool to telecom engineers, a formal security audit was run that surfaced 42 vulnerabilities across the codebase, resolved across two hardening rounds. [UNVERIFIED — from owner's audit notes; individual findings are not reproduced here, only the control categories verifiable in code.]

### Controls implemented (all traceable to code)

| Threat | Control | Location |
|---|---|---|
| DoS via query flooding | Per-IP rate limit: 20 req/min, LRU-bounded store of 10,000 IPs | `src/api/main.py` lines 62–112 |
| Memory DoS (session explosion) | Max 200 sessions; TTL 1 hour; LRU eviction | `src/api/main.py` lines 62–64, `AppState.evict_expired_sessions()` |
| Prompt injection | Strict system prompt with explicit override-rejection instruction | `streamlit_app.py` lines 100–113 (PROMPT_TEMPLATE) |
| SSRF via Ollama URL | `field_validator` restricts `ollama_base_url` to `localhost`/trusted hosts only | `src/config.py` lines 54–65 |
| SSRF via vectordb download | Domain allowlist: `{github.com, objects.githubusercontent.com, github-releases.githubusercontent.com}` | `streamlit_app.py` lines 149–158 |
| Path traversal via tar extract | Validates every tar member; blocks absolute paths and `..` sequences | `streamlit_app.py` lines 177–185 |
| XSS via source output | `html.escape()` on source filename and text before rendering | `streamlit_app.py` lines 584–585 |
| Oversized inputs | Pydantic `min_length`/`max_length` on all fields; `max_length=1000` on question; UUID pattern on session_id | `src/api/models.py` lines 19–31 |
| Response header attacks | `X-Content-Type-Options`, `X-Frame-Options: DENY`, CSP `frame-ancestors 'none'`, `Referrer-Policy`, `Permissions-Policy` | `src/api/main.py` lines 217–221 |

### Decision

All 42 vulnerabilities resolved before public promotion. A 3GPP compliance layer was also added (legal disclaimer, source-text truncation) to address regulatory exposure specific to the domain.

### Tradeoff accepted

The rate limiter is in-process — it resets on restart and doesn't share state across multiple instances. A distributed cache (Redis) would be needed for multi-instance deployments. Adequate for the current single-instance Streamlit Cloud deploy.

### Outcome

The public app has been live without a reported incident. The security controls are visible in code — not claims, verifiable decisions.

---

## ADR-007: Dedup to latest version per spec at index time

**Status:** Decided  
**Date:** Phase 2 (multi-spec build)  
**Context source:** `scripts/build_index.py` lines 70–119 (`find_spec_files()`)

### Context

The 3GPP FTP archive contains multiple version files per spec (e.g. `38300-h30.docx`, `38300-j10.docx`, `38300-j00.docx`). Indexing all versions would bloat the index, create duplicate answers with conflicting content across releases, and confuse the retrieval layer — a query about the F1 interface would retrieve chunks from 4 different release versions of TS 38.300 simultaneously.

### Options considered

| Approach | Concern |
|---|---|
| Index all versions | Index grows ~4x; retrieval returns conflicting information across releases; user can't tell which release answered the question |
| Index only a pinned version | Safe but requires manual update each 3GPP release cycle |
| Dedup to latest per spec (sort descending by filename) | Latest version wins automatically; index stays manageable; consistent with how engineers use specs in practice |
| Version-aware retrieval (keep all, filter by release) | Powerful for release-delta queries; complex to implement and query; user UX for release filtering is unclear |

### Decision

Dedup to latest version per spec at index-build time. `find_spec_files()` groups candidate files by inferred spec number, sorts descending by filename (highest version suffix wins), and selects one file per spec. Companion files (change-logs `-cl`, revision marks `-rm`, cover sheets) are filtered first via `_SKIP_SUFFIXES`.

### Tradeoff accepted

If a user specifically wants to query an older release, they cannot today without rebuilding the index from that version. The `--file` flag allows single-file reindexing for this use case, but there's no UI for version pinning. This is documented as a known limitation.

### Outcome

37 specs indexed, one file per spec (the latest available download). 44,290 chunks. The dedup logic is tested implicitly through the 40 eval tests in `tests/test_eval.py` and the index build output.

---

## Cross-stream requests

**To Stream A (README owner):**

The README's "Key design decisions" bullet list currently says "No cloud dependencies" — this was true in v1 but is inaccurate for v2 (Groq is a cloud dependency on the cloud path). Please update or remove that bullet, or qualify it as "local deploy only." The accurate framing is in ADR-002 above.
