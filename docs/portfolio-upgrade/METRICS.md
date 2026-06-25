# Product & Eval Metrics — 3GPP RAG Assistant

This document tracks the metrics that matter for this product — what was defined up front, what was actually measured, and what is still pending a run. Numbers are not inflated. Anything not yet run on the current index is marked `[RUN REQUIRED]`.

---

## Success criteria (defined before measuring)

These were the three criteria set before any eval was run, based on 10 user interviews with telecom engineers on the side project (see experience-library):

| Criterion | Target | Why |
|---|---|---|
| Retrieval accuracy | >80% pass rate on representative queries | Engineers need answers they can act on, not just related context |
| Response latency | <5s end-to-end on standard hardware | Matches the mental model of a fast colleague answering a question |
| Citation traceability | 100% of answers cite a source spec | Standards work requires verifiable references; an un-cited answer is not trusted |

Citation traceability is architectural (baked into the prompt and response schema), not measured as a metric. The other two are measured below.

---

## Current eval results

**Source file:** `data/eval_results.json`  
**Evaluated:** 2026-06-25 (full index)  
**Index size:** 43,121 chunks across 37 specs (local/API index; the hosted Streamlit demo loads a 41,429-chunk subset sized for free-tier deployment)  
**Dataset:** 30-query golden set (`data/eval/golden_set.jsonl`) — 25 in-corpus + 5 out-of-corpus refusal probes  
**Eval mode:** `full_eval: false` — retrieval only; answer block empty (LLM answer eval not run)  
**Reproduce with:** `python scripts/eval_retrieval.py --output data/eval_results.json`

### Retrieval metrics — in-corpus (N=25), standard IR

| Metric | Value | Notes |
|---|---|---|
| Hit-rate@5 | 0.88 | A relevant source appears in top-5 for 88% of queries |
| nDCG@5 | 0.723 | Rank-weighted; "GOOD" band |
| MRR | 0.679 | First relevant hit is high in the list on average |
| Recall@5 | 0.64 | Fraction of all expected source specs surfaced in top-5 |
| Avg context precision | 0.44 | Heuristic (source-level keyword); supplementary, not IR-standard |
| Avg context recall | 0.71 | Heuristic keyword coverage across top-3 |
| Legacy pass rate | 18/25 (72%) | Pass = keyword recall ≥0.5 AND avg cosine sim ≥0.50 |
| Avg cosine similarity | 0.557 | bge-small-en-v1.5 embedding space |
| Retrieve latency p50 / p95 | 0.021s / 0.048s | Apple M2, CPU only |

### Refusal axis — out-of-corpus probes (N=5)

| Metric | Value | Notes |
|---|---|---|
| Retrieval-refusal rate | 4/5 (80%) | Top-3 avg similarity correctly stays below the 0.50 threshold |
| Avg out-of-corpus similarity | 0.331 | vs 0.557 in-corpus — the system is measurably less confident on junk queries |
| LLM-judged refusal rate | `[RUN REQUIRED]` | Whether the generated answer actually declines — needs `--full` + live model |

**Reading these numbers honestly.** Hit-rate@5 (0.88) exceeds the legacy pass rate (0.72) because the legacy criterion also requires avg cosine similarity ≥0.50, which bge-small frequently misses even when the right document is retrieved. Of the 7 in-corpus queries below the legacy bar:

- **4 retrieve the correct source** (nDCG@5 = 1.0) and fail only on the similarity threshold: "What is gNB?" (sim 0.426), "What is HARQ in NR…?" (0.496), "What is the LTE X2 interface…?" (0.500), "What is SDAP…?" (0.462, with full keyword recall 1.0). These are threshold artifacts, not retrieval misses.
- **3 are genuine retrieval misses** (nDCG@5 = 0.0): "What is the E1 interface used for in 5G NG-RAN?", "…difference between SA and NSA 5G deployment options?", and "…differences between NR and LTE physical layer?" — all comparison/interface queries where the question phrasing diverges from spec terminology.

The two concrete improvement targets that follow: (a) recalibrate or learn the similarity threshold per embedding model so correctly-retrieved-but-low-similarity queries aren't penalized, and (b) query expansion / synonym handling for interface and comparison questions. Both are tracked in the roadmap.

### Answer quality metrics

Not run in the stored eval (requires a running LLM). The harness supports these via `--full`:

| Metric | Target | Status |
|---|---|---|
| Answer relevance (keyword match in response) | >70% | `[RUN REQUIRED]` |
| Faithfulness (grounding signal + context overlap) | >80% | `[RUN REQUIRED]` |
| Composite answer score (relevance 40% + faithfulness 40% + substantive 20%) | >0.70 | `[RUN REQUIRED]` |

