"""
Tests for src/core/bm25.py — the pure-Python BM25 keyword index used for
hybrid retrieval (ADR-012). No vector store, no models.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import bm25
from src.core.bm25 import BM25Index, matches_where, tokenize


class TestTokenize:
    def test_lowercases_and_drops_stopwords(self):
        assert tokenize("The gNB is a node") == ["gnb", "node"]

    def test_hyphenated_identifier_kept_whole_and_split(self):
        toks = tokenize("gNB-CU")
        assert toks[0] == "gnb-cu"
        assert "gnb" in toks and "cu" in toks

    def test_clause_number_kept_whole_only(self):
        toks = tokenize("see clause 5.3.5.4")
        assert "5.3.5.4" in toks
        assert "5" not in toks and "3" not in toks

    def test_camelcase_message_name_is_one_token(self):
        assert tokenize("RRCReconfiguration message") == ["rrcreconfiguration", "message"]

    def test_timer_names(self):
        assert tokenize("timer T310 expiry") == ["timer", "t310", "expiry"]


class TestMatchesWhere:
    def test_none_matches_everything(self):
        assert matches_where({"domain": "RAN"}, None)

    def test_equality(self):
        assert matches_where({"domain": "RAN"}, {"domain": "RAN"})
        assert not matches_where({"domain": "CORE"}, {"domain": "RAN"})

    def test_and(self):
        where = {"$and": [{"domain": "RAN"}, {"generation": "5G"}]}
        assert matches_where({"domain": "RAN", "generation": "5G"}, where)
        assert not matches_where({"domain": "RAN", "generation": "LTE"}, where)


def _index():
    texts = [
        "The RRCReconfiguration message is used to modify an RRC connection.",
        "Timer T310 is started upon detecting physical layer problems.",
        "The F1 interface connects the gNB-CU and the gNB-DU.",
        "The AMF handles registration management in the 5G core.",
        "General description of the NG-RAN architecture and the gNB.",
    ]
    metas = [
        {"source": "38331.docx", "domain": "RAN", "generation": "5G"},
        {"source": "38331.docx", "domain": "RAN", "generation": "5G"},
        {"source": "38401.docx", "domain": "RAN", "generation": "5G"},
        {"source": "23501.docx", "domain": "CORE", "generation": "5G"},
        {"source": "38300.docx", "domain": "RAN", "generation": "5G"},
    ]
    return BM25Index([f"id_{i}" for i in range(len(texts))], texts, metas)


class TestBM25Index:
    def test_exact_identifier_ranks_first(self):
        hits = _index().search("What does RRCReconfiguration do?", 3)
        assert hits[0]["id"] == "id_0"

    def test_timer_lookup(self):
        assert _index().search("when is T310 started", 1)[0]["id"] == "id_1"

    def test_compound_query_matches_parts(self):
        hits = _index().search("gNB-CU", 5)
        assert hits[0]["id"] == "id_2"
        # "gnb" part also matches the architecture chunk
        assert "id_4" in {h["id"] for h in hits}

    def test_no_match_returns_empty(self):
        assert _index().search("zzzz qqqq", 5) == []

    def test_n_limits_results(self):
        assert len(_index().search("gNB interface RRC AMF", 2)) == 2

    def test_where_filter(self):
        hits = _index().search("AMF registration gNB", 5, where={"domain": "CORE"})
        assert [h["id"] for h in hits] == ["id_3"]

    def test_source_filter(self):
        hits = _index().search("gNB", 5, source_filter="38401")
        assert [h["id"] for h in hits] == ["id_2"]

    def test_rare_term_outweighs_common_term(self):
        # "gnb" appears in two docs, "amf" in one: idf favours the AMF doc.
        hits = _index().search("gNB AMF", 5)
        assert hits[0]["id"] == "id_3"

    def test_repeated_query_terms_count_once(self):
        idx = _index()
        assert idx.score("T310") == idx.score("T310 T310 T310")

    def test_hit_shape(self):
        hit = _index().search("AMF", 1)[0]
        assert set(hit) == {"id", "text", "metadata", "bm25_score"}
        assert hit["bm25_score"] > 0

    def test_empty_index(self):
        idx = BM25Index([], [], [])
        assert len(idx) == 0
        assert idx.search("anything", 5) == []


class TestCollectionCache:
    def _collection(self, n=3):
        coll = MagicMock()
        coll.name = "c"
        coll.count.return_value = n
        coll.get.return_value = {
            "ids": [f"id_{i}" for i in range(n)],
            "documents": [f"doc {i} gnb" for i in range(n)],
            "metadatas": [{"source": f"s{i}"} for i in range(n)],
        }
        return coll

    def test_built_once_per_key(self):
        bm25.clear_cache()
        coll = self._collection()
        a = bm25.get_index_for_collection(coll)
        b = bm25.get_index_for_collection(coll)
        assert a is b
        assert coll.get.call_count == 1

    def test_count_change_rebuilds(self):
        bm25.clear_cache()
        coll = self._collection()
        a = bm25.get_index_for_collection(coll)
        coll.count.return_value = 4
        coll.get.return_value["ids"].append("id_3")
        coll.get.return_value["documents"].append("doc 3")
        coll.get.return_value["metadatas"].append({"source": "s3"})
        b = bm25.get_index_for_collection(coll)
        assert a is not b and len(b) == 4
