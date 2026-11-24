# Architecture Decision Records — 3GPP RAG Assistant

Real decisions made during the build (ADR-001 through ADR-007) and the Phase 2 work (ADR-008 through ADR-011). Each traces directly to code or to the owner's experience, with no invented outcomes.

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

Indexed 43,121 chunks across 37 specs. The full-index eval (2026-06-25, 25 in-corpus queries) shows hit-rate@5 0.88 and Recall@5 0.64 — the system surfaces a relevant source for most queries, but multi-spec recall lags (it often returns one of two expected specs). The genuine misses cluster on comparison/interface queries (E1, SA-vs-NSA, NR-vs-LTE PHY) where the question phrasing diverges from spec terminology — a recall/phrasing problem, not a precision error.

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

The live Streamlit Cloud app runs Groq llama-3.3-70b-versatile. Local installs default to Ollama. (2026-10: Groq shut down llama-3.3-70b-versatile for free/dev tiers on 2026-08-16; the cloud path moved to `openai/gpt-oss-120b`, Groq's recommended replacement, with `reasoning_effort=low` so reasoning tokens don't consume the answer budget.) The dual-path architecture is real and working; neither path was invented.

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

`bge-small` is the default for both local and cloud paths. Eval average cosine similarity is 0.557 across the 25 in-corpus queries (2026-06-25) — note bge-small runs cool, which is why the legacy 0.50 similarity threshold under-passes some correctly-retrieved queries (see EVAL_REPORT §6.2). The cloud deploy uses ChromaDB's built-in ONNX embedding path (see ADR-005), which bypasses the Python sentence-transformers model entirely.

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

43,121 chunks from 37 specs at this chunk size. The full-index eval latency at p50 is 0.021s for retrieval (2026-06-25, p95 0.048s), comfortably within budget. No individual case shows retrieval latency above ~0.05s once the embedding model is warm.

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

37 specs indexed, one file per spec (the latest available download). 43,121 chunks. The dedup logic is exercised through the eval test suite and the index build output.

---

## ADR-009: Query-time vocabulary expansion via rank fusion

**Status:** Decided  
**Date:** 2026-07-02 (Phase 2, Track B)  
**Context source:** `src/core/query_expansion.py`; `src/core/retriever.py` (`_rrf_merge`, `_search`); eval finding F2 in `docs/PHASE2.md` §2

### Context

