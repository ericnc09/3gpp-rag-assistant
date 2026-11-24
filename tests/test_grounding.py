"""
Tests for src/core/grounding.py — claim splitting, citation parsing and
claim-level support scoring (ADR-013). A bag-of-words fake embedder stands
in for bge-small so the tests are deterministic and model-free.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.grounding import (
    GroundingChecker,
    lexical_overlap,
    parse_citations,
    split_claims,
    strip_citations,
)


def bow_embed(text):
    """Deterministic fake embedding: hashed bag of lowercase words."""
    vec = [0.0] * 64
    for word in re.findall(r"[a-z0-9-]+", text.lower()):
        vec[hash(word) % 64] += 1.0
    return vec


DOCS = [
    {"text": "The gNB-CU hosts the RRC, SDAP and PDCP protocols. "
             "The gNB-DU hosts the RLC, MAC and PHY layers."},
    {"text": "The AMF performs registration management and connection management "
             "for the UE in the 5G core network."},
]


class TestParseCitations:
    @pytest.mark.parametrize("text,expected", [
        ("hosts RRC [D1].", [1]),
        ("see [D1, D2]", [1, 2]),
        ("see [D2; D3]", [2, 3]),
        ("[Document 2] says", [2]),
        ("(Document 3)", [3]),
        ("as in Document 4", [4]),
        ("bare [5] marker", [5]),
        ("no citation here", []),
        ("[D1] then [D1] again", [1]),
    ])
    def test_forms(self, text, expected):
        assert parse_citations(text) == expected

    def test_strip_citations_cleans_spacing(self):
        assert strip_citations("The CU hosts RRC [D1].") == "The CU hosts RRC."


class TestSplitClaims:
    def test_sentences_and_bullets(self):
        answer = ("The gNB-CU hosts RRC and PDCP [D1]. The gNB-DU hosts RLC and MAC [D1].\n"
                  "- The AMF handles registration management for the UE [D2].")
        claims = split_claims(answer)
        assert len(claims) == 3
        assert claims[2]["citations"] == [2]

    def test_short_fragments_and_headings_dropped(self):
        claims = split_claims("Overview:\nYes.\nThe AMF handles registration for each UE [D2].")
        assert [c["text"] for c in claims] == ["The AMF handles registration for each UE."]

    def test_decimal_spec_numbers_do_not_split(self):
        claims = split_claims("TS 38.300 defines the overall NR description in detail [D1].")
        assert len(claims) == 1

    def test_hedges_marked_meta(self):
        claims = split_claims("The context does not provide enough information on timers.")
        assert claims[0]["meta"] is True


class TestLexicalOverlap:
    def test_identifier_overlap(self):
        assert lexical_overlap("gNB-CU hosts PDCP", DOCS[0]["text"]) == 1.0

    def test_no_overlap(self):
        assert lexical_overlap("satellite ephemeris", DOCS[0]["text"]) == 0.0


class TestGroundingChecker:
    def checker(self):
        return GroundingChecker(bow_embed)

    def test_supported_cited_claim(self):
        out = self.checker().check("The gNB-CU hosts the RRC, SDAP and PDCP protocols [D1].", DOCS)
        claim = out["claims"][0]
        assert claim["cited"] and claim["supported"] and claim["grounded"]
        assert out["citation_coverage"] == 1.0 and out["citation_precision"] == 1.0

    def test_miscited_claim_unsupported_but_grounded(self):
        # True statement, but it cites the AMF chunk instead of the CU chunk.
        out = self.checker().check("The gNB-CU hosts the RRC, SDAP and PDCP protocols [D2].", DOCS)
        claim = out["claims"][0]
        assert claim["cited"] and not claim["supported"]
        assert claim["grounded"] and claim["grounded_doc"] == 1
        assert out["citation_precision"] == 0.0 and out["grounded_ratio"] == 1.0

    def test_uncited_claim_scored_against_all_docs(self):
        out = self.checker().check("The AMF performs registration management for the UE.", DOCS)
        claim = out["claims"][0]
        assert not claim["cited"] and claim["supported"] and claim["best_doc"] == 2
        assert out["citation_coverage"] == 0.0 and out["citation_precision"] is None

    def test_fabricated_claim_ungrounded(self):
        out = self.checker().check("Satellite ephemeris is broadcast every forty milliseconds.", DOCS)
        assert out["grounded_ratio"] == 0.0
        assert out["ungrounded_claims"] == ["Satellite ephemeris is broadcast every forty milliseconds."]

    def test_out_of_range_citation_counted_invalid(self):
        out = self.checker().check("The AMF performs registration management [17].", DOCS)
        assert out["invalid_citations"] == 1
        assert out["claims"][0]["cited"] is False

    def test_meta_claims_excluded_from_metrics(self):
        out = self.checker().check(
            "The AMF performs registration management for the UE [D2]. "
            "The context does not provide enough information about timers.", DOCS)
        assert out["n_claims"] == 1 and out["n_meta"] == 1
        assert out["grounded_ratio"] == 1.0

    def test_empty_inputs(self):
        assert self.checker().check("", DOCS)["n_claims"] == 0
        out = self.checker().check("The AMF performs registration management.", [])
        assert out["n_claims"] == 1 and out["grounded_ratio"] == 0.0

    def test_batch_embedder_used_when_given(self):
        calls = []

        def batch(texts):
            calls.append(len(texts))
            return [bow_embed(t) for t in texts]

        GroundingChecker(bow_embed, batch).check("The AMF performs registration management [D2].", DOCS)
        assert len(calls) == 1  # windows + claims embedded in one batch


@pytest.mark.parametrize("sentence", [
    "It is not specified in the provided context whether the F1 interface is bidirectional.",
    "The specific functions of the NG-RAN logical nodes are not explicitly stated in the provided context.",
    "The timer value is not mentioned in the documents.",
])
def test_context_hedges_are_meta(sentence):
    assert split_claims(sentence)[0]["meta"] is True


def test_negative_fact_is_not_meta():
    # A factual negative about the system, not about the context.
    claim = split_claims("The gNB-DU does not host the RRC protocol layer [D1].")[0]
    assert claim["meta"] is False
