"""
Agreement statistics and the human-calibration workflow for the LLM judge.

An LLM judge's scores are only as trustworthy as their agreement with a
human. This module provides:

  * ``cohen_kappa``            — chance-corrected agreement on nominal labels
                                 (used for claim-level supported / not).
  * ``weighted_kappa``         — quadratic-weighted kappa for ordinal 0-5
                                 judge scores (a 4 vs 5 disagreement costs
                                 far less than a 0 vs 5).
  * ``export`` sub-command     — writes a blind scoring sheet (CSV) plus a
                                 context file for N sampled answers; the
                                 judge's own scores are NOT in the sheet.
  * ``score`` sub-command      — reads the filled sheet and reports human vs
                                 judge agreement.

Usage:
    python scripts/eval/agreement.py export --results data/eval/sprint4_eval.json --n 20
    # ... fill human_faithfulness / human_correctness (0-5) in the CSV ...
    python scripts/eval/agreement.py score  --results data/eval/sprint4_eval.json

Pure stdlib (plus the vector store for ``export``, to print full chunks).
"""

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

SHEET = Path("data/eval/human_calibration.csv")
CONTEXT = Path("data/eval/human_calibration_context.md")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def cohen_kappa(a: Sequence, b: Sequence) -> Optional[float]:
    """Cohen's kappa for two raters over nominal labels.

    Returns None when undefined (no items, or both raters constant on the
    same single label, so chance agreement is 1).
    """
    if len(a) != len(b):
        raise ValueError("rater sequences must be the same length")
    n = len(a)
    if n == 0:
        return None
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[label] * cb[label] for label in set(ca) | set(cb)) / (n * n)
    if expected == 1.0:
        return None
    return round((observed - expected) / (1 - expected), 3)


def weighted_kappa(
    a: Sequence[int], b: Sequence[int], min_score: int = 0, max_score: int = 5
) -> Optional[float]:
    """Quadratic-weighted kappa for ordinal ratings in [min_score, max_score]."""
    if len(a) != len(b):
        raise ValueError("rater sequences must be the same length")
    n = len(a)
    if n == 0:
        return None
    k = max_score - min_score + 1
    observed = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        observed[x - min_score][y - min_score] += 1
    hist_a = [sum(row) for row in observed]
    hist_b = [sum(observed[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = ((i - j) ** 2) / ((k - 1) ** 2)
            num += w * observed[i][j]
            den += w * hist_a[i] * hist_b[j] / n
    if den == 0:
        return None
    return round(1 - num / den, 3)


def agreement_report(human: List[int], judge: List[int]) -> Dict:
    n = len(human)
    return {
        "n": n,
        "exact_agreement": round(sum(h == j for h, j in zip(human, judge)) / n, 3) if n else None,
        "within_one": round(sum(abs(h - j) <= 1 for h, j in zip(human, judge)) / n, 3) if n else None,
        "mean_human": round(sum(human) / n, 3) if n else None,
        "mean_judge": round(sum(judge) / n, 3) if n else None,
        "quadratic_weighted_kappa": weighted_kappa(human, judge),
    }


# ---------------------------------------------------------------------------
# Results-file helpers
# ---------------------------------------------------------------------------

def load_cases(results_path: str) -> List[Dict]:
    with open(results_path) as f:
        return json.load(f)["cases"]


def fetch_chunks(refs: List[Dict]) -> List[Dict]:
    """Re-fetch the exact chunks an answer was generated from, by id."""
    from src.core.vector_store import VectorStore

    ids = [r["id"] for r in refs if r.get("id")]
    if not ids:
        return []
    got = VectorStore().collection.get(ids=ids, include=["documents", "metadatas"])
    by_id = {i: (d, m) for i, d, m in zip(got["ids"], got["documents"], got["metadatas"])}
    return [
        {"id": i, "text": by_id[i][0], "source": by_id[i][1].get("source", "unknown")}
        for i in ids
        if i in by_id
    ]


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def export_sheet(results_path: str, n: int, seed: int) -> None:
    cases = [
        c for c in load_cases(results_path)
        if c.get("answer") and not c.get("is_out_of_corpus")
    ]
    random.Random(seed).shuffle(cases)
    sample = sorted(cases[:n], key=lambda c: c["id"])

    SHEET.parent.mkdir(parents=True, exist_ok=True)
    with open(SHEET, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "question", "answer", "human_faithfulness",
                         "human_correctness", "notes"])
        for c in sample:
            writer.writerow([c["id"], c["query"], c["answer"], "", "", ""])

    lines = [
        "# Human calibration — context for each answer",
        "",
        "Score each answer in `human_calibration.csv` on the judge's rubric "
        "(scripts/eval/judge.py), using only the context below:",
        "",
        "- **faithfulness 0-5**: 5 = every claim traces to the context; "
        "3 = one unsupported claim; 1 = several; 0 = ignores the context.",
        "- **correctness 0-5**: 5 = accurate and complete given the context; "
        "3 = partial; 1 = mostly wrong; 0 = does not address the question.",
        "",
        "The judge's scores are deliberately not shown. Score blind.",
        "",
    ]
    for c in sample:
        lines += [f"## {c['id']}: {c['query']}", "", "### Answer", "", c["answer"], "",
                  "### Context", ""]
        for j, chunk in enumerate(fetch_chunks(c.get("answer_doc_refs", [])), 1):
            lines += [f"**[D{j}] {chunk['source']}**", "", chunk["text"], ""]
    CONTEXT.write_text("\n".join(lines))
    print(f"Wrote {len(sample)} cases to {SHEET} and context to {CONTEXT}")


def score_sheet(results_path: str) -> Dict:
    judged = {
        c["id"]: c["llm_judge"] for c in load_cases(results_path)
        if c.get("llm_judge", {}).get("parse_ok")
    }
    pairs = {"faithfulness": ([], []), "answer_correctness": ([], [])}
    with open(SHEET) as f:
        for row in csv.DictReader(f):
            j = judged.get(row["id"])
            if not j:
                continue
            for axis, col in (("faithfulness", "human_faithfulness"),
                              ("answer_correctness", "human_correctness")):
                if row[col].strip():
                    pairs[axis][0].append(int(row[col]))
                    pairs[axis][1].append(int(j[f"{axis}_raw"]))
    report = {axis: agreement_report(h, j) for axis, (h, j) in pairs.items()}
    print(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    exp = sub.add_parser("export", help="write a blind human scoring sheet")
    exp.add_argument("--results", default="data/eval/sprint4_eval.json")
    exp.add_argument("--n", type=int, default=20)
    exp.add_argument("--seed", type=int, default=7)
    sc = sub.add_parser("score", help="compare the filled sheet with the judge")
    sc.add_argument("--results", default="data/eval/sprint4_eval.json")
    args = parser.parse_args()
    if args.cmd == "export":
        export_sheet(args.results, args.n, args.seed)
    else:
        score_sheet(args.results)


if __name__ == "__main__":
    main()
