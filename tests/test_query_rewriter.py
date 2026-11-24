"""Tests for src/core/query_rewriter.py (ADR-014)."""
from unittest.mock import MagicMock

import pytest

from src.core.query_rewriter import (
    QueryRewriter,
    clean_rewrite,
    fallback_query,
    format_history,
    needs_rewrite,
)

HISTORY = [
    {"role": "user", "content": "What is the F1 interface?"},
    {"role": "assistant", "content": "F1 connects the gNB-CU and the gNB-DU."},
]


class TestNeedsRewrite:
    def test_no_history_never_rewrites(self):
        assert not needs_rewrite("Which protocol runs on its control plane?", [])
        assert not needs_rewrite("Which protocol runs on its control plane?", None)

    @pytest.mark.parametrize("q", [
        "Which protocol runs on its control plane?",
        "And the UPF?",
        "What about LTE?",
        "How does that procedure end?",
        "Explain more",
    ])
    def test_follow_ups(self, q):
        assert needs_rewrite(q, HISTORY)

    def test_self_contained_question_skips(self):
        assert not needs_rewrite("Which protocol runs on the F1-C control plane between gNB-CU and gNB-DU?", HISTORY)


class TestHelpers:
    def test_fallback_prepends_last_user_turn(self):
        assert fallback_query("And the UPF?", HISTORY) == "What is the F1 interface? And the UPF?"

    def test_fallback_without_user_turn(self):
        assert fallback_query("q here", [{"role": "assistant", "content": "x"}]) == "q here"

    def test_format_history_truncates_assistant(self):
        long = [{"role": "user", "content": "Q"}, {"role": "assistant", "content": "a " * 1000}]
        text = format_history(long)
        assert text.startswith("User: Q\nAssistant: ")
        assert len(text) < 700

    @pytest.mark.parametrize("raw,expected", [
        ('"Which protocol runs on F1-C?"', "Which protocol runs on F1-C?"),
        ("Standalone question: What is F1AP used for?\nextra", "What is F1AP used for?"),
        ("\n\n  How does the AMF select an SMF?  ", "How does the AMF select an SMF?"),
    ])
    def test_clean_rewrite(self, raw, expected):
        assert clean_rewrite(raw) == expected

    @pytest.mark.parametrize("raw", ["", "F1AP", "x " * 400])
    def test_clean_rewrite_rejects(self, raw):
        assert clean_rewrite(raw) is None


class TestQueryRewriter:
    def test_no_history_no_llm_call(self):
        llm = MagicMock()
        out = QueryRewriter(llm).rewrite("What is F1?", [])
        assert out == {"query": "What is F1?", "method": "none"}
        llm.generate.assert_not_called()

    def test_llm_rewrite(self):
        llm = MagicMock()
        llm.generate.return_value = "Which protocol runs on the F1-C control plane?"
        out = QueryRewriter(llm).rewrite("Which protocol runs on its control plane?", HISTORY)
        assert out == {"query": "Which protocol runs on the F1-C control plane?", "method": "llm"}
        prompt = llm.generate.call_args.args[0]
        assert "F1 connects the gNB-CU" in prompt
        assert "Which protocol runs on its control plane?" in prompt

    def test_llm_error_falls_back(self):
        llm = MagicMock()
        llm.generate.side_effect = RuntimeError("ollama down")
        out = QueryRewriter(llm).rewrite("And the UPF?", HISTORY)
        assert out == {"query": "What is the F1 interface? And the UPF?", "method": "fallback"}

    def test_unusable_llm_output_falls_back(self):
        llm = MagicMock()
        llm.generate.return_value = "F1"
        assert QueryRewriter(llm).rewrite("And the UPF?", HISTORY)["method"] == "fallback"

    def test_no_llm_uses_fallback(self):
        assert QueryRewriter(None).rewrite("And the UPF?", HISTORY)["method"] == "fallback"

    def test_always_skips_gate(self):
        llm = MagicMock()
        llm.generate.return_value = "Which protocol runs on the F1-C control plane?"
        q = "Which protocol runs on the F1-C control plane between gNB-CU and gNB-DU?"
        assert QueryRewriter(llm).rewrite(q, HISTORY)["method"] == "none"
        assert QueryRewriter(llm, always=True).rewrite(q, HISTORY)["method"] == "llm"
