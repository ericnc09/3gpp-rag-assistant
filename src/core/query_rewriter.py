"""
Follow-up question rewriting for conversational retrieval (Sprint 2, ADR-014).

The chain already passes chat history to the LLM, but retrieval only sees the
latest message. "Which protocol runs on its control plane?" after a question
about F1 retrieves nothing about F1: the referent lives in the history.

``QueryRewriter`` turns a follow-up plus recent history into a standalone
search query before retrieval. The answer prompt still uses the user's
original wording; only the search text changes.

  * No history, or a question that already names its subject and has no
    anaphora → returned unchanged, no LLM call.
  * Otherwise one short LLM call ("rewrite as a standalone question").
  * If the LLM fails or returns something unusable → fallback: the previous
    user question prepended to the follow-up, which still puts the referent
    into both the dense and BM25 query.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """\
Rewrite the user's last message as ONE standalone search query about 3GPP \
specifications. Replace pronouns and references such as "it", "its", "they", \
"that procedure" or "the same" with the exact names they refer to in the \
conversation. Keep every technical term, interface and spec number. Do not \
answer the question. Output only the rewritten question.

Conversation:
{history}

Last message: {question}

Standalone question:"""

# Words that only make sense with a referent from earlier turns.
_ANAPHORA_RE = re.compile(
    r"\b(?:it|its|it's|they|them|their|theirs|this|that|these|those|"
    r"the same|the former|the latter|above|previous|mentioned|"
    r"what about|how about|and what|and how|also|instead|"
    r"compared|in contrast|difference|differ)\b",
    re.IGNORECASE,
)
# Openers of elliptical follow-ups: "And for LTE?", "What about Xn?"
_ELLIPSIS_RE = re.compile(r"^\s*(?:and|or|but|so|then|what about|how about)\b", re.IGNORECASE)
MAX_HISTORY_CHARS = 600  # per assistant turn; the subject is usually up front
MAX_QUERY_CHARS = 300


def needs_rewrite(question: str, history: Optional[List[Dict[str, str]]]) -> bool:
    """True when the question likely depends on earlier turns."""
    if not history:
        return False
    if _ELLIPSIS_RE.search(question) or _ANAPHORA_RE.search(question):
        return True
    return len(question.split()) <= 4  # "Which spec?", "Explain more"


def _last_user_turn(history: List[Dict[str, str]]) -> Optional[str]:
    for turn in reversed(history):
        if turn.get("role") == "user" and turn.get("content", "").strip():
            return turn["content"].strip()
    return None


def fallback_query(question: str, history: List[Dict[str, str]]) -> str:
    previous = _last_user_turn(history)
    return f"{previous} {question}" if previous else question


def format_history(history: List[Dict[str, str]], max_turns: int = 4) -> str:
    lines = []
    for turn in history[-max_turns * 2 :]:
        content = re.sub(r"\s+", " ", turn.get("content", "")).strip()
        if turn.get("role") == "assistant":
            content = content[:MAX_HISTORY_CHARS]
        role = "User" if turn.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def clean_rewrite(text: str) -> Optional[str]:
    """Take the first non-empty line, strip quotes/labels; None if unusable."""
    for line in (text or "").splitlines():
        line = line.strip().strip('"').strip("'").strip()
        line = re.sub(r"^(?:standalone question|rewritten question|query)\s*:\s*", "", line,
                      flags=re.IGNORECASE)
        if line:
            if len(line) > MAX_QUERY_CHARS or len(line.split()) < 3:
                return None
            return line
    return None


class QueryRewriter:
    """Rewrite follow-ups into standalone search queries.

    Args:
        llm: any object with ``generate(prompt, ...) -> str`` (OllamaLLM,
            GroqLLM). ``None`` disables the LLM and always uses the fallback.
        always: rewrite whenever there is history, skipping the heuristic gate.
    """

    def __init__(self, llm=None, always: bool = False) -> None:
        self.llm = llm
        self.always = always

    def rewrite(self, question: str, history: Optional[List[Dict[str, str]]]) -> Dict:
        """Return ``{"query", "method"}``; method is none | llm | fallback."""
        if not history or not (self.always or needs_rewrite(question, history)):
            return {"query": question, "method": "none"}
        if self.llm is not None:
            try:
                prompt = REWRITE_PROMPT.format(history=format_history(history), question=question)
                raw = self.llm.generate(prompt)
                cleaned = clean_rewrite(raw)
                if cleaned:
                    return {"query": cleaned, "method": "llm"}
                logger.info("Unusable rewrite %r; using fallback", (raw or "")[:80])
            except Exception as exc:  # noqa: BLE001 - retrieval must still run
                logger.warning("Query rewrite failed (%s); using fallback", exc)
        return {"query": fallback_query(question, history), "method": "fallback"}
