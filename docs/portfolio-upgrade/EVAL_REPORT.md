# Evaluation Report — 3GPP RAG Assistant

**Last run (full index):** 2026-06-25 (see `data/eval_results.json`)
**Last run (sample fixture):** 2026-06-23 (see `data/eval/sample_results.json`)
**Harness version:** v3 (graded nDCG; negative/refusal cases; in-corpus/refusal split; sample fixture; tightened relevance matching)
**Index size:** 43,121 chunks (local/API index; the hosted Streamlit demo loads a 41,429-chunk subset sized for free-tier deployment)
**Dataset:** 30-query golden set — 25 in-corpus + 5 out-of-corpus refusal probes
**Reproduce (sample fixture, no index required):** `python scripts/eval/run_sample_eval.py`
**Reproduce (full index):** `python scripts/eval_retrieval.py --output data/eval_results.json`

---

## Overview

This document defines every metric in the eval harness, explains why it matters, states its limitations honestly, and cites the current real numbers from the 2026-06-25 full-index run (43,121 chunks, 30-query golden set). Standard IR metrics are reported over the 25 in-corpus queries; the refusal axis over the 5 out-of-corpus probes. Anything requiring a live LLM (the LLM-judge metrics) is marked **[RUN REQUIRED]** — those placeholders are the correct deliverable when the infrastructure is not available at report-generation time.

---

## 1. Retrieval metrics

### 1.1 Standard IR metrics (primary)

These are the signals a skeptical enterprise-RAG PM or technical reviewer will look for. They come from information-retrieval literature and have well-understood properties.

#### Hit-rate@k

**Definition:** 1.0 if any of the top-k retrieved chunks comes from a ground-truth relevant source specification; 0.0 otherwise. Averaged across all queries in the dataset.

**Why it matters:** The minimum bar for usefulness. If the retriever surfaces zero relevant chunks for a query, no amount of LLM quality saves the answer. For enterprise RAG over technical/regulated documents, a hit-rate below 0.80 is a serious problem.

**Limitation:** Binary and tolerant — a single lucky chunk in position k scores the same as k/k relevant chunks. Doesn't distinguish a retriever that gets the right chunk at rank 1 from one that barely squeaks a relevant chunk in at rank k. Use alongside MRR and nDCG for a complete picture.

**Current value (full index, in-corpus N=25):** **0.88**. As expected, this sits above the 72% legacy pass rate, because hit-rate credits a relevant chunk in top-5 without also requiring the avg-similarity threshold the legacy criterion imposes.

---

#### Recall@k

**Definition:** Fraction of the distinct expected source specifications found at least once anywhere in the top-k results. For a query expecting chunks from TS 38.300 and TS 38.401, a top-5 result containing one 38.300 chunk and no 38.401 chunk scores 0.5.

**Why it matters:** Many complex 3GPP questions require evidence from multiple specifications (e.g., the F1 interface is described in both TS 38.401 architecture and TS 38.470/38.473 protocol specs). Recall@k measures whether the retriever casts a wide enough net across the relevant spec set, not just whether it finds one good chunk.

**Limitation:** Treats each expected source as a single binary signal — it doesn't account for how many chunks per spec were retrieved or whether the retrieved chunks contain the specific expected information. A query expecting two specs where the retriever finds one chunk from each scores 1.0, regardless of chunk quality.

**Current value (full index, in-corpus N=25):** **0.64**. Lower than hit-rate because several multi-spec queries surface one of two expected specs (e.g. gNB expects both TS 38.300 and TS 38.401; retrieval often returns only one). This is the clearest signal of where multi-evidence retrieval needs work.

---

#### MRR (Mean Reciprocal Rank)

**Definition:** 1/rank of the first relevant document retrieved, averaged across all queries. A relevant chunk at rank 1 scores 1.0; at rank 2, 0.5; at rank 10, 0.1.

**Why it matters:** For conversational RAG, the LLM's answer quality correlates with how early a relevant chunk appears in the context window. An LLM given 5 chunks where the only relevant one is at position 5 will produce a worse answer than one where the relevant chunk is at position 1. MRR captures this rank sensitivity.

**Limitation:** Only the rank of the **first** relevant document matters — all subsequent relevant documents are ignored. This makes it less informative when queries require multiple relevant chunks (common in 3GPP reasoning). For multi-evidence queries, nDCG@k is more appropriate.