Run with: `python scripts/eval_retrieval.py --full --output data/eval_results.json`

---

## Standard IR metrics — harness status

Recall@k, MRR, nDCG@k, and hit-rate are **implemented, unit-tested, and now measured on the full index** (see the in-corpus table above). They are wired into `scripts/eval_retrieval.py` and run as part of the standard eval path. The LLM-judge metrics remain `[RUN REQUIRED]` because they need a live model.

| Metric | Definition | Status |
|---|---|---|
| Recall@k (k=5) | Fraction of ground-truth source specs found in top-k results | Measured: **0.64** (in-corpus, N=25) |
| MRR (Mean Reciprocal Rank) | 1/rank of first relevant result, averaged across queries | Measured: **0.679** |
| nDCG@k (k=5) | Normalised Discounted Cumulative Gain at k (graded relevance) | Measured: **0.723** |
| Hit rate@k (k=5) | 1.0 if any relevant result in top-k, else 0.0; averaged | Measured: **0.88** |
| LLM-judge faithfulness | Judge model assesses whether each answer is grounded in retrieved context | Implemented in `scripts/eval/judge.py`; `[RUN REQUIRED]` (needs live LLM) |
| LLM-judge answer correctness | Judge model assesses factual accuracy within the context window | Implemented in `scripts/eval/judge.py`; `[RUN REQUIRED]` (needs live LLM) |
| Hallucination rate | Fraction of answers containing claims not traceable to retrieved context | Planned; not yet implemented |

See `EVAL_REPORT.md` §1 for the full metric definitions and limitations.

---

## System performance metrics

These are operational, not quality, metrics.

| Metric | Value | Notes |
|---|---|---|
| Index size | 43,121 chunks | 37 specs, latest version per spec (local/API index; cloud demo subset 41,429) |
| Supported specs | 37 | 5G NR RAN (19), LTE RAN (11), 5G Core (4), LTE Core (3) |
| Index build time | Not formally benchmarked | Single-spec rebuilds are fast; full rebuild is several hours on CPU |
| Cold start (cloud) | ~one-time 230 MB download | Vectordb shipped as GitHub Release asset |
| Retrieve latency p50 | 0.021s | See eval results (full-index, 30-query run) |
| Generate latency p50 (Groq) | `[RUN REQUIRED]` | Groq llama-3.3-70b; depends on response length and rate limits |
| Generate latency p50 (Ollama/llama3.2, CPU) | ~2–4s | Rough estimate from local testing; not formally benchmarked |
| End-to-end latency p50 | `[RUN REQUIRED]` | Retrieve + generate combined |

---

## Test coverage metrics

Source: `pytest --collect-only` (verified on `portfolio-upgrade` branch). 302 mocked tests collected excluding integration suite; 310 including 8 integration tests. No live services required for the mocked suite. In a clean environment all 302 pass; in a dev venv that has drifted to starlette ≥0.36 the 35 FastAPI route tests error on a known `on_startup` incompatibility, which `requirements.txt` pins out (`starlette>=0.35,<0.36`).

| Test module | Tests |
|---|---|
| `test_eval_metrics.py` | 103 |
| `test_api.py` | 30 |
| `test_retriever.py` | 16 |
| `test_rag_chain.py` | 14 |
| `test_embeddings.py` | 12 |
| `test_vector_store.py` | 11 |
| `test_llm.py` | 9 |
| Other unit suites (`test_corpus_config`, `test_document_processor`, `test_spec_catalog`, `test_config`, eval endpoint, …) | 107 |
| **Total (mocked, excl. integration)** | **302** |
| **Total (incl. 8 integration tests)** | **310** |

Coverage is measured per source module and reported by CI (Codecov); see the workflow badge.

**Run with (mocked suite, 302 tests):** `pytest tests/ --ignore=tests/test_integration.py --cov=src --cov-report=term-missing`

---

## Notes on methodology

**Context precision** in the current harness is defined as: fraction of retrieved chunks whose source filename matches the expected source document for that query. It is not semantic precision — it's source-level precision. This is stricter than "somewhat related" but looser than "the exact clause that answers the question."

**Context recall** is defined as: fraction of expected keywords (manually specified per query in the eval set) found anywhere across the top-3 retrieved chunks. This is a heuristic, not a gold-standard recall measure. It depends on keyword choice, which is manual.

Both heuristic metrics are honest proxies for a harder measurement, kept as supplementary signals alongside the standard IR metrics. The standard IR view (hit-rate@5 0.88, nDCG@5 0.723) is the primary read; the heuristic context precision (0.44) is deliberately strict (source-filename match) and runs lower. An LLM-judge eval would give a more reliable picture of whether answers are actually useful — it stays `[RUN REQUIRED]` pending a live model.
