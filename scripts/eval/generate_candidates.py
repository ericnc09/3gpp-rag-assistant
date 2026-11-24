"""
Generate *candidate* golden-set questions from spec chunks (Sprint 4).

The golden set has 30 hand-written queries, so one query moves hit-rate by
0.04. This script drafts more: it samples substantive chunks evenly across
the 37 indexed specs and asks a local LLM to write one question each chunk
answers, plus the keywords an answer must contain.

Output goes to ``data/eval/golden_candidates.jsonl`` with
``"status": "needs_review"``. Candidates are NOT golden: a generated
question can be trivially lexical, leak the chunk's wording, or be
answerable from several specs. Nothing here is merged into
``golden_set.jsonl`` or used in reported metrics until a human has accepted
it (set ``status`` to ``accepted`` and fix ``relevant_sources``).

Usage:
    python scripts/eval/generate_candidates.py --per-spec 2 --model llama3.2
"""

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.eval.judge import _call_ollama  # noqa: E402

OUT = Path("data/eval/golden_candidates.jsonl")

PROMPT = """\
You write evaluation questions for a search system over 3GPP specifications.
Read the PASSAGE from {spec} and write ONE question that:
- an engineer might genuinely ask,
- is fully answered by this passage,
- does NOT copy a whole sentence from the passage,
- names the technology (e.g. NR, LTE, 5GC) so it is not ambiguous.

PASSAGE:
---
{text}
---

Reply with JSON only:
{{"question": "...", "expected_keywords": ["3-5 lowercase terms an answer must contain"],
  "expected_fact": "one sentence the answer must state"}}
"""

# Boilerplate that makes useless questions: tables of contents, change
# history, foreword/scope, reference lists, abbreviation lists.
_BOILERPLATE = re.compile(
    r"(\.{5,}|Contents|Foreword|Change history|\bScope\b|Abbreviations|"
    r"References\b|The present document|Release \d+\)\s*\d+\s*3GPP)",
    re.IGNORECASE,
)


def substantive(text: str) -> bool:
    if len(text) < 700 or _BOILERPLATE.search(text[:300]):
        return False
    letters = sum(ch.isalpha() for ch in text)
    return letters / max(len(text), 1) > 0.6  # skip tables of numbers


def sample_chunks(per_spec: int, seed: int) -> List[Dict]:
    from src.core.vector_store import VectorStore

    collection = VectorStore().collection
    by_spec: Dict[str, List[Dict]] = defaultdict(list)
    total = collection.count()
    for offset in range(0, total, 5000):
        page = collection.get(include=["documents", "metadatas"], limit=5000, offset=offset)
        for cid, text, meta in zip(page["ids"], page["documents"], page["metadatas"]):
            spec = meta.get("spec_number", "unknown")
            if spec != "unknown" and substantive(text):
                by_spec[spec].append({"id": cid, "text": text, "spec": spec,
                                      "source": meta.get("source")})
    rng = random.Random(seed)
    picked = []
    for spec in sorted(by_spec):
        pool = by_spec[spec]
        picked += rng.sample(pool, min(per_spec, len(pool)))
    return picked


def draft(chunk: Dict, model: str, url: str) -> Optional[Dict]:
    raw = _call_ollama(PROMPT.format(spec=f"TS {chunk['spec']}", text=chunk["text"][:2500]),
                       model, url)
    try:
        data = json.loads(raw)
        question = str(data["question"]).strip()
        if not question.endswith("?") or len(question.split()) < 5:
            return None
        return {
            "question": question,
            "expected_keywords": [str(k).lower() for k in data.get("expected_keywords", [])][:5],
            "expected_fact": str(data.get("expected_fact", "")).strip(),
        }
    except Exception:  # noqa: BLE001 - malformed drafts are simply skipped
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-spec", type=int, default=2)
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    chunks = sample_chunks(args.per_spec, args.seed)
    print(f"Sampled {len(chunks)} substantive chunks across "
          f"{len({c['spec'] for c in chunks})} specs")
    written = 0
    with open(OUT, "w") as f:
        for i, chunk in enumerate(chunks, 1):
            d = draft(chunk, args.model, args.ollama_url)
            if d is None:
                print(f"  [{i}/{len(chunks)}] TS {chunk['spec']}: skipped (malformed draft)")
                continue
            written += 1
            record = {
                "id": f"cand-{written:03d}",
                "query": d["question"],
                "relevant_sources": [chunk["spec"].replace(".", "")],
                "expected_keywords": d["expected_keywords"],
                "expected_facts": [d["expected_fact"]] if d["expected_fact"] else [],
                "spec_refs": [f"TS {chunk['spec']}"],
                "status": "needs_review",
                "generated_by": args.model,
                "source_chunk_id": chunk["id"],
                "source_excerpt": chunk["text"][:300],
                "notes": "LLM-drafted from one chunk; relevant_sources lists only the "
                         "source spec and may be incomplete. Review before use.",
            }
            f.write(json.dumps(record) + "\n")
            print(f"  [{i}/{len(chunks)}] TS {chunk['spec']}: {d['question']}")
    print(f"Wrote {written} candidates to {OUT} (status: needs_review)")


if __name__ == "__main__":
    main()
