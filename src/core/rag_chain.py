"""
RAG (Retrieval-Augmented Generation) chain

Ties together:
  1. DocumentRetriever  - finds relevant spec chunks via vector search
  2. OllamaLLM          - generates a grounded answer from those chunks
  3. Conversation memory - maintains multi-turn context

Usage:
    chain = RAGChain()
    result = chain.query("What is the gNB-CU architecture?")
    print(result["answer"])
    print(result["sources"])
"""
import logging
import time
from typing import List, Dict, Optional, Iterator

from src.core.retriever import DocumentRetriever
from src.core.llm import OllamaLLM

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """Based on the following excerpts from 3GPP technical specifications, \
please answer the question.

CONTEXT:
{context}

QUESTION:
{question}

Provide a clear, technically accurate answer. Cite the source documents where relevant."""


class RAGChain:
    """Full RAG pipeline: retrieve relevant chunks, then generate an answer."""

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        llm: Optional[OllamaLLM] = None,
        top_k: int = 5,
        max_history_turns: int = 5,
    ):
        """
        Args:
            retriever: DocumentRetriever instance (created with defaults if None)
            llm: OllamaLLM instance (created with defaults if None)
            top_k: Number of chunks to retrieve per query
            max_history_turns: How many prior Q&A pairs to keep in context
        """
        self.retriever = retriever or DocumentRetriever(top_k=top_k)
        self.llm = llm or OllamaLLM()
        self.max_history_turns = max_history_turns
        self._history: List[Dict[str, str]] = []

        logger.info(
            f"Initialized RAGChain (top_k={top_k}, "
            f"model={self.llm.model}, "
            f"history={max_history_turns})"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        source_filter: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Dict:
        """
        Run a single RAG query (blocking).

        Args:
            question: Natural language question
            source_filter: Restrict retrieval to a specific document name
            top_k: Override the default number of retrieved chunks

        Returns:
            {
                "answer":      str,
                "sources":     [{"source": str, "similarity": float, "text": str}],
                "context":     str,       # raw context fed to the LLM
                "query_time":  float,     # total seconds
                "retrieve_time": float,
                "generate_time": float,
            }
        """
        start = time.time()

        # 1. Retrieve relevant chunks
        t0 = time.time()
        docs = self.retriever.retrieve(
            question, top_k=top_k, source_filter=source_filter
        )
        retrieve_time = time.time() - t0

        if not docs:
            return self._empty_response(question, time.time() - start)

        # 2. Build the prompt
        context = self.retriever.format_context(docs)
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        # 3. Generate answer
        t0 = time.time()
        answer = self.llm.generate(prompt, history=self._get_history())
        generate_time = time.time() - t0

        # 4. Update conversation history
        self._add_to_history(question, answer)

        total_time = time.time() - start
        logger.info(
            f"Query completed in {total_time:.2f}s "
            f"(retrieve={retrieve_time:.2f}s, generate={generate_time:.2f}s)"
        )

        return {
            "answer": answer,
            "sources": [
                {
                    "source": d["source"],
                    "similarity": round(d["similarity"], 4),
                    "text": d["text"][:300] + "..." if len(d["text"]) > 300 else d["text"],
                }
                for d in docs
            ],
            "context": context,
            "query_time": round(total_time, 3),
            "retrieve_time": round(retrieve_time, 3),
            "generate_time": round(generate_time, 3),
        }

    def stream_query(
        self,
        question: str,
        source_filter: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Iterator[Dict]:
        """
        Stream a RAG query, yielding chunks as the LLM generates them.

        Yields dicts of two types:
          {"type": "sources", "sources": [...], "context": str}  -- sent first
          {"type": "token",   "token": str}                      -- one per LLM token
          {"type": "done",    "query_time": float}               -- sent last
        """
        start = time.time()

        docs = self.retriever.retrieve(
            question, top_k=top_k, source_filter=source_filter
        )

        if not docs:
            yield {"type": "sources", "sources": [], "context": ""}
            yield {"type": "token", "token": "No relevant documents found."}
            yield {"type": "done", "query_time": round(time.time() - start, 3)}
            return

        context = self.retriever.format_context(docs)
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        sources = [
            {
                "source": d["source"],
                "similarity": round(d["similarity"], 4),
                "text": d["text"][:300] + "..." if len(d["text"]) > 300 else d["text"],
            }
            for d in docs
        ]

        yield {"type": "sources", "sources": sources, "context": context}

        full_answer = []
        for token in self.llm.stream(prompt, history=self._get_history()):
            full_answer.append(token)
            yield {"type": "token", "token": token}

        self._add_to_history(question, "".join(full_answer))
        yield {"type": "done", "query_time": round(time.time() - start, 3)}

    def clear_history(self) -> None:
        """Reset conversation memory."""
        self._history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, str]]:
        """Return a copy of the current conversation history."""
        return list(self._history)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_history(self) -> List[Dict[str, str]]:
        """Return last N turns of history for the LLM."""
        return self._history[-(self.max_history_turns * 2):]

    def _add_to_history(self, question: str, answer: str) -> None:
        self._history.append({"role": "user", "content": question})
        self._history.append({"role": "assistant", "content": answer})

    def _empty_response(self, question: str, elapsed: float) -> Dict:
        logger.warning(f"No documents retrieved for: '{question}'")
        return {
            "answer": (
                "I could not find relevant information in the 3GPP specifications "
                "to answer your question. Please ensure the vector index is built "
                "and try rephrasing your query."
            ),
            "sources": [],
            "context": "",
            "query_time": round(elapsed, 3),
            "retrieve_time": 0.0,
            "generate_time": 0.0,
        }


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print("RAG Chain Test")
    print("=" * 60 + "\n")

    chain = RAGChain()

    if not chain.llm.is_available():
        print("Ollama is not running or model not pulled.")
        print(f"Run: ollama pull {chain.llm.model}")
        sys.exit(1)

    queries = [
        "What is the gNB-CU and gNB-DU split in NG-RAN?",
        "Explain the difference between SA and NSA 5G deployment options.",
    ]

    for q in queries:
        print(f"\nQ: {q}")
        print("-" * 50)
        result = chain.query(q)
        print(f"A: {result['answer']}")
        print(f"\nSources ({len(result['sources'])}):")
        for s in result["sources"]:
            print(f"  - {s['source']} (similarity={s['similarity']})")
        print(f"\nTiming: total={result['query_time']}s  "
              f"retrieve={result['retrieve_time']}s  "
              f"generate={result['generate_time']}s")
        print("=" * 60)