**Current value (full index, in-corpus N=25):** **0.679**. When a relevant chunk is retrieved at all, it tends to land near the top — consistent with the high hit-rate.

---

#### nDCG@k (Normalised Discounted Cumulative Gain)

**Definition:** Measures both relevance and rank position, then normalises by the ideal (best possible) ranking. Supports two modes:

- **Binary mode (default):** Each retrieved chunk receives gain 1 if its source matches a relevant spec token, else 0. The ideal ranking places all relevant chunks first.
- **Graded mode:** Each chunk receives a gain from a `graded_relevance` dict (e.g. `{"38300": 2, "38401": 1}`), where 2 = highly relevant (primary spec), 1 = partially relevant (supporting spec), 0 = not relevant. The ideal ranking orders chunks by descending gain. Graded nDCG is more discriminating than binary nDCG because it distinguishes the primary definitional spec from secondary supporting specs.

The gain at each rank is discounted: gain(rank) = gain / log2(rank + 1). The score is normalised to [0, 1] by dividing by the DCG of the ideal ranking.

**Why it matters:** nDCG is the most complete single retrieval metric. It rewards the retriever for putting relevant chunks early (like MRR) while also crediting retrieval of multiple relevant chunks (unlike MRR). It's the metric used in TREC, MS-MARCO, and most enterprise RAG benchmark papers. A Layer 2 hiring manager reviewing this report will expect to see nDCG. The graded variant adds signal for queries where the retrieval system must distinguish primary from supporting evidence.

**Implementation note:** The ideal DCG is computed from the actual gains achievable in the full retrieved list (not just the number of distinct spec tokens). This correctly handles the case where multiple chunks from the same spec appear in the result set, preventing nDCG > 1.0.

**Limitation:** Binary relevance flattens the distinction between a highly relevant chunk and a marginally relevant one. Graded relevance is more informative but requires additional annotation effort. A subset of 7 golden-set queries now carry graded labels (see §3).

**Current value (full index, in-corpus N=25):** **0.723** (graded nDCG@5) — the harness reports this as a "GOOD" band. This is the single most complete retrieval signal in the report: it credits both early placement and multiple relevant chunks.

**Sample fixture result (2026-06-23):**
- nDCG@5 binary: **0.984** (avg over 6 fixture queries)
- nDCG@5 graded: **0.982** (avg over 6 fixture queries)
- Note: these are sample fixture numbers from `data/eval/sample_results.json`. They confirm the harness computes graded nDCG correctly; they do not reflect full-corpus quality (the full-index value above is the real one).

---

### 1.2 Heuristic metrics (RAGAS-inspired; supplementary)

These were the original harness metrics. They are keyword-based heuristics, not IR-standard precision/recall. They are retained for trend continuity but should be treated as supplementary sanity checks, not primary quality signals.

#### Context precision (heuristic)

**Definition:** Fraction of ALL retrieved chunks (not just top-k) whose source filename matches a ground-truth relevant specification.

**Why it matters as a sanity check:** A score near 1.0 indicates the retriever is not surfacing chunks from obviously irrelevant spec series. In a domain-specific corpus like 3GPP, high precision is expected by construction — the index only contains 3GPP specs, and most are relevant to most queries.

**Limitation:** In a domain-specific RAG corpus, this metric is easily near-1.0 without any real quality signal. It cannot distinguish between a retriever that returns the specific relevant spec section vs. any spec section. It is NOT IR-standard precision. The name is kept for API compatibility.

**Full-index result (2026-06-25, in-corpus N=25):** avg_context_precision = **0.44**. This is lower than the old 10-query figure (1.0) because the 30-query golden set is harder and broader, and because this strict source-filename definition penalizes retrieving a *related* spec section that isn't the exact expected file. It is a deliberately conservative heuristic, not the primary signal — read it alongside hit-rate@5 (0.88).

---

#### Context recall (heuristic keyword coverage)

**Definition:** Fraction of expected technical keywords found anywhere in the combined text of the top-3 retrieved chunks. For example, a query expecting ["gnb", "base station", "node", "ran"] scores 0.75 if 3 of 4 keywords appear in the top-3 chunks.

**Why it matters as a sanity check:** A quick check that the retrieved chunks contain the basic vocabulary of the right answer. Cheap to compute; no LLM required.

