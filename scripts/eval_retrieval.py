"""
Evaluation script for the 3GPP RAG pipeline

Measures three layers of quality:

  1. Retrieval quality  — are the right chunks being fetched?
     - Context precision  : fraction of retrieved chunks that are relevant
     - Context recall     : fraction of expected keywords found in top-k chunks
     - Average similarity : mean cosine similarity of top-3 results
     - Latency            : p50 / p95 retrieve time

  2. Answer quality (requires Ollama) — is the generated answer good?
     - Answer relevance   : do expected answer terms appear in the response?
     - Faithfulness       : does the answer stay grounded in retrieved sources?
     - Answer length      : is the response substantive (>50 chars)?
     - Latency            : p50 / p95 generate time

  3. End-to-end latency benchmarks
     - Total query time (retrieve + generate)
     - p50 / p95 across all test cases

Usage:
    # Retrieval only (fast, no LLM needed)
    python scripts/eval_retrieval.py

    # Full eval including answer quality
    python scripts/eval_retrieval.py --full

    # Save results to JSON (served by the API at GET /eval)
    python scripts/eval_retrieval.py --full --output data/eval_results.json
"""
import sys
import json
import argparse
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.retriever import DocumentRetriever


# ---------------------------------------------------------------------------
# Test cases — representative 3GPP questions with ground-truth signals
# ---------------------------------------------------------------------------

TEST_CASES: List[Dict[str, Any]] = [
    {
        "query": "What is gNB?",
        "expected_keywords": ["gnb", "base station", "node", "ran"],
        "answer_keywords": ["gnb", "base station", "radio"],
        "relevant_sources": ["38300", "38401"],
        "min_similarity": 0.50,
    },
    {
        "query": "Explain the 5G protocol stack",
        "expected_keywords": ["protocol", "stack", "layer", "nr"],
        "answer_keywords": ["protocol", "layer", "stack"],
        "relevant_sources": ["38300"],
        "min_similarity": 0.50,
    },
    {
        "query": "What are the NG-RAN functions?",
        "expected_keywords": ["ng-ran", "function", "ran"],
        "answer_keywords": ["ng-ran", "function"],
        "relevant_sources": ["38300", "38401"],
        "min_similarity": 0.50,
    },
    {
        "query": "How does handover work in 5G?",
        "expected_keywords": ["handover", "mobility", "cell"],
        "answer_keywords": ["handover", "cell", "ue"],
        "relevant_sources": ["38300"],
        "min_similarity": 0.45,
    },
    {
        "query": "What is the NR physical layer?",
        "expected_keywords": ["physical", "layer", "nr"],
        "answer_keywords": ["physical", "layer", "channel"],
        "relevant_sources": ["38300"],
        "min_similarity": 0.50,
    },
    {
        "query": "What is the difference between SA and NSA 5G deployments?",
        "expected_keywords": ["standalone", "non-standalone", "sa", "nsa"],
        "answer_keywords": ["sa", "nsa", "standalone"],
        "relevant_sources": ["38300"],
        "min_similarity": 0.45,
    },
    {
        "query": "Describe the F1 interface between gNB-CU and gNB-DU",
        "expected_keywords": ["f1", "cu", "du", "interface"],
        "answer_keywords": ["f1", "cu", "du"],
        "relevant_sources": ["38401"],
        "min_similarity": 0.45,
    },
    {
        "query": "What is E1 interface used for in 5G?",
        "expected_keywords": ["e1", "interface", "cu-cp", "cu-up"],
        "answer_keywords": ["e1", "cu-cp", "cu-up"],
        "relevant_sources": ["38401"],
        "min_similarity": 0.45,
    },
    {
        "query": "How is QoS managed in NG-RAN?",
        "expected_keywords": ["qos", "quality", "service", "bearer"],
        "answer_keywords": ["qos", "service", "flow"],
        "relevant_sources": ["38300"],
        "min_similarity": 0.45,
    },
    {
        "query": "What is Xn interface?",
        "expected_keywords": ["xn", "interface", "gnb"],
        "answer_keywords": ["xn", "interface", "gnb"],
        "relevant_sources": ["38300", "38401"],
        "min_similarity": 0.45,
    },
]


