"""
Retrieval quality on follow-up questions (Sprint 2, ADR-014).

Each case in ``data/eval/multiturn_set.jsonl`` is a short conversation and a
follow-up whose subject lives only in the history ("Which protocol runs on
its control plane?" after a question about F1). For every case the
follow-up is searched four ways:

  * ``raw``       the follow-up as typed (what retrieval saw before Sprint 2)
  * ``fallback``  previous user question + follow-up (no LLM)
  * ``llm``       QueryRewriter with a local LLM (the shipped default)
  * ``oracle``    a hand-written standalone question (upper bound)

and scored with the same retrieval metrics as the golden set.

Usage:
    python scripts/eval/multiturn_eval.py --model llama3.2 [--collection 3gpp_clauses]
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import settings  # noqa: E402

STRATEGIES = ("raw", "fallback", "llm", "oracle")


def load_cases(path: str) -> List[Dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", default="data/eval/multiturn_set.jsonl")
    parser.add_argument("--model", default="llama3.2", help="Ollama model for the rewrite")
    parser.add_argument("--collection", default=None)
    parser.add_argument("--output", default="data/eval/multiturn.json")
    args = parser.parse_args()

    if args.collection:
        settings.collection_name = args.collection

    from scripts.eval_retrieval import _ablation_row, evaluate_retrieval_case
    from src.core.llm import OllamaLLM
    from src.core.query_rewriter import QueryRewriter, fallback_query
    from src.core.retriever import DocumentRetriever

    cases = load_cases(args.cases)
    retriever = DocumentRetriever(top_k=5)
    retriever.retrieve("warm-up query")
    rewriter = QueryRewriter(OllamaLLM(model=args.model, temperature=0.0), always=True)

    per_strategy: Dict[str, List[Dict]] = {s: [] for s in STRATEGIES}
    rewrites: List[Dict] = []
    for case in cases:
        llm = rewriter.rewrite(case["query"], case["history"])
        queries = {
            "raw": case["query"],
            "fallback": fallback_query(case["query"], case["history"]),
            "llm": llm["query"],
            "oracle": case["standalone"],
        }
        rewrites.append({"id": case["id"], "followup": case["query"],
                         "llm_rewrite": llm["query"], "llm_method": llm["method"]})
        line = []
        for name, q in queries.items():
            r = evaluate_retrieval_case(retriever, {**case, "query": q})
            r.pop("docs", None)
            per_strategy[name].append(r)
            line.append(f"{name}={r['recall_at_k']:.2f}")
        print(f"{case['id']}  {'  '.join(line)}  | llm: {llm['query']}")

    rows = []
    for name in STRATEGIES:
        row = _ablation_row(per_strategy[name])
        row.pop("retrieval_refusal_rate", None)
        rows.append({"strategy": name, **row})

    print("\n| Search query | Hit@5 | Recall@5 | MRR | nDCG@5 |")
    print("|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['strategy']} | {r['hit_rate_at_5']:.2f} | {r['recall_at_5']:.3f} | "
              f"{r['mrr']:.3f} | {r['ndcg_at_5']:.3f} |")

    Path(args.output).write_text(json.dumps({
        "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "config": {"cases": len(cases), "rewrite_model": args.model,
                   "collection": settings.collection_name,
                   "hybrid": retriever.hybrid, "rerank": retriever.rerank},
        "strategies": rows,
        "rewrites": rewrites,
    }, indent=2))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