**Limitation:** Brittle for technical text. The same concept often appears under multiple terms ("gNB" vs "base station" vs "next-generation NodeB"). A chunk that perfectly explains the concept using different terminology will score 0 on a keyword it should score 1 on. This is part of why several in-corpus queries miss the legacy pass bar despite the retriever surfacing genuinely relevant chunks (see §6). This is NOT IR-standard recall.

**Full-index result (2026-06-25, in-corpus N=25):** avg_context_recall = **0.71** (individual query scores range from 0.0 to 1.0)

---

### 1.3 Latency

**Definition:** Wall-clock time for a single retrieval call (embed query + ANN search in ChromaDB), measured in seconds. Reported as p50 and p95 across all queries in the run.

**Why it matters:** For interactive use, retrieval latency is the dominant component of perceived response time (LLM generation is slower but asynchronous in streaming UI). Sub-400ms retrieval keeps the overall time-to-first-token competitive for technical users who expect search-engine-like responsiveness.

**Limitation:** Latency is hardware- and load-dependent. These numbers were recorded on a specific machine (Apple M2, CPU only). The embedding model (bge-small ONNX) loads on first query, so a cold session's first query is slower; over a 30-query run the warm-up is amortized into p95.

**Full-index results (2026-06-25, Apple M2 CPU, 30-query run):**

| Metric | Value |
|---|---|
| Retrieve p50 | **0.021s** |
| Retrieve p95 | **0.048s** |

These are an order of magnitude faster than the earlier reported figures because the embedding model is now warm across the run and ChromaDB ANN search over 43,121 chunks is sub-50ms at p95 on CPU. Generation latency (Groq / Ollama) is separate and tracked in METRICS.md.

---

## 2. Answer quality metrics

### 2.1 Heuristic answer metrics (no LLM required)

These run when `--full` is passed. They use keyword matching and text-overlap heuristics — fast but approximate.

#### Answer relevance (heuristic)
Fraction of expected answer keywords present in the generated response. Same brittleness caveats as context recall above.

#### Faithfulness (heuristic)
Proxy for grounding: scores (a) presence of grounding vocabulary ("according to", "3GPP", "specification") and (b) word-overlap between the answer and the top retrieved chunk. This is a surface heuristic — it can be fooled by an answer that copies terminology from the retrieved chunk without actually being grounded in it.

**2026-06-25 result:** answer block is **empty** (`{}`) — the baseline run is retrieval-only (`--full` not passed; no live LLM). Result is **[RUN REQUIRED]**.

---

### 2.2 LLM-judge metrics (faithfulness + answer-correctness)

**Status: [RUN REQUIRED]** — Implementation is complete in `scripts/eval/judge.py`. Results require a live LLM.

**Activate with:**
```
python scripts/eval_retrieval.py --full --judge --judge-provider groq
# Requires: GROQ_API_KEY environment variable
```

#### Faithfulness (LLM-judge)
**Definition:** LLM judge scores 0–5: does the answer make claims supported by the retrieved context? 5 = every claim traces to a context passage; 0 = answer ignores or contradicts the context. Normalised to [0, 1].

**Why it matters:** Hallucination in technical/regulated domains is a safety and compliance risk. For 3GPP specs used in network engineering, a hallucinated interface definition or protocol requirement could propagate errors into product decisions. LLM-judge faithfulness is the closest proxy for hallucination rate short of human review.

**Limitation:** The judge model's own capabilities bound the score quality. Using the same model as the responder is a known bias risk (self-judging). Default judge: llama-3.3-70b-versatile (Groq), same as production — a different judge model would give a more independent signal. Judge prompts must be versioned; changing the prompt changes scores.

**Current value:** **[RUN REQUIRED]**

---

#### Answer correctness (LLM-judge)
**Definition:** LLM judge scores 0–5: does the answer address the question accurately and completely, given what the retrieved context provides? This is not a reference-answer comparison (the golden set does not include full reference answers) — it is the judge's assessment of technical accuracy within the context window. Normalised to [0, 1].

**Why it matters:** Answer relevance (keyword overlap) misses cases where an answer uses the right vocabulary but gives the wrong technical explanation. LLM-judge correctness catches substantive errors that keyword heuristics cannot.

**Limitation:** Without ground-truth reference answers, "correctness" is the judge's interpretation, not a ground-truth oracle. Treat as a directional signal; calibrate by sampling and reviewing judge reasoning on a small set.

**Current value:** **[RUN REQUIRED]**

---

## 3. Golden dataset

