"""
Claim-level citation and grounding check (Sprint 4, ADR-013).

An answer-level faithfulness score ("0.64") says nothing about *which*
sentence is unsupported. This module breaks an answer into claims
(sentences / bullet items), reads the inline citations the prompt asks for
(``[2]``, ``[Document 2]``), and scores each claim against the retrieved
chunks it cites:

  * ``support``   — max cosine similarity between the claim and any sentence
                    window of the cited chunk(s), using the same bge-small
                    model as retrieval (no extra model, no LLM call).
  * ``lexical``   — fraction of the claim's content tokens that appear in
                    the cited chunk(s) (identifier-preserving tokenizer from
                    ``bm25.py``), so exact identifiers count.

A claim is ``supported`` when either signal clears its threshold. Uncited
claims are scored against all retrieved chunks, so the report separates
"true but uncited" from "not in the context at all".

This is a cheap, deterministic proxy, not entailment: similarity cannot see
a negation or a wrong number. Its agreement with an LLM claim judge is
measured in ``scripts/eval/claim_judge.py`` and reported in EVAL_REPORT §6b;
treat the per-claim flags as triage for a reader, not as a verdict.
"""

from __future__ import annotations

import math
import re
from typing import Callable, Dict, List, Optional, Sequence

from src.core.bm25 import tokenize

# Thresholds chosen a priori (before the claim-judge comparison) from the
# bge-small similarity scale used elsewhere in this repo: the eval's
# calibrated pass threshold is 0.42 *query*-to-chunk; a claim restating a
# chunk sentence sits well above that. EVAL_REPORT §6b reports how these
# fixed values agree with the LLM claim judge.
SUPPORT_THRESHOLD = 0.75
LEXICAL_THRESHOLD = 0.70
MIN_CLAIM_WORDS = 5

# Citation markers the prompt asks for ([D1], [D2, D3]) plus the forms models
# fall back to ([Document 1], (Document 2), "Document 3"). A bare [17] is
# also read as a citation; in 3GPP text it is often the spec's own
# bibliography marker copied from a chunk, and it surfaces as an *invalid*
# citation (no 17th retrieved doc), which is what it is from the reader's
# side. The prompt's [Dn] form exists to avoid that collision.
_CITATION_RE = re.compile(
    r"\[(?:Document|Doc\.?|Source|D)?\s*(\d+(?:\s*(?:,|;|and|&)\s*(?:Document|D)?\s*\d+)*)\]"
    r"|\((?:Document|Doc\.?|D)\s*(\d+(?:\s*(?:,|;|and|&)\s*(?:D)?\s*\d+)*)\)"
    r"|\bDocument\s+(\d+)\b",
    re.IGNORECASE,
)

