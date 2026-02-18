"""
Evaluation script for the 3GPP RAG pipeline

Measures two layers of quality:

  1. Retrieval quality  - are the right chunks being fetched?
     - Semantic similarity score of top results
     - Keyword recall in top-3 chunks

  2. Answer quality (requires Ollama) - is the generated answer good?
     - Answer keyword coverage   : do expected terms appear in the answer?
     - Answer grounding score    : does the answer reference source documents?
     - Answer length check       : is the answer substantive (>50 chars)?

Usage:
    # Retrieval only (fast, no LLM needed)
    python scripts/eval_retrieval.py

    # Full eval including answer quality
    python scripts/eval_retrieval.py --full

    # Save results to JSON
    python scripts/eval_retrieval.py --full --output data/eval_results.json
"""
import sys
import json
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.retriever import DocumentRetriever


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "query": "What is gNB?",
        "expected_keywords": ["gnb", "base station", "node", "ran"],
        "answer_keywords": ["gnb", "base station", "radio"],
        "min_similarity": 0.65,
    },
    {
        "query": "Explain the 5G protocol stack",
        "expected_keywords": ["protocol", "stack", "layer", "nr"],
        "answer_keywords": ["protocol", "layer", "stack"],
        "min_similarity": 0.65,
    },
    {
        "query": "What are the NG-RAN functions?",
        "expected_keywords": ["ng-ran", "function", "ran"],
        "answer_keywords": ["ng-ran", "function"],
        "min_similarity": 0.65,
    },
    {
        "query": "How does handover work in 5G?",
        "expected_keywords": ["handover", "mobility", "cell"],
        "answer_keywords": ["handover", "cell", "ue"],
        "min_similarity": 0.60,
    },
    {
        "query": "What is the NR physical layer?",
        "expected_keywords": ["physical", "layer", "nr"],
        "answer_keywords": ["physical", "layer", "channel"],
        "min_similarity": 0.65,
    },
    {
        "query": "What is the difference between SA and NSA 5G deployments?",
        "expected_keywords": ["standalone", "non-standalone", "sa", "nsa"],
        "answer_keywords": ["sa", "nsa", "standalone"],
        "min_similarity": 0.60,
    },
    {
        "query": "Describe the F1 interface between gNB-CU and gNB-DU",
        "expected_keywords": ["f1", "cu", "du", "interface"],
        "answer_keywords": ["f1", "cu", "du"],
        "min_similarity": 0.60,
    },
]


# ---------------------------------------------------------------------------
# Retrieval evaluation
# ---------------------------------------------------------------------------

def evaluate_retrieval_case(retriever: DocumentRetriever, case: dict) -> dict:
    """Run retrieval evaluation for a single test case."""
    query = case["query"]
    expected_kw = case["expected_keywords"]
    min_sim = case.get("min_similarity", 0.65)

    t0 = time.time()
    docs = retriever.retrieve(query)
    elapsed = time.time() - t0

    if not docs:
        return {
            "query": query,
            "retrieval_pass": False,
            "keyword_score": 0.0,
            "avg_similarity": 0.0,
            "top_source": "N/A",
            "retrieve_time": elapsed,
        }

    top_text = " ".join(d["text"].lower() for d in docs[:3])
    keyword_hits = sum(1 for kw in expected_kw if kw.lower() in top_text)
    keyword_score = keyword_hits / len(expected_kw)
    avg_sim = sum(d["similarity"] for d in docs[:3]) / min(3, len(docs))
    passed = keyword_score >= 0.5 and avg_sim >= min_sim

    return {
        "query": query,
        "retrieval_pass": passed,
        "keyword_score": round(keyword_score, 3),
        "avg_similarity": round(avg_sim, 3),
        "min_similarity": min_sim,
        "keyword_hits": keyword_hits,
        "keyword_total": len(expected_kw),
        "top_source": docs[0]["source"],
        "num_results": len(docs),
        "retrieve_time": round(elapsed, 3),
        "docs": docs,  # kept for answer eval, stripped before saving
    }


