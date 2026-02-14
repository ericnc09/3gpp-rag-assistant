"""
Evaluate retrieval quality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.retriever import DocumentRetriever


# Test questions with expected keywords in results
TEST_CASES = [
    {
        "query": "What is gNB?",
        "expected_keywords": ["gnb", "base station", "node", "ran"],
        "min_similarity": 0.70
    },
    {
        "query": "Explain the 5G protocol stack",
        "expected_keywords": ["protocol", "stack", "layer", "nr"],
        "min_similarity": 0.70
    },
    {
        "query": "What are the NG-RAN functions?",
        "expected_keywords": ["ng-ran", "function", "ran"],
        "min_similarity": 0.70
    },
    {
        "query": "How does handover work in 5G?",
        "expected_keywords": ["handover", "mobility", "cell"],
        "min_similarity": 0.65
    },
    {
        "query": "What is the NR physical layer?",
        "expected_keywords": ["physical", "layer", "nr"],
        "min_similarity": 0.70
    },
]


def evaluate_retrieval():
    """Evaluate retrieval on test cases"""
    retriever = DocumentRetriever(top_k=5)
    
    results = []
    
    print("\n" + "="*60)
    print("Retrieval Quality Evaluation")
    print("="*60)
    
    for i, test_case in enumerate(TEST_CASES, 1):
        query = test_case["query"]
        expected_keywords = test_case["expected_keywords"]
        min_similarity = test_case.get("min_similarity", 0.70)
        
        print(f"\nTest {i}: {query}")
        print("-" * 60)
        
        # Retrieve documents
        docs = retriever.retrieve(query)
        
        if not docs:
            print("  ❌ No results returned")
            results.append({
                "query": query,
                "keyword_score": 0,
                "avg_similarity": 0,
                "pass": False
            })
            continue
        
        # Check if keywords appear in top results
        top_text = " ".join([d['text'].lower() for d in docs[:3]])
        
        keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in top_text)
        keyword_score = keyword_hits / len(expected_keywords)
        
        # Calculate scores
        avg_similarity = sum(d['similarity'] for d in docs[:3]) / min(3, len(docs))
        
        # Pass criteria
        passed = keyword_score >= 0.5 and avg_similarity >= min_similarity
        
        result = {
            "query": query,
            "keyword_score": keyword_score,
            "avg_similarity": avg_similarity,
            "pass": passed
        }
        
        results.append(result)
        
        # Print results
        print(f"  Keywords found: {keyword_hits}/{len(expected_keywords)} ({keyword_score:.1%})")
        print(f"  Avg similarity: {avg_similarity:.3f} (min: {min_similarity:.3f})")
        print(f"  Top result: {docs[0]['source']}")
        print(f"  Status: {'✅ PASS' if passed else '❌ FAIL'}")
    
    # Summary
    print("\n" + "="*60)
    print("Evaluation Summary")
    print("="*60)
    passed = sum(1 for r in results if r['pass'])
    total = len(results)
    pass_rate = passed / total if total > 0 else 0
    avg_similarity = sum(r['avg_similarity'] for r in results) / total if total > 0 else 0
    avg_keyword_score = sum(r['keyword_score'] for r in results) / total if total > 0 else 0
    
    print(f"Tests passed: {passed}/{total} ({pass_rate:.1%})")
    print(f"Average similarity: {avg_similarity:.3f}")
    print(f"Average keyword coverage: {avg_keyword_score:.1%}")
    
    if pass_rate >= 0.70:
        print("\n✅ GOOD - Retrieval quality is acceptable (≥70% pass rate)")
    elif pass_rate >= 0.50:
        print("\n⚠️  FAIR - Consider improving (50-70% pass rate)")
    else:
        print("\n❌ POOR - Needs improvement (<50% pass rate)")
    
    print("="*60 + "\n")
    
    # Recommendations
    if pass_rate < 0.70:
        print("Improvement suggestions:")
        print("  1. Try a better embedding model (bge-base instead of mini)")
        print("  2. Increase chunk_size in document processor")
        print("  3. Add more 3GPP documents for better coverage")
        print("  4. Adjust chunk_overlap for better context")
        print()


if __name__ == "__main__":
    # Check if vector store has data
    from src.core.vector_store import VectorStore
    store = VectorStore()
    stats = store.get_stats()
    
    if stats['total_chunks'] == 0:
        print("\n❌ Error: Vector store is empty!")
        print("Please run: python scripts/build_index.py\n")
        sys.exit(1)
    
    evaluate_retrieval()
