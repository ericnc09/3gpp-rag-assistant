"""
Re-judge saved answers with the legacy (truncated) judge input.

Until 2026-11 the harness judged ``answer_preview`` (the first 200 chars of
the answer) against the first 400 chars of each chunk. This script re-runs
the judge on the *same saved answers* with that legacy input, so the effect
of the truncation is measured on identical answers, with only the judge
input changing.

Usage:
    python scripts/eval/rejudge.py --results data/eval/sprint4_eval.json \
        --provider ollama --model gemma3:4b
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.eval.agreement import fetch_chunks, load_cases  # noqa: E402
from scripts.eval.judge import LLMJudge  # noqa: E402
from scripts.eval_retrieval import build_judge_input  # noqa: E402


def _mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", default="data/eval/sprint4_eval.json")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "groq"])
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--output", default="data/eval/judge_input_comparison.json")
    args = parser.parse_args()

    judge = LLMJudge(provider=args.provider, model=args.model)
    rows = []
    for case in load_cases(args.results):
        full = case.get("llm_judge") or {}
        if not full.get("parse_ok") or case.get("is_out_of_corpus"):
            continue
        result = {**case, "answer_docs": fetch_chunks(case.get("answer_doc_refs", []))}
        context, answer = build_judge_input(result, legacy=True)
        legacy = judge.judge(question=case["query"], context=context, answer=answer)
        if not legacy.get("parse_ok"):
            continue
        rows.append({
            "id": case["id"],
            "answer_chars": len(case.get("answer", "")),
            "full_faithfulness": full["faithfulness"],
            "full_correctness": full["answer_correctness"],
            "legacy_faithfulness": legacy["faithfulness"],
            "legacy_correctness": legacy["answer_correctness"],
        })
        print(f"  {case['id']}: faith {legacy['faithfulness']:.2f} -> {full['faithfulness']:.2f}  "
              f"corr {legacy['answer_correctness']:.2f} -> {full['answer_correctness']:.2f}")

    summary = {
        "judge_model": args.model,
        "cases": len(rows),
        "avg_answer_chars": _mean([r["answer_chars"] for r in rows]),
        "legacy_input": {
            "avg_faithfulness": _mean([r["legacy_faithfulness"] for r in rows]),
            "avg_correctness": _mean([r["legacy_correctness"] for r in rows]),
        },
        "full_input": {
            "avg_faithfulness": _mean([r["full_faithfulness"] for r in rows]),
            "avg_correctness": _mean([r["full_correctness"] for r in rows]),
        },
    }
    print(json.dumps(summary, indent=2))
    Path(args.output).write_text(json.dumps({"summary": summary, "cases": rows}, indent=2))
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