# ---------------------------------------------------------------------------
# Retrieval evaluation
# ---------------------------------------------------------------------------

def _context_precision(docs: List[Dict], relevant_sources: List[str]) -> float:
    """
    RAGAS-inspired context precision.

    Fraction of retrieved chunks whose source document is relevant
    (i.e. the filename contains one of the relevant_sources strings).
    """
    if not docs:
        return 0.0
    relevant_hits = sum(
        1 for d in docs
        if any(rs in d["source"] for rs in relevant_sources)
    )
    return relevant_hits / len(docs)


def _context_recall(docs: List[Dict], expected_keywords: List[str]) -> float:
    """
    RAGAS-inspired context recall.

    Fraction of expected keywords found anywhere in the top-3 retrieved chunks.
    """
    if not docs or not expected_keywords:
        return 0.0
    combined_text = " ".join(d["text"].lower() for d in docs[:3])
    hits = sum(1 for kw in expected_keywords if kw.lower() in combined_text)
    return hits / len(expected_keywords)


def evaluate_retrieval_case(retriever: DocumentRetriever, case: Dict) -> Dict:
    """Run retrieval evaluation for a single test case."""
    query = case["query"]
    min_sim = case.get("min_similarity", 0.50)

    t0 = time.time()
    docs = retriever.retrieve(query)
    elapsed = round(time.time() - t0, 4)

    if not docs:
        return {
            "query": query,
            "retrieval_pass": False,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "avg_similarity": 0.0,
            "top_source": "N/A",
            "retrieve_time": elapsed,
        }

    precision = _context_precision(docs, case.get("relevant_sources", []))
    recall = _context_recall(docs, case["expected_keywords"])
    avg_sim = sum(d["similarity"] for d in docs[:3]) / min(3, len(docs))

    # Pass if recall >= 50% AND avg similarity >= threshold
    passed = recall >= 0.5 and avg_sim >= min_sim

    return {
        "query": query,
        "retrieval_pass": passed,
        "context_precision": round(precision, 3),
        "context_recall": round(recall, 3),
        "avg_similarity": round(avg_sim, 3),
        "min_similarity": min_sim,
        "top_source": docs[0]["source"],
        "num_results": len(docs),
        "retrieve_time": elapsed,
        "docs": docs,   # stripped before saving
    }


def _print_retrieval_result(i: int, result: Dict) -> None:
    status = "PASS" if result["retrieval_pass"] else "FAIL"
    icon = "✅" if result["retrieval_pass"] else "❌"
    print(f"\nTest {i}: {result['query']}")
    print("-" * 60)
    print(f"  Context precision:  {result['context_precision']:.1%}")
    print(f"  Context recall:     {result['context_recall']:.1%}")
    print(f"  Avg similarity:     {result['avg_similarity']:.3f}  "
          f"(min={result.get('min_similarity', 0.50):.3f})")
    print(f"  Top source:         {result['top_source']}")
    print(f"  Retrieve time:      {result['retrieve_time']}s")
    print(f"  Status:             {icon} {status}")


# ---------------------------------------------------------------------------
# Answer quality evaluation (RAGAS-style)
# ---------------------------------------------------------------------------

def _answer_relevance(answer: str, case: Dict) -> float:
    """
    RAGAS-inspired answer relevance.

    Measures how many expected answer keywords appear in the generated answer.
    Range: 0.0 - 1.0
    """
    kw = case.get("answer_keywords", [])
    if not kw:
        return 0.0
    hits = sum(1 for k in kw if k.lower() in answer.lower())
    return hits / len(kw)


