"""
Tests for src/core/retriever.py (DocumentRetriever)

VectorStore and LocalEmbeddingGenerator are mocked via conftest fixtures.
"""
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def retriever(mock_vector_store, mock_embedding_generator):
    from src.core.retriever import DocumentRetriever
    return DocumentRetriever(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator,
        top_k=5,
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestRetrieverInit:
    def test_default_top_k(self, mock_vector_store, mock_embedding_generator):
        from src.core.retriever import DocumentRetriever
        ret = DocumentRetriever(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator,
        )
        assert ret.top_k == 5

    def test_custom_top_k(self, mock_vector_store, mock_embedding_generator):
        from src.core.retriever import DocumentRetriever
        ret = DocumentRetriever(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator,
            top_k=10,
        )
        assert ret.top_k == 10


# ---------------------------------------------------------------------------
# retrieve
# ---------------------------------------------------------------------------

class TestRetrieve:
    def test_returns_list(self, retriever):
        results = retriever.retrieve("What is gNB?")
        assert isinstance(results, list)

    def test_result_has_required_keys(self, retriever):
        results = retriever.retrieve("What is gNB?")
        assert len(results) > 0
        for doc in results:
            assert "text" in doc
            assert "source" in doc
            assert "similarity" in doc
            assert "chunk_index" in doc

    def test_similarity_between_zero_and_one(self, retriever):
        results = retriever.retrieve("protocol stack")
        for doc in results:
            assert 0.0 <= doc["similarity"] <= 1.0

    def test_calls_embedding_generator(self, retriever, mock_embedding_generator):
        retriever.retrieve("test query")
        mock_embedding_generator.generate_embedding.assert_called_once_with("test query")

    def test_calls_vector_store_query(self, retriever, mock_vector_store):
        retriever.retrieve("test query")
        mock_vector_store.query.assert_called_once()

    def test_top_k_override(self, retriever, mock_vector_store):
        retriever.retrieve("query", top_k=3)
        call_kwargs = mock_vector_store.query.call_args[1]
        # With source_filter=None, n_results == top_k
        assert call_kwargs["n_results"] == 3

    def test_source_filter_requests_extra_results(self, retriever, mock_vector_store):
        """When source_filter is set, retriever requests 2× results to allow filtering."""
        retriever.retrieve("query", source_filter="38300")
        call_kwargs = mock_vector_store.query.call_args[1]
        assert call_kwargs["n_results"] == retriever.top_k * 2

    def test_query_expansion_applied_before_embedding(
        self, retriever, mock_embedding_generator, monkeypatch
    ):
        """With expansion enabled, the embedded text carries the 3GPP gloss
        while the user's original wording is preserved as its prefix."""
        from src.core import retriever as retriever_module
        monkeypatch.setattr(retriever_module.settings, "query_expansion", True)
        retriever.retrieve("What is SDAP?")
        embedded = mock_embedding_generator.generate_embedding.call_args[0][0]
        assert embedded.startswith("What is SDAP?")
        assert "Service Data Adaptation Protocol" in embedded

    def test_query_expansion_disabled_passes_raw_query(
        self, retriever, mock_embedding_generator, monkeypatch
    ):
        from src.core import retriever as retriever_module
        monkeypatch.setattr(retriever_module.settings, "query_expansion", False)
        monkeypatch.setattr(retriever_module.settings, "query_decomposition", False)
        retriever.retrieve("What is SDAP?")
        mock_embedding_generator.generate_embedding.assert_called_once_with("What is SDAP?")

    def test_comparison_query_searches_per_side(
        self, retriever, mock_embedding_generator, monkeypatch
    ):
        """A comparison query embeds the raw query plus one sub-query per
        side (expansion disabled here to isolate decomposition)."""
        from src.core import retriever as retriever_module
        monkeypatch.setattr(retriever_module.settings, "query_expansion", False)
        monkeypatch.setattr(retriever_module.settings, "query_decomposition", True)
        retriever.retrieve("What are the differences between NR and LTE physical layer?")
        embedded = [c[0][0] for c in mock_embedding_generator.generate_embedding.call_args_list]
        assert len(embedded) == 3
        assert "NR physical layer" in embedded
        assert "LTE physical layer" in embedded

    def test_decomposition_disabled_skips_subqueries(
        self, retriever, mock_embedding_generator, monkeypatch
    ):
        from src.core import retriever as retriever_module
        monkeypatch.setattr(retriever_module.settings, "query_expansion", False)
        monkeypatch.setattr(retriever_module.settings, "query_decomposition", False)
        retriever.retrieve("What are the differences between NR and LTE physical layer?")
        assert mock_embedding_generator.generate_embedding.call_count == 1

    def test_source_filter_applied(self, mock_vector_store, mock_embedding_generator):
        """Only docs whose source contains the filter string are returned."""
        from src.core.retriever import DocumentRetriever

        mock_vector_store.query.return_value = {
            "documents": [["doc A", "doc B"]],
            "metadatas": [
                [
                    {"source": "38300-spec.docx", "chunk_index": 0},
                    {"source": "38401-spec.docx", "chunk_index": 1},
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        ret = DocumentRetriever(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator,
            top_k=5,
        )
        results = ret.retrieve("query", source_filter="38300")
        assert len(results) == 1
        assert "38300" in results[0]["source"]

    def test_empty_vector_store_returns_empty_list(
        self, mock_vector_store, mock_embedding_generator
    ):
        from src.core.retriever import DocumentRetriever
        mock_vector_store.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        ret = DocumentRetriever(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator,
        )
        results = ret.retrieve("no results query")
        assert results == []


# ---------------------------------------------------------------------------
# format_context
# ---------------------------------------------------------------------------

class TestFormatContext:
    def test_returns_string(self, retriever, retrieved_docs):
        ctx = retriever.format_context(retrieved_docs)
        assert isinstance(ctx, str)

    def test_contains_document_numbers(self, retriever, retrieved_docs):
        ctx = retriever.format_context(retrieved_docs)
        assert "[Document 1]" in ctx
        assert "[Document 2]" in ctx

    def test_contains_source_names(self, retriever, retrieved_docs):
        ctx = retriever.format_context(retrieved_docs)
        for doc in retrieved_docs:
            assert doc["source"] in ctx

    def test_contains_text(self, retriever, retrieved_docs):
        ctx = retriever.format_context(retrieved_docs)
        for doc in retrieved_docs:
            assert doc["text"][:20] in ctx

    def test_empty_list_returns_empty_string(self, retriever):
        ctx = retriever.format_context([])
        assert ctx == ""


# ---------------------------------------------------------------------------
# Hybrid (dense + BM25) and rerank wiring (ADR-012)
# ---------------------------------------------------------------------------

@pytest.fixture
def hybrid_retriever(mock_vector_store, mock_embedding_generator):
    """Retriever over a mocked store whose collection backs a real BM25 index."""
    from unittest.mock import MagicMock
    from src.core import bm25
    from src.core.retriever import DocumentRetriever

    bm25.clear_cache()
    mock_vector_store.query.return_value = {
        "ids": [["id_0", "id_1"]],
        "documents": [["chunk about gNB", "chunk about F1"]],
        "metadatas": [[
            {"source": "38300-g30.docx", "chunk_index": 0},
            {"source": "38401-g30.docx", "chunk_index": 1},
        ]],
        "distances": [[0.08, 0.13]],
    }
    coll = MagicMock()
    coll.name = "3gpp_specs"
    coll.count.return_value = 3
    coll.metadata = {}
    coll.get.side_effect = lambda **kw: (
        {"ids": ["id_2"], "embeddings": [[0.0] * 384]}
        if "ids" in kw else
        {
            "ids": ["id_0", "id_1", "id_2"],
            "documents": ["chunk about gNB", "chunk about F1",
                          "T310 timer is started on radio link problems"],
            "metadatas": [
                {"source": "38300-g30.docx", "chunk_index": 0},
                {"source": "38401-g30.docx", "chunk_index": 1},
                {"source": "38331-g30.docx", "chunk_index": 7},
            ],
        }
    )
    mock_vector_store.collection = coll
    return DocumentRetriever(
        vector_store=mock_vector_store,
        embedding_generator=mock_embedding_generator,
        top_k=5, hybrid=True, rerank=False, expand=False, decompose=False,
    )


class TestHybridRetrieve:
    def test_keyword_only_hit_is_fused_in(self, hybrid_retriever):
        docs = hybrid_retriever.retrieve("When is T310 started?")
        assert "38331-g30.docx" in [d["source"] for d in docs]

    def test_keyword_only_hit_gets_embedding_similarity(self, hybrid_retriever,
                                                        mock_embedding):
        docs = hybrid_retriever.retrieve("When is T310 started?")
        t310 = next(d for d in docs if d["source"] == "38331-g30.docx")
        # squared-L2 similarity against a zero vector: 1 - |q|^2
        expected = 1 - sum(x * x for x in mock_embedding)
        assert t310["similarity"] == pytest.approx(expected)

    def test_dense_hits_keep_store_similarity(self, hybrid_retriever):
        docs = hybrid_retriever.retrieve("When is T310 started?")
        gnb = next(d for d in docs if d["source"] == "38300-g30.docx")
        assert gnb["similarity"] == pytest.approx(0.92)

    def test_no_duplicate_chunks(self, hybrid_retriever):
        docs = hybrid_retriever.retrieve("gNB F1 T310")
        keys = [(d["source"], d["chunk_index"]) for d in docs]
        assert len(keys) == len(set(keys))

    def test_hybrid_off_never_touches_bm25(self, retriever, mock_vector_store):
        from unittest.mock import patch
        with patch("src.core.bm25.get_index_for_collection") as get_idx:
            retriever.retrieve("anything")
        get_idx.assert_not_called()


class TestRerankWiring:
    def test_rerank_flag_routes_through_reranker(self, mock_vector_store,
                                                 mock_embedding_generator):
        from src.core.retriever import DocumentRetriever
        r = DocumentRetriever(vector_store=mock_vector_store,
                              embedding_generator=mock_embedding_generator,
                              top_k=2, rerank=True, expand=False, decompose=False)
        r._reranker = lambda q, docs: list(reversed(docs))
        docs = r.retrieve("query")
        assert docs[0]["source"] == "38401-g30.docx"

    def test_overrides_beat_settings(self, mock_vector_store, mock_embedding_generator,
                                     monkeypatch):
        from src.core import retriever as retriever_module
        monkeypatch.setattr(retriever_module.settings, "hybrid_search", True)
        r = retriever_module.DocumentRetriever(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator, hybrid=False)
        assert r.hybrid is False
        r2 = retriever_module.DocumentRetriever(
            vector_store=mock_vector_store,
            embedding_generator=mock_embedding_generator)
        assert r2.hybrid is True