# Sentences about the context itself ("the context does not specify...")
# are hedges or refusals, not factual claims; they are kept for display
# but excluded from the grounding metrics.
_META_RE = re.compile(
    r"\b(?:the\s+)?(?:provided\s+)?(?:context|documents?|sources?|information)\s+"
    r"(?:provided\s+)?(?:does|do|did)\s+not\b"
    r"|\bnot\s+(?:enough|sufficient)\s+information\b"
    r"|\b(?:based\s+on|according\s+to)\s+the\s+(?:provided\s+)?context\s*,?\s*(?:it\s+is\s+)?(?:unclear|not)\b"
    r"|\bI\s+(?:cannot|can't|could\s+not|don't|do\s+not)\b"
    # "...is not (explicitly) specified/stated/mentioned in the (provided)
    # context/documents" — added after the 2026-11-20 claim-judge review
    # found these counted as ungrounded claims.
    r"|\bnot\s+(?:explicitly\s+|directly\s+|clearly\s+)?"
    r"(?:specified|stated|mentioned|described|defined|provided|covered|addressed)\s+"
    r"(?:in|by)\s+the\s+(?:provided\s+|given\s+|retrieved\s+)?(?:context|documents?|passages?|sources?)\b",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\[(*])")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_MARKDOWN_RE = re.compile(r"[*_`#>]+")

EmbedFn = Callable[[str], Sequence[float]]


def parse_citations(text: str) -> List[int]:
    """Document numbers cited in a piece of text, in order, de-duplicated."""
    found: List[int] = []
    for match in _CITATION_RE.finditer(text):
        group = next(g for g in match.groups() if g)
        for num in re.findall(r"\d+", group):
            n = int(num)
            if n not in found:
                found.append(n)
    return found


def strip_citations(text: str) -> str:
    text = re.sub(r"\s{2,}", " ", _CITATION_RE.sub("", text))
    return re.sub(r"\s+([.,;:!?])", r"\1", text).strip()


def split_claims(answer: str, min_words: int = MIN_CLAIM_WORDS) -> List[Dict]:
    """Split an answer into claims, each with the citations attached to it.

    Bullets and lines are split first, then sentences. Short fragments and
    headings (ending in ':') are dropped — they assert nothing checkable.
    """
    claims: List[Dict] = []
    for line in answer.splitlines():
        line = _BULLET_RE.sub("", line).strip()
        if not line:
            continue
        for sentence in _SENTENCE_SPLIT_RE.split(line):
            sentence = sentence.strip()
            clean = _MARKDOWN_RE.sub("", strip_citations(sentence)).strip()
            if len(clean.split()) < min_words or clean.endswith(":"):
                continue
            claims.append(
                {
                    "text": clean,
                    "raw": sentence,
                    "citations": parse_citations(sentence),
                    "meta": bool(_META_RE.search(clean)),
                }
            )
    return claims


def _windows(text: str, size: int = 2) -> List[str]:
    """Overlapping sentence windows of a chunk (claims often span 2 sentences)."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?;])\s+", text) if s.strip()]
    if len(sentences) <= size:
        return [" ".join(sentences)] if sentences else []
    return [" ".join(sentences[i : i + size]) for i in range(len(sentences) - size + 1)]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def lexical_overlap(claim: str, passage: str) -> float:
    """Fraction of the claim's content tokens present in the passage."""
    claim_tokens = set(tokenize(claim))
    if not claim_tokens:
        return 0.0
    return len(claim_tokens & set(tokenize(passage))) / len(claim_tokens)


class GroundingChecker:
    """Score each claim of an answer against the retrieved chunks.

    Args:
        embed_fn: ``text -> vector`` (pass the retriever's embedding model so
            no extra model is loaded). Chunk windows are embedded once per
            ``check`` call and cached by text.
        embed_batch_fn: optional batched variant, used when available.
    """

    def __init__(
        self,
        embed_fn: EmbedFn,
        embed_batch_fn: Optional[Callable[[List[str]], List[Sequence[float]]]] = None,
        support_threshold: float = SUPPORT_THRESHOLD,
        lexical_threshold: float = LEXICAL_THRESHOLD,
    ) -> None:
        self.embed_fn = embed_fn
        self.embed_batch_fn = embed_batch_fn
        self.support_threshold = support_threshold
        self.lexical_threshold = lexical_threshold

    def _embed_many(self, texts: List[str]) -> List[Sequence[float]]:
        if self.embed_batch_fn is not None:
            return self.embed_batch_fn(texts)
        return [self.embed_fn(t) for t in texts]

    def check(self, answer: str, docs: List[Dict]) -> Dict:
        """Return per-claim scores and answer-level grounding metrics.

        ``docs`` are the retrieved chunks in prompt order, so citation ``[n]``
        refers to ``docs[n-1]``.
        """
        claims = split_claims(answer)
        n_docs = len(docs)
        if not claims or not docs:
            return self._summary(claims, n_docs)

        windows_per_doc = [_windows(d.get("text", "")) for d in docs]
        flat = [w for ws in windows_per_doc for w in ws]
        vectors = self._embed_many(flat + [c["text"] for c in claims])
        window_vecs, claim_vecs = vectors[: len(flat)], vectors[len(flat) :]

        doc_window_vecs: List[List[Sequence[float]]] = []
        pos = 0
        for ws in windows_per_doc:
            doc_window_vecs.append(window_vecs[pos : pos + len(ws)])
            pos += len(ws)

        for claim, cvec in zip(claims, claim_vecs):
            valid = [n for n in claim["citations"] if 1 <= n <= n_docs]
            claim["invalid_citations"] = [n for n in claim["citations"] if n not in valid]
            claim["cited"] = bool(valid)
            per_doc = [
                (
                    max((_cosine(cvec, w) for w in doc_window_vecs[i]), default=0.0),
                    lexical_overlap(claim["text"], docs[i].get("text", "")),
                )
                for i in range(n_docs)
            ]

            def best(indices):
                if not indices:
                    return None, 0.0, 0.0
                i = max(indices, key=lambda j: per_doc[j])
                return i + 1, per_doc[i][0], per_doc[i][1]

            def passes(sim, lex):
                return sim >= self.support_threshold or lex >= self.lexical_threshold

            # `supported`: cited claims are judged only against what they
            # cite; uncited claims against everything retrieved.
            # `grounded`: supported by *any* retrieved chunk.
            targets = [n - 1 for n in valid] if valid else list(range(n_docs))
            doc, sim, lex = best(targets)
            claim["support"] = round(sim, 3)
            claim["lexical"] = round(lex, 3)
            claim["best_doc"] = doc
            claim["supported"] = passes(sim, lex)
            any_doc, any_sim, any_lex = best(list(range(n_docs)))
            claim["grounded"] = passes(any_sim, any_lex)
            claim["grounded_doc"] = any_doc
        return self._summary(claims, n_docs)

    @staticmethod
    def _summary(claims: List[Dict], n_docs: int) -> Dict:
        factual = [c for c in claims if not c.get("meta")]
        n = len(factual)
        cited = [c for c in factual if c.get("cited")]
        grounded = [c for c in factual if c.get("grounded")]
        return {
            "claims": claims,
            "n_claims": n,
            "n_meta": len(claims) - n,
            "n_docs": n_docs,
            # Share of claims carrying at least one valid [n] citation.
            "citation_coverage": round(len(cited) / n, 3) if n else None,
            # Of the cited claims, share whose cited chunk supports them.
            "citation_precision": (
                round(sum(1 for c in cited if c.get("supported")) / len(cited), 3)
                if cited
                else None
            ),
            # Share of all claims supported by some retrieved chunk.
            "grounded_ratio": round(len(grounded) / n, 3) if n else None,
            "invalid_citations": sum(len(c.get("invalid_citations", [])) for c in claims),
            "ungrounded_claims": [c["text"] for c in factual if not c.get("grounded")],
        }


def public_report(report: Optional[Dict]) -> Optional[Dict]:
    """Trim a grounding report to the shape the API and UI expose."""
    if not report:
        return None
    keep = (
        "n_claims",
        "citation_coverage",
        "citation_precision",
        "grounded_ratio",
        "invalid_citations",
    )
    return {
        **{k: report.get(k) for k in keep},
        "claims": [
            {
                "text": c["text"],
                "citations": c.get("citations", []),
                "cited": c.get("cited", False),
                "supported": c.get("supported", False),
                "grounded": c.get("grounded", False),
                "support": c.get("support", 0.0),
            }
            for c in report.get("claims", [])
            if not c.get("meta")
        ],
    }