def _faithfulness(answer: str, docs: List[Dict]) -> float:
    """
    RAGAS-inspired faithfulness.

    Scores whether the answer stays grounded in the retrieved context.
    Uses two heuristics:
      1. Direct grounding signals (mentions source docs / 3GPP terminology)
      2. Content overlap: key words from the top chunk appear in the answer
    Range: 0.0 - 1.0
    """
    if not docs:
        return 0.0

    answer_lower = answer.lower()

    # Heuristic 1: grounding signals
    grounding_signals = [
        "3gpp", "ts ", "specification", "according", "document",
        "source:", "based on", "the spec", "release",
    ]
    grounding_score = min(
        sum(1 for s in grounding_signals if s in answer_lower) / 3, 1.0
    )

    # Heuristic 2: content overlap with top retrieved chunk
    stop = {
        "the", "a", "an", "is", "are", "in", "of", "to", "and", "or",
        "that", "it", "this", "for", "be", "was", "with", "as", "by",
    }
    top_words = set(docs[0]["text"].lower().split()) - stop
    answer_words = set(answer_lower.split()) - stop
    if top_words:
        overlap = len(top_words & answer_words) / min(len(top_words), 20)
        overlap_score = min(overlap, 1.0)
    else:
        overlap_score = 0.0

    return round((grounding_score * 0.5) + (overlap_score * 0.5), 3)


def evaluate_answer_quality(answer: str, case: Dict, docs: List[Dict]) -> Dict:
    """Score the quality of a generated answer against a test case."""
    relevance = _answer_relevance(answer, case)
    faithfulness = _faithfulness(answer, docs)

    is_substantive = len(answer.strip()) >= 50
    refusal_signals = [
        "cannot find", "not enough information", "no relevant",
        "i don't know", "i cannot answer",
    ]
    is_refusal = any(s in answer.lower() for s in refusal_signals)

    # Composite score: relevance 40%, faithfulness 40%, substantive 20%
    score = round(
        (relevance * 0.4)
        + (faithfulness * 0.4)
        + (0.2 if is_substantive and not is_refusal else 0.0),
        3,
    )

    return {
        "answer_relevance": round(relevance, 3),
        "faithfulness": round(faithfulness, 3),
        "answer_score": score,
        "is_substantive": is_substantive,
        "is_refusal": is_refusal,
        "answer_pass": score >= 0.40,
        "answer_preview": answer[:200].replace("\n", " "),
    }


def run_answer_eval(
    retriever: DocumentRetriever, retrieval_results: List[Dict]
) -> List[Dict]:
    """Enhance retrieval results with answer quality scores."""
    try:
        from src.core.llm import OllamaLLM
        from src.core.rag_chain import RAGChain
    except ImportError as e:
        print(f"\n⚠️  Could not import LLM modules: {e}")
        return retrieval_results

    llm = OllamaLLM()
    if not llm.is_available():
        print(f"\n⚠️  Ollama not available — skipping answer quality evaluation")
        print(f"   Start Ollama: ollama serve  |  Pull model: ollama pull {llm.model}")
        return retrieval_results

    chain = RAGChain(retriever=retriever, llm=llm)
    print(f"\n{'='*60}")
    print(f"Answer Quality Evaluation  (model: {llm.model})")
    print("=" * 60)

    enriched = []
    for i, (result, case) in enumerate(
        zip(retrieval_results, TEST_CASES[: len(retrieval_results)]), 1
    ):
        print(f"\nTest {i}: {result['query']}")
        print("-" * 60)

        t0 = time.time()
        rag_result = chain.query(result["query"])
        gen_time = round(time.time() - t0, 4)

        docs = result.get("docs", [])
        aq = evaluate_answer_quality(rag_result["answer"], case, docs)
        aq["generate_time"] = gen_time

        icon = "✅" if aq["answer_pass"] else "❌"
        print(f"  Answer relevance:  {aq['answer_relevance']:.1%}")
        print(f"  Faithfulness:      {aq['faithfulness']:.1%}")
        print(f"  Score:             {aq['answer_score']:.2f}/1.00")
        print(f"  Generate time:     {gen_time}s")
        print(f"  Status:            {icon} {'PASS' if aq['answer_pass'] else 'FAIL'}")
        print(f"  Preview:           {aq['answer_preview'][:120]}...")

        enriched.append({**result, **aq})

    return enriched