def print_retrieval_result(i: int, result: dict) -> None:
    status = "✅ PASS" if result["retrieval_pass"] else "❌ FAIL"
    print(f"\nTest {i}: {result['query']}")
    print("-" * 60)
    print(f"  Keywords:   {result['keyword_hits']}/{result['keyword_total']} "
          f"({result['keyword_score']:.1%})")
    print(f"  Similarity: {result['avg_similarity']:.3f}  "
          f"(min={result.get('min_similarity', 0.65):.3f})")
    print(f"  Top source: {result['top_source']}")
    print(f"  Time:       {result['retrieve_time']}s")
    print(f"  Status:     {status}")


# ---------------------------------------------------------------------------
# Answer quality evaluation
# ---------------------------------------------------------------------------

def evaluate_answer_quality(answer: str, case: dict) -> dict:
    """Score the quality of a generated answer against a test case."""
    answer_lower = answer.lower()
    kw = case.get("answer_keywords", [])

    # Keyword coverage
    hits = sum(1 for k in kw if k.lower() in answer_lower)
    kw_coverage = hits / len(kw) if kw else 0.0

    # Grounding: does the answer mention a source or reference?
    grounding_signals = ["source:", "document", "3gpp", "ts ", "specification", "according"]
    is_grounded = any(s in answer_lower for s in grounding_signals)

    # Length check: reject very short answers
    is_substantive = len(answer.strip()) >= 50

    # Refusal check: did the LLM say it couldn't answer?
    refusal_signals = ["cannot find", "not enough information", "no relevant", "i don't know"]
    is_refusal = any(s in answer_lower for s in refusal_signals)

    score = round(
        (kw_coverage * 0.5)
        + (0.25 if is_grounded else 0.0)
        + (0.25 if is_substantive and not is_refusal else 0.0),
        3,
    )

    return {
        "answer_score": score,
        "answer_keyword_coverage": round(kw_coverage, 3),
        "answer_keyword_hits": hits,
        "answer_keyword_total": len(kw),
        "is_grounded": is_grounded,
        "is_substantive": is_substantive,
        "is_refusal": is_refusal,
        "answer_pass": score >= 0.5,
        "answer_preview": answer[:200].replace("\n", " "),
    }


def run_answer_eval(retriever: DocumentRetriever, retrieval_results: list) -> list:
    """Enhance retrieval results with answer quality scores."""
    try:
        from src.core.llm import OllamaLLM
        from src.core.rag_chain import RAGChain
    except ImportError as e:
        print(f"\n⚠️  Could not import LLM modules: {e}")
        return retrieval_results

    llm = OllamaLLM()
    if not llm.is_available():
        print(f"\n⚠️  Ollama not available - skipping answer quality evaluation")
        print(f"   Start Ollama: ollama serve  |  Pull model: ollama pull {llm.model}")
        return retrieval_results

    chain = RAGChain(retriever=retriever, llm=llm)
    print(f"\n{'='*60}")
    print(f"Answer Quality Evaluation  (model: {llm.model})")
    print("=" * 60)

    enriched = []
    for i, (result, case) in enumerate(
        zip(retrieval_results, TEST_CASES[:len(retrieval_results)]), 1
    ):
        print(f"\nTest {i}: {result['query']}")
        print("-" * 60)

        t0 = time.time()
        rag_result = chain.query(result["query"])
        gen_time = round(time.time() - t0, 3)

        aq = evaluate_answer_quality(rag_result["answer"], case)
        aq["generate_time"] = gen_time

        status = "✅ PASS" if aq["answer_pass"] else "❌ FAIL"
        print(f"  Keywords: {aq['answer_keyword_hits']}/{aq['answer_keyword_total']} "
              f"({aq['answer_keyword_coverage']:.1%})")
        print(f"  Grounded: {'yes' if aq['is_grounded'] else 'no'}")
        print(f"  Score:    {aq['answer_score']:.2f}/1.00")
        print(f"  Time:     {gen_time}s")
        print(f"  Status:   {status}")
        print(f"  Preview:  {aq['answer_preview'][:100]}...")

        enriched.append({**result, **aq})

    return enriched


# ---------------------------------------------------------------------------
# Summary & reporting
# ---------------------------------------------------------------------------

