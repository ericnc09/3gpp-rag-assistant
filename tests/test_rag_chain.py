"""
Tests for src/core/rag_chain.py

All external dependencies (retriever, LLM) are mocked so tests run without
a live vector store or Ollama server.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_DOCS = [
    {
        "text": "The gNB-CU is a logical node that handles RRC and PDCP protocols.",
        "source": "38300-g30.docx",
        "chunk_index": 0,
        "similarity": 0.92,
    },
    {
        "text": "The gNB-DU is connected to the gNB-CU via the F1 interface.",
        "source": "38401-g30.docx",
        "chunk_index": 1,
        "similarity": 0.87,
    },
]


def _make_chain(docs=None, llm_answer="Test answer from LLM."):
    """Build a RAGChain with mocked retriever and LLM."""
    from src.core.rag_chain import RAGChain

    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = docs if docs is not None else SAMPLE_DOCS
    mock_retriever.format_context.return_value = "\n".join(
        d["text"] for d in (docs or SAMPLE_DOCS)
    )

    mock_llm = MagicMock()
    mock_llm.model = "llama3.2"
    mock_llm.generate.return_value = llm_answer

    chain = RAGChain(retriever=mock_retriever, llm=mock_llm)
    return chain, mock_retriever, mock_llm


# ---------------------------------------------------------------------------
# RAGChain.query tests
# ---------------------------------------------------------------------------

class TestRAGChainQuery:
    def test_query_returns_required_keys(self):
        chain, _, _ = _make_chain()
        result = chain.query("What is gNB-CU?")
        for key in ("answer", "sources", "context", "query_time",
                    "retrieve_time", "generate_time"):
            assert key in result

    def test_query_answer_from_llm(self):
        chain, _, _ = _make_chain(llm_answer="The gNB-CU handles PDCP.")
        result = chain.query("Explain gNB-CU")
        assert result["answer"] == "The gNB-CU handles PDCP."

    def test_query_sources_structure(self):
        chain, _, _ = _make_chain()
        result = chain.query("gNB architecture")
        assert len(result["sources"]) == 2
        for s in result["sources"]:
            assert "source" in s
            assert "similarity" in s
            assert "text" in s

    def test_query_passes_source_filter(self):
        chain, mock_retriever, _ = _make_chain()
        chain.query("gNB", source_filter="38300")
        mock_retriever.retrieve.assert_called_once_with(
            "gNB", top_k=None, source_filter="38300",
            domain=None, generation=None,
        )

    def test_query_passes_top_k_override(self):
        chain, mock_retriever, _ = _make_chain()
        chain.query("gNB", top_k=3)
        mock_retriever.retrieve.assert_called_once_with(
            "gNB", top_k=3, source_filter=None,
            domain=None, generation=None,
        )

    def test_query_empty_result_when_no_docs(self):
        chain, _, _ = _make_chain(docs=[])
        result = chain.query("unknown topic")
        assert result["sources"] == []
        assert "could not find" in result["answer"].lower()

    def test_query_times_are_non_negative(self):
        chain, _, _ = _make_chain()
        result = chain.query("timing test")
        assert result["query_time"] >= 0
        assert result["retrieve_time"] >= 0
        assert result["generate_time"] >= 0


# ---------------------------------------------------------------------------
# RAGChain conversation history tests
# ---------------------------------------------------------------------------

class TestRAGChainHistory:
    def test_history_accumulates_across_queries(self):
        chain, _, mock_llm = _make_chain()
        chain.query("First question")
        chain.query("Second question")
        # After 2 queries the history should have 4 messages (2 user + 2 assistant)
        assert len(chain.get_history()) == 4

    def test_clear_history_resets(self):
        chain, _, _ = _make_chain()
        chain.query("First question")
        chain.clear_history()
        assert chain.get_history() == []

    def test_history_sent_to_llm(self):
        chain, _, mock_llm = _make_chain()
        chain.query("First question")
        chain.query("Follow-up question")
        second_call_kwargs = mock_llm.generate.call_args_list[1][1]
        history = second_call_kwargs.get("history", [])
        assert len(history) >= 2  # at least the first turn


# ---------------------------------------------------------------------------
# RAGChain.stream_query tests
# ---------------------------------------------------------------------------

class TestRAGChainStream:
    def test_stream_yields_sources_first(self):
        chain, _, mock_llm = _make_chain()
        mock_llm.stream.return_value = iter(["Answer ", "here."])

        chunks = list(chain.stream_query("gNB?"))
        first = chunks[0]
        assert first["type"] == "sources"
        assert isinstance(first["sources"], list)

    def test_stream_yields_tokens(self):
        chain, _, mock_llm = _make_chain()
        mock_llm.stream.return_value = iter(["Hello", " world"])

        tokens = [c["token"] for c in chain.stream_query("hi") if c["type"] == "token"]
        assert tokens == ["Hello", " world"]

    def test_stream_ends_with_done(self):
        chain, _, mock_llm = _make_chain()
        mock_llm.stream.return_value = iter(["ok"])

        chunks = list(chain.stream_query("test"))
        last = chunks[-1]
        assert last["type"] == "done"
        assert "query_time" in last

    def test_stream_empty_docs(self):
        chain, _, _ = _make_chain(docs=[])
        chunks = list(chain.stream_query("nothing"))
        types = [c["type"] for c in chunks]
        assert types == ["sources", "token", "done"]


# ---------------------------------------------------------------------------
# Claim-level grounding (ADR-013)
# ---------------------------------------------------------------------------

class TestRAGChainGrounding:
    def _chain(self, mock_llm, answer, grounding=True):
        from unittest.mock import MagicMock
        from src.core.rag_chain import RAGChain

        retriever = MagicMock()
        retriever.retrieve.return_value = [
            {"text": "The AMF performs registration management for the UE.",
             "source": "23501.docx", "similarity": 0.8},
        ]
        retriever.format_context.return_value = "[Document 1] ..."
        retriever.embedding_generator.generate_embedding.side_effect = (
            lambda t: [float(len(t) % 7), 1.0, 0.5])
        retriever.embedding_generator.generate_embeddings_batch.side_effect = (
            lambda texts, show_progress_bar=True: [[float(len(t) % 7), 1.0, 0.5] for t in texts])
        mock_llm.generate.return_value = answer
        return RAGChain(retriever=retriever, llm=mock_llm, grounding=grounding)

    def test_query_includes_grounding_report(self, mock_llm):
        chain = self._chain(mock_llm, "The AMF performs registration management for the UE [D1].")
        result = chain.query("What does the AMF do?")
        assert result["grounding"]["n_claims"] == 1
        assert result["grounding"]["citation_coverage"] == 1.0

    def test_grounding_disabled(self, mock_llm):
        chain = self._chain(mock_llm, "The AMF performs registration [D1].", grounding=False)
        assert "grounding" not in chain.query("What does the AMF do?")

    def test_grounding_failure_never_loses_answer(self, mock_llm):
        chain = self._chain(mock_llm, "The AMF performs registration management [D1].")
        chain.grounding_checker.check = lambda *a: (_ for _ in ()).throw(RuntimeError("boom"))
        result = chain.query("What does the AMF do?")
        assert result["answer"].startswith("The AMF")
        assert "grounding" not in result

    def test_prompt_asks_for_dn_citations(self):
        from src.core.rag_chain import PROMPT_TEMPLATE
        assert "[D1]" in PROMPT_TEMPLATE and "[17]" in PROMPT_TEMPLATE


class TestRAGChainConversational:
    """Follow-up rewriting and clause expansion (ADR-014)."""

    def _chain(self, rewrite_to="Which protocol runs on the F1-C control plane?", expand=False):
        from src.core.rag_chain import RAGChain

        retriever = MagicMock()
        retriever.retrieve.return_value = SAMPLE_DOCS
        retriever.format_context.return_value = "[Document 1] ..."
        retriever.expand_to_clauses.side_effect = lambda docs: [dict(d, expanded=True) for d in docs]
        llm = MagicMock()
        llm.model = "llama3.2"
        # First generate() call is the answer; later ones may be rewrites.
        llm.generate.side_effect = lambda prompt, **kw: (
            rewrite_to if "Standalone question:" in prompt else "Answer [D1].")
        llm.stream.return_value = iter(["Answer"])
        chain = RAGChain(retriever=retriever, llm=llm, rewrite=True, clause_expand=expand)
        return chain, retriever, llm

    def test_first_question_not_rewritten(self):
        chain, retriever, llm = self._chain()
        result = chain.query("What is the F1 interface?")
        assert result["search_query"] == "What is the F1 interface?"
        assert result["rewrite_method"] == "none"
        assert llm.generate.call_count == 1

    def test_follow_up_retrieves_with_rewrite_but_answers_original(self):
        chain, retriever, llm = self._chain()
        chain.query("What is the F1 interface?")
        result = chain.query("Which protocol runs on its control plane?")
        assert retriever.retrieve.call_args.args[0] == "Which protocol runs on the F1-C control plane?"
        assert result["rewrite_method"] == "llm"
        answer_prompt = llm.generate.call_args.args[0]
        assert "Which protocol runs on its control plane?" in answer_prompt
        assert chain.get_history()[-2]["content"] == "Which protocol runs on its control plane?"

    def test_stream_reports_search_query(self):
        chain, retriever, llm = self._chain()
        chain._add_to_history("What is the F1 interface?", "F1 connects CU and DU.")
        first = next(chain.stream_query("And its user plane?"))
        assert first["type"] == "sources"
        assert first["search_query"] == "Which protocol runs on the F1-C control plane?"

    def test_rewrite_disabled(self):
        from src.core.rag_chain import RAGChain
        chain = RAGChain(retriever=MagicMock(), llm=MagicMock(), rewrite=False)
        assert chain.rewriter is None
        assert chain.search_query("And its user plane?") == {"query": "And its user plane?",
                                                             "method": "none"}

    def test_clause_expansion_applied_when_enabled(self):
        chain, retriever, _ = self._chain(expand=True)
        chain.query("What is the F1 interface?")
        retriever.expand_to_clauses.assert_called_once()
        assert all(d.get("expanded") for d in retriever.format_context.call_args.args[0])

    def test_clause_expansion_off(self):
        chain, retriever, _ = self._chain(expand=False)
        chain.query("What is the F1 interface?")
        retriever.expand_to_clauses.assert_not_called()

    def test_sources_carry_clause_ref(self):
        from src.core.rag_chain import RAGChain
        src = RAGChain._format_source({"text": "t", "source": "38401.docx", "similarity": 0.5,
                                       "spec_number": "38.401", "clause": "8.4.1",
                                       "clause_title": "Addition"})
        assert src["clause_ref"] == "TS 38.401 §8.4.1"
        assert src["clause_title"] == "Addition"