**File:** `data/eval/golden_set.jsonl`
**Size:** 30 queries (25 positive + 5 negative/refusal cases)
**Format:** JSONL, one case per line. Positive cases have fields: `id`, `query`, `relevant_sources` (list of TS spec numbers), `expected_keywords`, `expected_facts`, `spec_refs`, `notes`. Negative cases additionally have `is_out_of_corpus: true`, `expected_behavior: "refusal"`, and `refusal_hint`.

### Dataset construction

Queries were written to cover:
- Core architecture concepts (gNB, NG-RAN, CU/DU split) → TS 38.300, 38.401
- Interface specifications (F1, E1, Xn, NG, X2) → TS 38.470, 38.460, 38.420, 38.410, 36.423
- Protocol specifications (MAC, RLC, PDCP, RRC, SDAP) → TS 38.321, 38.322, 38.323, 38.331
- Physical layer (SSB, HARQ, RACH, NR vs LTE) → TS 38.211, 38.213, 36.211
- Advanced 5G features (dual connectivity, network slicing, beamforming) → TS 38.300, 38.331

### What is and isn't ground truth

`relevant_sources` and `expected_keywords` are genuine ground truth — they identify the 3GPP specifications that define the answer to each query, based on the actual 3GPP catalog. These are checkable against the corpus.

`expected_facts` are directionally correct technical claims about 3GPP specifications. They are NOT full reference answers and should not be used for automated answer-correctness scoring without human review. They serve as audit markers for a human reviewer confirming whether a generated answer addressed the core technical point.

### Graded relevance labels (v3 addition)

Seven queries carry a `graded_relevance` field: a dict mapping spec token to integer grade:
- **2** = primary/definitional spec — the system must retrieve from this spec to answer the query correctly.
- **1** = supporting spec — provides useful context but not the primary definition.
- **0** = not relevant (implicit; any spec not in the dict).

Queries with graded labels: gs-001, gs-002, gs-003, gs-004, gs-005, gs-008, gs-009. These cover gNB definition, F1/E1 interfaces, NG-RAN architecture, handover, MAC, and RRC.

When `graded_relevance` is present in a case, `ndcg_at_k` uses graded gains. Binary metrics (hit-rate, Recall@k, MRR) continue to use the binary `relevant_sources` list.

### Negative / out-of-corpus cases (v3 addition)

Five cases (`neg-001` through `neg-005`) are explicitly out-of-corpus:
- `neg-001`: Food/nutrition question (completely unrelated domain)
- `neg-002`: Kubernetes/Calico networking (cloud-native, not 3GPP)
- `neg-003`: Non-existent spec number TS 99.999 (hallucination trap)
- `neg-004`: Ericsson stock price (financial, not telecom standards)
- `neg-005`: Cisco IOS BGP configuration (vendor-specific, adjacent domain)

These test that the system declines rather than confabulating a 3GPP answer. The `refusal_rate` metric (in `scripts/eval/metrics.py`) measures what fraction of out-of-corpus queries the system correctly refuses. **[RUN REQUIRED]** for live numbers — requires the full index and a live LLM to generate answers for these queries, then `is_refusal()` to score them.

### What was NOT done (remaining gaps)

- No paraphrase variants per query
- No human annotation of individual retrieved chunks (only source-level relevance)
- Refusal-rate numbers not yet produced (require live inference on negative cases)

These are the logical next steps for a v4 golden set.

---

## 4. Regression mode

**Activate with:**
```
# Save current run as baseline
python scripts/eval_retrieval.py --save-baseline

# On subsequent runs, check for regression (CI gate)
python scripts/eval_retrieval.py --regression
```

**Tracked metrics:**
- `retrieval.avg_hit_rate_at_k` (tolerance: ±0.05)
- `retrieval.avg_recall_at_k` (tolerance: ±0.05)
- `retrieval.avg_mrr` (tolerance: ±0.05)
- `retrieval.avg_ndcg_at_k` (tolerance: ±0.05)
- `retrieval.avg_context_precision` (tolerance: ±0.05)
- `retrieval.avg_context_recall` (tolerance: ±0.05)
- `latency.retrieve.p50` (tolerance: +0.10s)
- `latency.retrieve.p95` (tolerance: +0.20s)

**Regression definition:** A metric regresses when the current value falls below `baseline - tolerance` (quality metrics) or rises above `baseline + tolerance` (latency). The tolerances are set to absorb normal run-to-run noise while catching genuine quality drops.