def print_summary(results: list, full_eval: bool) -> None:
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)

    r_passed = sum(1 for r in results if r["retrieval_pass"])
    r_total = len(results)
    r_rate = r_passed / r_total if r_total else 0
    avg_sim = sum(r["avg_similarity"] for r in results) / r_total if r_total else 0
    avg_kw = sum(r["keyword_score"] for r in results) / r_total if r_total else 0
    avg_time = sum(r["retrieve_time"] for r in results) / r_total if r_total else 0

    print(f"\nRetrieval")
    print(f"  Pass rate:          {r_passed}/{r_total} ({r_rate:.1%})")
    print(f"  Avg similarity:     {avg_sim:.3f}")
    print(f"  Avg keyword recall: {avg_kw:.1%}")
    print(f"  Avg retrieve time:  {avg_time:.3f}s")

    if r_rate >= 0.80:
        print("  → ✅ EXCELLENT retrieval quality")
    elif r_rate >= 0.60:
        print("  → ✅ GOOD retrieval quality")
    elif r_rate >= 0.40:
        print("  → ⚠️  FAIR - consider improving embedding model or chunk size")
    else:
        print("  → ❌ POOR - check vector store and embedding model")

    if full_eval and any("answer_score" in r for r in results):
        a_passed = sum(1 for r in results if r.get("answer_pass", False))
        avg_ascore = sum(r.get("answer_score", 0) for r in results) / r_total
        avg_gtime = sum(r.get("generate_time", 0) for r in results) / r_total

        print(f"\nAnswer Quality")
        print(f"  Pass rate:        {a_passed}/{r_total} ({a_passed/r_total:.1%})")
        print(f"  Avg score:        {avg_ascore:.2f}/1.00")
        print(f"  Avg generate time:{avg_gtime:.2f}s")

        if avg_ascore >= 0.7:
            print("  → ✅ GOOD answer quality")
        elif avg_ascore >= 0.5:
            print("  → ⚠️  FAIR - answers could be more detailed/grounded")
        else:
            print("  → ❌ POOR - check prompt template and LLM model")

    if r_rate < 0.70:
        print("\nRetrieval improvement suggestions:")
        print("  1. Use bge-base embedding model (best for technical docs)")
        print("  2. Increase chunk_size (try 1500) for more context per chunk")
        print("  3. Add more 3GPP spec versions for broader coverage")
        print("  4. Increase chunk_overlap (try 300) for better boundary handling")

    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline quality")
    parser.add_argument("--full", action="store_true",
                        help="Run answer quality evaluation (requires Ollama)")
    parser.add_argument("--output", help="Save results to this JSON file")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Chunks to retrieve per query (default: 5)")
    args = parser.parse_args()

    from src.core.vector_store import VectorStore
    stats = VectorStore().get_stats()
    if stats["total_chunks"] == 0:
        print("\n❌ Vector store is empty. Run: python scripts/build_index.py\n")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("3GPP RAG Pipeline Evaluation")
    print(f"{'='*60}")
    print(f"Vector store: {stats['total_chunks']} chunks")
    print(f"Test cases:   {len(TEST_CASES)}")
    print(f"Mode:         {'Full (retrieval + answer)' if args.full else 'Retrieval only'}")

    retriever = DocumentRetriever(top_k=args.top_k)

    # --- Retrieval evaluation ---
    print(f"\n{'='*60}")
    print("Retrieval Quality Evaluation")
    print("=" * 60)

    retrieval_results = []
    for i, case in enumerate(TEST_CASES, 1):
        result = evaluate_retrieval_case(retriever, case)
        print_retrieval_result(i, result)
        retrieval_results.append(result)

    # --- Answer quality evaluation (optional) ---
    final_results = retrieval_results
    if args.full:
        final_results = run_answer_eval(retriever, retrieval_results)

    print_summary(final_results, full_eval=args.full)

    # --- Save to JSON ---
    if args.output:
        # Strip raw docs from saved output (too large)
        save_data = [{k: v for k, v in r.items() if k != "docs"} for r in final_results]
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(save_data, f, indent=2)
        print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