The Phase 1 eval's three genuine retrieval misses (E1 interface, SA-vs-NSA, NR-vs-LTE physical layer) share one root cause: the question's phrasing diverges from spec terminology, so the raw query embedding lands far from the defining chunks. The fix candidates all involve injecting standard 3GPP vocabulary (from TR 21.905 and the specs' own abbreviation clauses) into retrieval.

### Options considered

| Option | Measured / expected effect |
|---|---|
| No expansion (baseline) | Hit-rate@5 0.88, Recall@5 0.64; the miss cluster stays |
| Replace the query with its expanded form | **Measured regression:** fixed E1 (nDCG 0 → 1.0) but hit-rate@5 fell 0.88 → 0.80, Recall@5 0.64 → 0.57, nDCG@5 0.723 → 0.641 — the gloss shifts embeddings of previously-healthy queries |
| Fuse raw + expanded rankings (RRF) | **Measured improvement:** hit-rate@5 held at 0.88, Recall@5 0.64 → 0.683, MRR 0.679 → 0.697, nDCG@5 0.723 → 0.718 (−0.005, within tolerance); E1 fixed (hit-rate 1.0) |
| Index-time enrichment (expand chunks, not queries) | Requires a full 43K-chunk re-index per vocabulary change; not measured |

### Decision

Reciprocal Rank Fusion of the raw-query and expanded-query rankings (`k_const=60`), config-gated by `query_expansion` (default on). Queries containing no known abbreviations skip the second search entirely. The vocabulary is a general-purpose abbreviation table applied uniformly to every query — deliberately not tuned per eval case — and the decision between replace and fusion was made by the eval harness, not by intuition: replace-mode's regression was measured and rejected before fusion was built.

### Tradeoff accepted

Expansion queries run two embed+search passes, roughly tripling retrieval latency (p50 ~0.02s → ~0.07s) — still two orders of magnitude below generation latency. Under fusion, a result list mixes cosine similarities computed against two different query embeddings, which makes the similarity-based legacy pass criterion noisier (one more reason the standard IR metrics are primary). The cloud Streamlit app now runs the same fusion via a shared module (ADR-011), though its ONNX embedding space was not separately evaluated.

### Outcome

Recall@5 0.683 (from 0.64) with hit-rate maintained and the regression gate green; E1 recovered. The two remaining misses (SA-vs-NSA, NR-vs-LTE PHY) are comparison queries — a single embedding cannot serve both sides of a "difference between X and Y" question — and are the target of the multi-spec decomposition work (M9 remainder, `docs/PHASE2.md` Track B item 3).

---

## ADR-010: Comparison-query decomposition with side-aware slot allocation

**Status:** Decided  
**Date:** 2026-07-03 (Phase 2, Track B / M9)  
**Context source:** `src/core/query_decomposition.py`; `src/core/retriever.py` (`_interleave_sides`, `_cap_per_source`); ADR-009 outcome

### Context

After expansion fusion (ADR-009), the two surviving retrieval misses (SA-vs-NSA, NR-vs-LTE physical layer) were both comparison questions. Two mechanisms failed them in measurably different ways: a single query embedding averages both sides of a "difference between X and Y" question and lands near neither; and RRF — correct for merging rewrites of one intent — rewards consensus across lists, so per-side evidence that appears in only one sub-query's list always loses to consensus noise (measured: adding decomposed sub-queries to the global RRF merge left both misses at hit-rate 0).

### Options considered

| Option | Measured / expected effect |
|---|---|
| Global RRF over raw + expanded + sub-queries | **Measured: no effect** — both comparison misses stay at hit-rate 0; consensus bias buries single-list evidence |
| Side-aware allocation: per-side raw+expanded fusion, per-source dedup within each side, round-robin slots across sides, base ranking as backfill | **Measured improvement:** hit-rate@5 0.88 → 0.96, Recall@5 0.683 → 0.737, MRR 0.697 → 0.720, nDCG@5 0.718 → 0.755; SA-vs-NSA fully recovered; NR-vs-LTE reaches hit-rate 1.0 (recall 1/3) |
| Expanded-only side searches | **Measured regression during development:** the expanded side text pushed the relevant spec out of the side's own top-10 — sides now fuse raw + expanded, the same never-discard-the-raw rule as ADR-009 |

### Decision

Decomposition is gated on explicit comparison wording (differ/compare/vs/versus) — bare "between" is deliberately excluded because interface questions ("the F1 interface between gNB-CU and gNB-DU") use it without being comparisons. Each side is searched raw and vocabulary-expanded and RRF-fused; each side's list is deduplicated to one chunk per source; top-k slots are allocated round-robin across sides with the fused base ranking as backfill. Non-comparison multi-spec queries get a per-source cap (max 3 chunks per source in a fused top-5) instead. All config-gated (`query_decomposition`, default on).

### Tradeoff accepted

Comparison queries run up to six embed+search passes. Side extraction is a regex heuristic (single-token right side; tails can read awkwardly) — documented in the module. The per-source-dedup-within-sides rule assumes a comparison wants breadth across specs, which is right for the observed cases but untested beyond them.

### Outcome

Recall@5 0.737 against the M9 target of ≥ 0.80. The honest residual, established by direct probing rather than assumed: "NR physical layer" cannot surface TS 38.211 in its own top-12 — the embedding model ranks sibling PHY specs (38.212–38.215) above the labeled definitional spec. That is an embedding-resolution limit, not a query-mechanics problem; the named next lever is the bge-base upgrade already designated in ADR-003 (requires a full index rebuild), plus graded-relevance label review for comparison queries.

---

## ADR-008: Version-aware indexing (release intelligence)

**Status:** Proposed — gated on user-hypothesis validation (see PHASE2.md Track C)  
**Date:** drafted 2026-07-03 (Phase 2, Track C groundwork)  
**Context source:** `docs/PHASE2.md` §Track C; ADR-007 (which this would supersede); `src/core/spec_catalog.py` (`infer_release_from_filename`)

*(File order is chronological; ADR numbers follow the assignment in PHASE2.md §8.)*

### Context

ADR-007 dedupes to the latest version per spec at index time, which prevents cross-release contradictions but makes "what changed between Rel-17 and Rel-18?" unanswerable — a question practicing engineers face at every release cycle (hypothesis H1, unvalidated). Answering it requires retaining multiple releases per spec with release metadata, plus Change Request data for the "why."

### Proposal

1. Retain the last N releases per spec (starting with 2–3 releases of flagship specs: 38.300, 38.331, 23.501) with `release` chunk metadata, reversing ADR-007's dedup for those specs only.
2. Ingest Change Request metadata (portal exports; `-cl` companion files currently skipped by `_SKIP_SUFFIXES`).
3. Release filter in retrieval; a delta-answer prompt path citing spec version and CR number; a release-delta golden-set axis.

### Groundwork already landed (ungated)

`infer_release_from_filename()` parses the release from the archive filename's version suffix (h30 → Rel-17), and `build_index.py` now stores `release` in chunk metadata — effective at the next index rebuild. This improves citations regardless of whether the full proposal proceeds.

### Gate

Implementation starts only after H1 is validated in structured conversations with practicing RAN/Core engineers (PHASE2.md §Track C). If H1 fails, M10 is re-scoped before any multi-release indexing work begins.

### Tradeoffs to accept if adopted

Index grows roughly linearly with retained releases (storage, build time, possibly latency); cross-release retrieval must not reintroduce the contradictory-answers problem ADR-007 solved — the release filter must default to latest-only unless the query asks for a delta.

---

## ADR-011: Shared retrieval-fusion module across both deploy paths

**Status:** Decided
**Date:** 2026-07-03 (Phase 2, Track B follow-up)
**Context source:** `src/core/retrieval_fusion.py`; `src/core/retriever.py`; `streamlit_app.py`

### Context

The Track B retrieval improvements (query-expansion fusion in ADR-009, comparison decomposition in ADR-010) were built into `DocumentRetriever`, which the local/API path uses. The public Streamlit Cloud app (`streamlit_app.py`) is a self-contained file with its own `retrieve()` — deliberately standalone so Streamlit Cloud never imports torch/sentence-transformers (ADR-005). So the live demo, the URL most people actually click, was serving none of the Track B work. That is the wrong artifact to leave stale.

### Options considered

| Option | Assessment |
|---|---|
| Leave the cloud app as-is | Rejected — the live demo is the primary shopfront; it should reflect the work |
| Copy the fusion logic into `streamlit_app.py` | Works, but duplicated logic diverges; two implementations to keep in sync |
| Import `DocumentRetriever` in the cloud app | Rejected — it pulls sentence-transformers/torch, which the cloud tier deliberately excludes |
| Extract the fusion orchestration into a pure-stdlib module both paths import | Chosen — single source of truth, no heavy-dependency leak |

### Decision

Extract the rank-fusion primitives and the query-rewriting orchestration into `src/core/retrieval_fusion.py`, which imports only stdlib plus the two pure-stdlib rewriter modules. It drives any backend through a `search_fn(text, n)` callback. `DocumentRetriever` now delegates to it via a closure over its bge-small search; `streamlit_app.py` delegates via a closure over its ONNX ChromaDB search. The import chain was verified to pull in no torch/pydantic/chromadb, so the cloud tier stays lean; the import is also guarded so the app degrades to single-search retrieval rather than failing to start if the package is ever unavailable.

### Tradeoff accepted — the honest caveat

The fusion *mechanics* are embedding-agnostic and transfer, but the *measured quality gains* do not: every golden-set number in this repo (hit-rate 0.96, Recall@5 0.737) was measured on the local **bge-small** index. The cloud app embeds with ChromaDB's built-in **ONNX (all-MiniLM)** model — a different vector space — and there is no eval harness for that path. So the cloud app now *runs* the same query rewriting, but its improvement is **unmeasured**, and the tuned bge-small constants (the 0.42 legacy-pass threshold) are intentionally not applied to it. Two further gaps remain the user's action, not code: the cloud vectordb is a pre-built GitHub Release tarball, so (a) the new `release` chunk metadata (ADR-008 groundwork) and (b) any re-embedded index appear only after a local rebuild and re-upload of that asset.

### Outcome

The refactor is behavior-preserving on the local path — the full eval reproduced every retrieval metric exactly (regression gate green), and the mocked suite stays green (373 tests). The cloud `retrieve()` was verified end-to-end against a fake collection: expansion and decomposition fire, and the raw query is never discarded.

---

## ADR-012: Hybrid BM25 + dense retrieval on; cross-encoder reranker available but off

**Status:** Decided
**Date:** 2026-11-19 (Sprint 1 — retrieval upgrades, M9)
**Context source:** `src/core/bm25.py`; `src/core/reranker.py`; `src/core/retriever.py`; `src/core/retrieval_fusion.py`; `data/eval/ablation.json`

### Context

Dense bge-small retrieval blurs exact identifiers — message names (`RRCReconfiguration`), timers (`T310`), interfaces (`X2`, `N2`), clause numbers — into topical neighbourhoods. Recall@5 had plateaued below the M9 target of 0.80. Two standard levers were untested here: lexical (BM25) retrieval fused with dense, and a cross-encoder reranking stage.

### Options considered

| Option | Assessment |
|---|---|
| `rank_bm25` / Elasticsearch / Chroma full-text | Rejected — new dependency or service; the Streamlit Cloud path must stay torch-free and lean (ADR-005, ADR-011) |
| Pure-stdlib BM25 built from the ChromaDB collection at first use | Chosen — no second artifact to ship, identifier-preserving tokenizer, `array`-backed postings keep 44k chunks in tens of MB |
| Weighted score fusion (α·dense + (1−α)·BM25) | Rejected — needs score normalization and a tuned α; RRF is rank-based and already used here (ADR-009) |
| RRF of dense and BM25 rankings inside the `search_fn` | Chosen — composes with expansion and decomposition unchanged |
| Reranker: `bge-reranker-base` (1.1 GB) vs `ms-marco-MiniLM-L-6-v2` (90 MB) | MiniLM chosen for CPU latency; bge-reranker left as an untested upgrade |

### Decision

- **Hybrid on by default** (`settings.hybrid_search = True`). Each `search_fn` call fuses the dense and BM25 top-n via RRF. Chunks only BM25 found get their `similarity` computed from their stored embedding in the collection's own metric, so the refusal and calibrated-pass thresholds keep their meaning.
- **Reranker off by default** (`settings.rerank = False`), exposed via `fused_retrieve(rerank_fn=…)`. When enabled it reorders a 20-deep candidate pool and is skipped for comparison queries (one score over the whole question would undo ADR-010's per-side slot allocation).

### Evidence (ablation, same rebuilt index, 25 in-corpus + 5 OOC queries)

| Variant | Hit@5 | Recall@5 | MRR | nDCG@5 | OOC refusal | p50 |
|---|---|---|---|---|---|---|
| dense + Track B (previous default) | 0.840 | 0.663 | 0.630 | 0.664 | 4/5 | 51 ms |
| **+ BM25 hybrid (new default)** | **0.960** | **0.710** | 0.621 | 0.698 | **5/5** | 64 ms |
| + rerank, no BM25 | 0.920 | 0.657 | 0.685 | 0.723 | 4/5 | 520 ms |
| + BM25 hybrid + rerank | 0.920 | 0.677 | **0.727** | **0.762** | 4/5 | 527 ms |

Hybrid fixes four queries (beam management, dual connectivity, X2, SSB) and loses one (NG-RAN logical nodes). The reranker gives the best ordering but drops three of hybrid's recall gains. It's an MS MARCO web-search model with no telecom vocabulary.

### Tradeoff accepted

- **Recall over ordering.** The generator reads all top-5 chunks, so getting the right evidence into the top 5 matters more than its rank. MRR dips 0.009 with hybrid.
- **N = 25.** One query moves hit-rate by 0.04. The hybrid gain is 4 fixed vs 1 broken: directional, not statistically established.
- **Cold start.** The BM25 index is built in-process on first hybrid query (seconds, then cached per collection count).
- **Cloud path not yet hybrid.** `streamlit_app.py` still runs dense-only. `bm25.py` is stdlib-only so it can be wired in, but that path has no eval harness (ADR-011 caveat).

### Outcome

M9's Recall@5 ≥ 0.80 target is still not met (0.710). Remaining levers: a telecom-aware or larger reranker (bge-reranker-base), the bge-base rebuild (ADR-003), and graded-relevance label review. The rebuilt index uses the latest spec versions (44,133 chunks vs 43,121), and the previous default scores lower on it than on the old index. The regression baseline was therefore re-saved on the rebuilt index with the hybrid default (2026-11-20: hit-rate@5 0.96, Recall@5 0.71, MRR 0.621, nDCG@5 0.698). It reproduced exactly on a second run, and the gate is green.

---

## ADR-013: Claim-level citations with a cheap grounding check; LLM judges must be calibrated

**Status:** Decided
**Date:** 2026-11-20 (Sprint 4 — trustworthy answers)
**Context source:** `src/core/grounding.py`; `src/core/rag_chain.py`; `scripts/eval/claim_judge.py`; `scripts/eval/agreement.py`; `docs/EVAL_REPORT.md` §6b

### Context

Answer-level faithfulness ("0.64") cannot tell a reader *which* sentence to doubt. The judge behind that number was also measured on truncated input (200-char answers, 400-char chunks).

### Options considered

| Option | Assessment |
|---|---|
| NLI entailment model per claim | Most principled; needs another model download and CPU latency per sentence. Deferred |
| LLM claim judge in the request path | Catches entity swaps, but adds an LLM call per sentence. Kept for offline eval only |
| Embedding + lexical similarity against the cited chunk | Chosen for the request path: reuses bge-small, deterministic, about 0.1 s per answer |

### Decision

- **Citation format.** The prompt asks for `[Dn]` markers. 3GPP chunks contain their own `[17]`-style reference markers, and models copy them, so a distinct marker avoids the collision.
- **Grounding report.** `GroundingChecker` splits the answer into claims, ignores hedges about the context, and reports grounded ratio, citation coverage, citation precision and invalid citations. The API returns it, and the local UI shows a grounding meter with the sentences to check.
- **Offline validation.** An LLM claim judge (`claim_judge.py`) checks the cheap checker. Human scoring (`agreement.py`) calibrates the answer-level judge.

### Tradeoff accepted

- **Similarity is not entailment.** The checker passes fluent wrong-entity sentences built from context wording. Measured agreement with an LLM claim judge is κ = 0.215, so the UI wording says "matches a retrieved source", never "verified".
- **The local judge is lenient.** `gemma3:4b` gave 19 of 25 answers perfect scores, including two factually wrong ones. Judge scores are not published as quality until human κ is measured.
- **Coverage gaps.** The cloud Streamlit app does not run the checker; it has no bge-small. The streaming endpoint sends the report as a final `grounding` event.

### Outcome

Grounded ratio is 0.866, citation coverage 0.685 and citation precision 0.882 over 157 claims, with 1 invalid citation. The judge-input fix moves the same judge from 0.79 to 0.90 on faithfulness for the same answers. Human calibration is ready to run (20-answer blind sheet). Open items:
- human κ
- an NLI or claim-judge check for entity substitution
- judging the cloud path (needs a Groq key)
- reviewing the 73 golden-set candidates

---

## ADR-014: Conversational retrieval and clause-aware chunks

**Status:** Decided
**Date:** 2026-11-23 (Sprint 2 — conversational and structure-aware RAG)
**Context source:** `src/core/query_rewriter.py`; `src/core/clause_chunker.py`; `src/core/retriever.py` (`expand_to_clauses`); `scripts/build_index_clauses.py`; `scripts/eval/multiturn_eval.py`; `docs/EVAL_REPORT.md` §6c

### Context

Two structural gaps limited answers:

- **Retrieval ignored the conversation.** History went to the LLM, but the search used only the latest message. "Which protocol runs on its control plane?" after a question about F1 searched for "its control plane".
- **Chunks ignored the document.** The fixed-size chunker collapsed each spec to one string, appended every table at the end of the file and cut 1000-character windows. A chunk did not know its clause, could straddle two clauses, and table rows were detached from the text that introduces them. Citations could only name a file.

### Options considered

| Option | Assessment |
|---|---|
| Always send history + question to retrieval | No LLM call, but long assistant turns drown the follow-up in the embedding. Kept as the fallback (previous *user* turn only) |
| LLM rewrite of every turn | Simple, but adds an LLM call to every first question for no gain |
| Gated LLM rewrite (chosen) | Rewrite only when there is history and the question has anaphora / ellipsis or is very short; fall back to "previous question + follow-up" if the LLM fails |
| Structure-aware chunking with LLM-written context (Anthropic "contextual retrieval") | Best reported gains, but one LLM call per chunk: ~50k calls on a local model is days of CPU |
| Clause chunks with a structural header (chosen) | DOCX heading styles give exact clause numbers and titles; the header (spec, title, clause breadcrumb) is free to build |

### Decision

- **Follow-up rewriting.** `QueryRewriter` turns a follow-up plus the last turns into one standalone search query. Only retrieval sees it; the answer prompt keeps the user's wording. The API returns `search_query`, the stream's `sources` event carries it, and the UI shows "Searched for: …" when it differs from the question.
- **Clause chunks.** `clause_chunker` walks the DOCX body in order (tables in place), splits at heading paragraphs, never crosses a clause boundary, and stores `clause`, `clause_title`, `clause_path`, `section_id`, `part`/`n_parts`. Sources and the LLM context cite "TS 38.401 §8.4.1.1".
- **Contextual header.** Each chunk's embedded and BM25-indexed text starts with `TS <spec> (<title>) §<clause>: <breadcrumb>`. `header_len` lets callers strip it.
- **One chunk per clause.** When the top-k holds two parts of the same clause, retrieval keeps the best one and refills from a deeper list (`section_dedupe`).
- **Small-to-big.** Retrieval ranks the small parts; `expand_to_clauses` hands the LLM the whole clause (up to 3000 characters, windowed around the hit), merging parts of the same clause.
- **Separate collection.** The clause index lives in `3gpp_clauses`; `3gpp_specs` stays. `COLLECTION_NAME` selects the served index and `--collection` the evaluated one.

### Tradeoff accepted

- **DOCX only.** Clause detection relies on heading styles; PDFs and legacy `.doc` still use the fixed-size chunker. All 37 indexed specs are DOCX.
- **Rewrite costs an LLM call** on follow-ups (about 1–2 s on llama3.2 locally) and can drift; the gate skips self-contained questions.
- **The golden set scores retrieval at spec level.** It cannot see clause-level precision, which is the main reason for clause chunks; clause-level labels are future work.
- **Ollama context.** Whole-clause context needs a larger window, so `OllamaLLM` now requests `num_ctx=8192`.
- **Per-clause dedupe was tuned on the eval set.** It was added after seeing duplicate parts in the top 5, so its gain (Recall@5 0.677 → 0.737) is in-sample.

### Outcome

Follow-ups: on 10 multi-turn cases, LLM rewriting raises Recall@5 from 0.483 to 0.767 on the fixed index, and Hit@5 from 0.60 to 1.00. Chunking (default pipeline, 25 in-corpus queries): clause chunks with headers and per-clause dedupe reach Recall@5 0.737, MRR 0.750 and nDCG@5 0.756, against 0.710 / 0.621 / 0.698 for fixed chunks. Hit@5 is 0.92 against 0.96, one query. Without the header, clause chunks are worse than fixed chunks (MRR 0.616), so the header is not optional. The served default stays `3gpp_specs` until answer-level evaluation on the clause index and a new regression baseline and cloud release exist. Open items:
- clause-level relevance labels
- an answer and grounding run with small-to-big context
- switching the default collection
- the cloud path (no rewrite, fixed chunks)

---