# ---------------------------------------------------------------------------
# Latency benchmarks
# ---------------------------------------------------------------------------

def _percentile(values: List[float], pct: int) -> float:
    """Return the given percentile value from a list of floats."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = max(0, int(len(sorted_vals) * pct / 100) - 1)
    return round(sorted_vals[idx], 4)


def compute_latency_benchmarks(results: List[Dict]) -> Dict:
    """Compute p50/p95 latency stats for retrieve and generate times."""
    retrieve_times = [r["retrieve_time"] for r in results if "retrieve_time" in r]
    generate_times = [r["generate_time"] for r in results if r.get("generate_time")]

    benchmarks: Dict[str, Any] = {
        "retrieve": {
            "p50": _percentile(retrieve_times, 50),
            "p95": _percentile(retrieve_times, 95),
            "mean": round(statistics.mean(retrieve_times), 4) if retrieve_times else 0,
        }
    }
    if generate_times:
        total_times = [
            r.get("retrieve_time", 0) + r.get("generate_time", 0)
            for r in results
            if r.get("generate_time")
        ]
        benchmarks["generate"] = {
            "p50": _percentile(generate_times, 50),
            "p95": _percentile(generate_times, 95),
            "mean": round(statistics.mean(generate_times), 4),
        }
        benchmarks["total"] = {
            "p50": _percentile(total_times, 50),
            "p95": _percentile(total_times, 95),
            "mean": round(statistics.mean(total_times), 4),
        }

    return benchmarks


# ---------------------------------------------------------------------------
# Summary & reporting
# ---------------------------------------------------------------------------

def print_summary(results: List[Dict], full_eval: bool) -> Dict:
    """Print evaluation summary and return a structured summary dict."""
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)

    r_total = len(results)
    r_passed = sum(1 for r in results if r["retrieval_pass"])
    r_rate = r_passed / r_total if r_total else 0

    avg_precision = sum(r["context_precision"] for r in results) / r_total if r_total else 0
    avg_recall = sum(r["context_recall"] for r in results) / r_total if r_total else 0
    avg_sim = sum(r["avg_similarity"] for r in results) / r_total if r_total else 0

    print(f"\nRetrieval Quality")
    print(f"  Pass rate:             {r_passed}/{r_total} ({r_rate:.1%})")
    print(f"  Avg context precision: {avg_precision:.1%}")
    print(f"  Avg context recall:    {avg_recall:.1%}")
    print(f"  Avg similarity:        {avg_sim:.3f}")

    if r_rate >= 0.80:
        print("  → ✅ EXCELLENT retrieval quality")
    elif r_rate >= 0.60:
        print("  → ✅ GOOD retrieval quality")
    elif r_rate >= 0.40:
        print("  → ⚠️  FAIR — consider tuning chunk size or embedding model")
    else:
        print("  → ❌ POOR — check vector store and embedding model")

    answer_summary: Dict = {}
    if full_eval and any("answer_score" in r for r in results):
        a_passed = sum(1 for r in results if r.get("answer_pass", False))
        avg_relevance = sum(r.get("answer_relevance", 0) for r in results) / r_total
        avg_faithfulness = sum(r.get("faithfulness", 0) for r in results) / r_total
        avg_score = sum(r.get("answer_score", 0) for r in results) / r_total

        print(f"\nAnswer Quality")
        print(f"  Pass rate:            {a_passed}/{r_total} ({a_passed/r_total:.1%})")
        print(f"  Avg answer relevance: {avg_relevance:.1%}")
        print(f"  Avg faithfulness:     {avg_faithfulness:.1%}")
        print(f"  Avg score:            {avg_score:.2f}/1.00")

        if avg_score >= 0.65:
            print("  → ✅ GOOD answer quality")
        elif avg_score >= 0.40:
            print("  → ⚠️  FAIR — answers could be more grounded/detailed")
        else:
            print("  → ❌ POOR — check prompt template and LLM model")

        answer_summary = {
            "pass_rate": round(a_passed / r_total, 3),
            "avg_answer_relevance": round(avg_relevance, 3),
            "avg_faithfulness": round(avg_faithfulness, 3),
            "avg_score": round(avg_score, 3),
        }

    benchmarks = compute_latency_benchmarks(results)
    print(f"\nLatency Benchmarks")
    print(f"  Retrieve p50: {benchmarks['retrieve']['p50']}s  "
          f"p95: {benchmarks['retrieve']['p95']}s")
    if "generate" in benchmarks:
        print(f"  Generate p50: {benchmarks['generate']['p50']}s  "
              f"p95: {benchmarks['generate']['p95']}s")
        print(f"  Total    p50: {benchmarks['total']['p50']}s  "
              f"p95: {benchmarks['total']['p95']}s")

    if r_rate < 0.70:
        print("\nImprovement suggestions:")
        print("  1. Use bge-base embedding model (stronger for technical text)")
        print("  2. Increase chunk_size to 1500 for more context per chunk")
        print("  3. Increase chunk_overlap to 300 for better boundary handling")
        print("  4. Index more 3GPP spec series (23.xxx, 36.xxx, 38.xxx)")

    print("=" * 60 + "\n")

    return {
        "retrieval": {
            "pass_rate": round(r_rate, 3),
            "passed": r_passed,
            "total": r_total,
            "avg_context_precision": round(avg_precision, 3),
            "avg_context_recall": round(avg_recall, 3),
            "avg_similarity": round(avg_sim, 3),
        },
        "answer": answer_summary,
        "latency": benchmarks,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate 3GPP RAG pipeline quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Run answer quality evaluation (requires Ollama)",
    )
    parser.add_argument(
        "--output", default="data/eval_results.json",
        help="Save results to this JSON file (default: data/eval_results.json)",
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="Chunks to retrieve per query (default: 5)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Skip saving results to disk",
    )
    args = parser.parse_args()

    from src.core.vector_store import VectorStore
    vs_stats = VectorStore().get_stats()
    if vs_stats["total_chunks"] == 0:
        print("\n❌ Vector store is empty. Run: python scripts/build_index.py\n")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("3GPP RAG Pipeline Evaluation")
    print(f"{'='*60}")
    print(f"Vector store:  {vs_stats['total_chunks']} chunks")
    print(f"Test cases:    {len(TEST_CASES)}")
    print(f"Top-k:         {args.top_k}")
    print(f"Mode:          {'Full (retrieval + answer)' if args.full else 'Retrieval only'}")

    retriever = DocumentRetriever(top_k=args.top_k)

    # Retrieval evaluation
    print(f"\n{'='*60}")
    print("Retrieval Quality Evaluation")
    print("=" * 60)

    retrieval_results = []
    for i, case in enumerate(TEST_CASES, 1):
        result = evaluate_retrieval_case(retriever, case)
        _print_retrieval_result(i, result)
        retrieval_results.append(result)

    # Answer quality evaluation (optional)
    final_results = retrieval_results
    if args.full:
        final_results = run_answer_eval(retriever, retrieval_results)

    summary = print_summary(final_results, full_eval=args.full)

    # Save results
    if not args.no_save:
        import datetime
        save_data = {
            "evaluated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "config": {
                "top_k": args.top_k,
                "full_eval": args.full,
                "total_chunks": vs_stats["total_chunks"],
            },
            "summary": summary,
            "cases": [
                {k: v for k, v in r.items() if k != "docs"}
                for r in final_results
            ],
        }
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(save_data, f, indent=2)
        print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