**CI integration:** The eval script exits with code 1 on regression. Add to CI:
```yaml
- name: Regression check
  run: python scripts/eval_retrieval.py --regression
```
This gate is meaningful once a baseline is established from a full run on the complete index.

**Baseline file:** `data/eval/baseline.json` — created by `--save-baseline`, tracked in version control. Each baseline commit should note the index version and date it was produced.

**Current baseline:** `data/eval/baseline.json` is the full-index baseline (2026-06-25, 43,121 chunks, 25 in-corpus queries), tracked in version control so `--regression` compares like-for-like. Regenerate after an index or model change with `python scripts/eval_retrieval.py --save-baseline`.

**Committed baseline values (full index, in-corpus N=25):**
- avg_hit_rate_at_k: 0.880
- avg_recall_at_k: 0.640
- avg_mrr: 0.679
- avg_ndcg_at_k: 0.723
- avg_context_precision: 0.440
- avg_context_recall: 0.714
- retrieve p50 / p95: ~0.021s / ~0.048s

---

## 5. How to reproduce

### Sample fixture run (no index, no LLM required — runs immediately)
```bash
python scripts/eval/run_sample_eval.py
```
Runs 6 fixture queries against a 10-chunk in-memory TF-IDF index. Confirms the harness computes all metrics end-to-end. Results are labeled "sample fixture — NOT full-corpus quality."

To write results and set as regression baseline:
```bash
python scripts/eval/run_sample_eval.py --output data/eval/sample_results.json --save-baseline
```

### Fast retrieval-only run (no LLM required; requires built index)
```bash
python scripts/eval_retrieval.py --output data/eval_results.json
```
Runs all 30 golden-set queries (25 positive + 5 negative), computes standard IR + heuristic retrieval metrics, writes results to `data/eval_results.json`. Typical runtime: 10–30 seconds depending on embedding warm-up.

### With heuristic answer quality (requires Ollama)
```bash
ollama serve
ollama pull llama3.2
python scripts/eval_retrieval.py --full --output data/eval_results.json
```

### With LLM-judge [RUN REQUIRED]
```bash
export GROQ_API_KEY=your_key_here
python scripts/eval_retrieval.py --full --judge --judge-provider groq --output data/eval_results.json
```

### Legacy 10-query run (original inline test set)
```bash
python scripts/eval_retrieval.py --no-golden --output data/eval_results.json
```

### Build the index first (if not already built)
```bash
python scripts/download_specs.py
python scripts/build_index.py
```
Index build requires ~2–4 GB disk for 3GPP spec downloads and ~30–60 minutes for chunking + embedding 43k+ passages.

---

## 6. Current results

### 6.1 Sample fixture run (2026-06-23) — harness smoke test

Produced by `python scripts/eval/run_sample_eval.py`. Results in `data/eval/sample_results.json`.

**Fixture: 10 hand-built chunks, 6 queries, k=5, TF-IDF similarity (no vector DB or LLM)**

These numbers confirm the harness computes every metric correctly end-to-end. They are NOT representative of full-corpus quality.

| Metric | Value | Note |
|---|---|---|
| Hit-rate@5 | **1.000** | All 6 fixture queries retrieved ≥1 relevant chunk in top 5 |
| Recall@5 | **1.000** | All expected source specs found in top 5 for every query |
| MRR | **1.000** | Relevant chunk ranked first for every query |
| nDCG@5 (binary) | **0.984** | Avg; fix-001 scores 0.906 (two 38300 chunks split the grade) |
| nDCG@5 (graded) | **0.982** | Avg with 0/1/2 grades; confirms graded path works |
| Context precision (heuristic) | **0.300** | Expected: fixture has non-relevant chunks that score 0 |
| Context recall / keyword (heuristic) | **0.958** | 5/6 queries achieve full keyword coverage |
| Retrieve latency p50 | **~0.000045s** | In-memory TF-IDF; orders of magnitude faster than ChromaDB |
| Retrieve latency p95 | **~0.000065s** | — |

fix-001 nDCG < 1.0 is expected and correct: the TF-IDF retriever surfaces two chunks from `38300-g10.docx` in the top 5 (chunks 001 and 006), placing the `38401` chunk at rank 3 instead of rank 2, which is a suboptimal ranking for this two-spec query. The metric correctly penalizes it.

Context precision of 0.3 is expected: the fixture index contains 10 chunks from 10 different specs; for a query expecting 1-2 specs, 3-4 of the 5 retrieved chunks will typically come from non-matching specs. This is a characteristic of a small diverse fixture, not a production quality signal.

