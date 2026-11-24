"""
Validate the cheap grounding checker against an LLM claim judge (ADR-013).

``src/core/grounding.py`` flags each answer sentence as supported or not
using embedding similarity + lexical overlap — fast and free, but blind to
negation and wrong numbers. This script asks an LLM, claim by claim, "is
this sentence supported by these passages?" and reports how often the two
agree (accuracy and Cohen's kappa). It also sweeps the checker's similarity
threshold to show what an in-sample-optimal threshold would be; that value
is reported, not adopted, because tuning on the same 25 answers would
overstate agreement.

Usage:
    python scripts/eval/claim_judge.py --results data/eval/sprint4_eval.json \
        --model gemma3:4b --output data/eval/claim_judge.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.eval.agreement import cohen_kappa, fetch_chunks, load_cases  # noqa: E402
from scripts.eval.judge import _call_ollama  # noqa: E402
from src.core.grounding import LEXICAL_THRESHOLD, SUPPORT_THRESHOLD  # noqa: E402

CLAIM_PROMPT = """\
You are checking one sentence from an answer about 3GPP specifications.
Decide whether the PASSAGES fully support the SENTENCE. "Supported" means a
reader of only the passages would accept every factual detail in the
sentence (names, numbers, relationships). Paraphrase is fine. Missing,
different or contradicted details mean NOT supported.

PASSAGES:
---
{passages}
---

SENTENCE: {claim}

Reply with JSON only: {{"supported": true or false, "reason": "<short reason>"}}
"""


def judge_claim(claim: str, passages: List[str], model: str, url: str) -> Dict:
    prompt = CLAIM_PROMPT.format(passages="\n\n".join(passages)[:6000], claim=claim)
    raw = None
    for attempt in range(2):  # Ollama occasionally 500s on a JSON-constrained decode
        try:
            raw = _call_ollama(prompt, model, url)
            break
        except Exception as exc:  # noqa: BLE001
            error = exc
    if raw is None:
        return {"supported": None, "reason": f"call_error: {error}", "parse_ok": False}
    try:
        data = json.loads(raw.strip().strip("`").removeprefix("json").strip())
        value = data.get("supported")
        if isinstance(value, str):
            value = value.strip().lower() == "true"
        return {"supported": bool(value), "reason": str(data.get("reason", "")), "parse_ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"supported": None, "reason": f"parse_error: {exc}", "parse_ok": False}


def sweep(rows: List[Dict]) -> Dict:
    """Best balanced accuracy over support thresholds (lexical fixed)."""
    best = {"threshold": None, "balanced_accuracy": 0.0}
    for t in [x / 100 for x in range(50, 96)]:
        tp = fn = tn = fp = 0
        for r in rows:
            pred = r["support"] >= t or r["lexical"] >= LEXICAL_THRESHOLD
            if r["llm"]:
                tp, fn = tp + pred, fn + (not pred)
            else:
                tn, fp = tn + (not pred), fp + pred
        tpr = tp / (tp + fn) if tp + fn else 0.0
        tnr = tn / (tn + fp) if tn + fp else 0.0
        bal = (tpr + tnr) / 2
        if bal > best["balanced_accuracy"]:
            best = {"threshold": t, "balanced_accuracy": round(bal, 3)}
    return best


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", default="data/eval/sprint4_eval.json")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--output", default="data/eval/claim_judge.json")
    args = parser.parse_args()

    rows: List[Dict] = []
    skipped = 0
    for case in load_cases(args.results):
        grounding = case.get("grounding") or {}
        claims = [c for c in grounding.get("claims", []) if not c.get("meta")]
        if case.get("is_out_of_corpus") or not claims:
            continue
        chunks = fetch_chunks(case.get("answer_doc_refs", []))
        texts = [c["text"] for c in chunks]
        for claim in claims:
            valid = [n for n in claim.get("citations", []) if 1 <= n <= len(texts)]
            targets = [texts[n - 1] for n in valid] if valid else texts
            verdict = judge_claim(claim["text"], targets, args.model, args.ollama_url)
            if not verdict["parse_ok"]:
                skipped += 1
                print(f"  skipped claim on {case['id']}: {verdict['reason'][:80]}")
                continue
            rows.append({
                "case": case["id"],
                "claim": claim["text"],
                "cited": claim.get("cited", False),
                "support": claim["support"],
                "lexical": claim["lexical"],
                "checker": bool(claim["supported"]),
                "llm": verdict["supported"],
                "llm_reason": verdict["reason"],
            })
            mark = "=" if rows[-1]["checker"] == rows[-1]["llm"] else "≠"
            print(f"  {mark} {case['id']} checker={rows[-1]['checker']!s:5} "
                  f"llm={rows[-1]['llm']!s:5} sim={claim['support']:.2f} | {claim['text'][:70]}")

    checker = [r["checker"] for r in rows]
    llm = [r["llm"] for r in rows]
    n = len(rows)
    both = lambda c, l: sum(1 for r in rows if r["checker"] is c and r["llm"] is l)  # noqa: E731
    summary = {
        "claims": n,
        "skipped_claims": skipped,
        "judge_model": args.model,
        "thresholds": {"support": SUPPORT_THRESHOLD, "lexical": LEXICAL_THRESHOLD},
        "accuracy": round(sum(c == l for c, l in zip(checker, llm)) / n, 3) if n else None,
        "cohen_kappa": cohen_kappa(checker, llm),
        "confusion": {
            "checker_yes_llm_yes": both(True, True),
            "checker_yes_llm_no": both(True, False),
            "checker_no_llm_yes": both(False, True),
            "checker_no_llm_no": both(False, False),
        },
        "llm_supported_rate": round(sum(llm) / n, 3) if n else None,
        "checker_supported_rate": round(sum(checker) / n, 3) if n else None,
        "in_sample_best_support_threshold": sweep(rows),
    }
    print(json.dumps(summary, indent=2))
    Path(args.output).write_text(json.dumps({"summary": summary, "claims": rows}, indent=2))
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