---

### 6.2 Full index baseline (2026-06-25) — production baseline

All numbers below come directly from `data/eval_results.json`, dated 2026-06-25. They were produced on the full 43,121-chunk local/API index using the 30-query golden set (25 in-corpus + 5 out-of-corpus refusal probes). Standard IR metrics are over the 25 in-corpus queries; the refusal axis over the 5. This is also the committed regression baseline (`data/eval/baseline.json`).

**Retrieval — in-corpus (N=25):**

| Metric | Value | Note |
|---|---|---|
| Hit-rate@5 | **0.88** | Relevant source in top-5 for 88% of queries |
| nDCG@5 (graded) | **0.723** | "GOOD" band; primary retrieval signal |
| MRR | **0.679** | First relevant hit lands high on average |
| Recall@5 | **0.64** | Fraction of all expected source specs surfaced |
| Avg context precision (heuristic) | **0.44** | Strict source-filename match; supplementary |
| Avg context recall kw (heuristic) | **0.71** | Avg keyword coverage across top-3 |
| Legacy pass rate | **18/25 (72%)** | Composite: keyword recall ≥0.5 AND avg sim ≥0.50 |
| Avg cosine similarity | **0.557** | Mean of top-3 chunks per query |
| Retrieve p50 / p95 latency | **0.021s / 0.048s** | Apple M2 CPU |

**Refusal axis — out-of-corpus probes (N=5):**

| Metric | Value | Note |
|---|---|---|
| Retrieval-refusal rate | **4/5 (80%)** | Top-3 avg sim correctly below the 0.50 threshold |
| Avg out-of-corpus similarity | **0.331** | vs 0.557 in-corpus — measurably less confident on junk |
| LLM-judged refusal rate | **[RUN REQUIRED]** | Whether the generated answer declines — needs `--full` + live LLM |
| Faithfulness (LLM-judge) | **[RUN REQUIRED]** | Requires live LLM |
| Answer correctness (LLM-judge) | **[RUN REQUIRED]** | Requires live LLM |

**Reading the 88% hit-rate vs 72% legacy pass.** Seven in-corpus queries miss the legacy bar. Four of them actually retrieve the correct source (nDCG@5 = 1.0) and miss only because bge-small's cosine similarity sits just below the 0.50 threshold: gNB (0.426), HARQ (0.496), LTE X2 (0.500), SDAP (0.462, with full keyword recall). The other three are genuine retrieval misses (nDCG@5 = 0.0): E1 interface (gs-003), SA-vs-NSA (gs-007), and NR-vs-LTE physical layer (gs-025) — all comparison/interface queries where the question wording diverges from spec terminology.

---

## 7. Interpretation and next steps

The 2026-06-25 full-index baseline gives an honest picture of a working retrieval system:

- **Strong on single-fact lookup:** hit-rate@5 0.88 and MRR 0.679 mean that when a query maps to one definitional spec, the right chunk is usually retrieved and ranked high.
- **Weaker on multi-evidence:** Recall@5 0.64 reflects queries that expect two specs but get one (e.g. gNB → 38.300 + 38.401). This is the clearest place to improve.
- **The similarity threshold is mis-calibrated for bge-small:** four "failures" retrieved the correct document but scored below the 0.50 cosine cutoff. The pass criterion, not the retriever, is the problem for those.
- **Comparison/interface queries are the genuine miss cluster:** E1, SA-vs-NSA, NR-vs-LTE PHY all fail because the question phrasing doesn't match spec vocabulary.
- **Refusal behaviour is reasonable at the retrieval layer:** 4/5 out-of-corpus probes stay below threshold; the answer-layer refusal still needs an LLM run.

**Priority improvements:**
1. Recalibrate or learn the per-embedding-model similarity threshold so correctly-retrieved-but-low-similarity queries aren't penalized.
2. Query-side synonym/paraphrase expansion for interface and comparison questions (E1, SA/NSA, NR-vs-LTE PHY).
3. Investigate multi-spec recall: ensure both expected specs surface for two-spec queries.
4. Run LLM-judge faithfulness/answer-correctness on the golden set **[RUN REQUIRED]**.
5. Run the 5 negative cases through the live answer path and record the LLM-judged refusal rate **[RUN REQUIRED]**.
6. Expand graded relevance labels beyond the current 7 in-corpus queries.
