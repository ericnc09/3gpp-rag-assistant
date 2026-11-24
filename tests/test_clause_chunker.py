"""Tests for src/core/clause_chunker.py (ADR-014)."""
import pytest

from src.core.clause_chunker import (
    Section,
    build_sections,
    chunk_docx,
    chunk_sections,
    context_header,
    format_clause_ref,
    is_numbered,
    iter_docx_blocks,
    pack_blocks,
    parse_heading,
    strip_header,
)


class TestParseHeading:
    @pytest.mark.parametrize("text,expected", [
        ("5.3.5.4\tReception of RRCReconfiguration", ("5.3.5.4", "Reception of RRCReconfiguration")),
        ("4\tGeneral", ("4", "General")),
        ("5.2.2a\tVoid", ("5.2.2a", "Void")),
        ("A.1\tDeployment", ("A.1", "Deployment")),
        ("Annex B (informative):\tChange history", ("B", "Change history")),
    ])
    def test_clause_headings(self, text, expected):
        assert parse_heading(text) == expected

    @pytest.mark.parametrize("text", ["Foreword", "5G is a system", "", "Introduction"])
    def test_non_clauses(self, text):
        assert parse_heading(text) is None

    def test_is_numbered(self):
        assert is_numbered("8.4.1.1") and is_numbered("A.2") and is_numbered("5.2.2a")
        assert not is_numbered("Foreword") and not is_numbered("Front matter")


class TestBuildSections:
    def test_breadcrumb_tracks_parents_and_pops_siblings(self):
        blocks = [
            ("heading", "8\tProcedures"),
            ("heading", "8.4\tMulti-Connectivity"),
            ("heading", "8.4.1\tSecondary Node Addition"),
            ("text", "addition body"),
            ("heading", "8.4.2\tSecondary Node Release"),
            ("text", "release body"),
            ("heading", "9\tNext"),
            ("text", "nine body"),
        ]
        sections = build_sections(iter(blocks))
        # Headings without body text are dropped; their titles live in paths.
        assert [s.clause for s in sections] == ["8.4.1", "8.4.2", "9"]
        assert sections[0].path == ["Procedures", "Multi-Connectivity"]
        assert sections[1].path == ["Procedures", "Multi-Connectivity"]
        assert sections[2].path == []

    def test_text_before_first_heading_is_front_matter(self):
        sections = build_sections(iter([("text", "cover"), ("heading", "1\tScope"), ("text", "s")]))
        assert sections[0].clause == "Front matter"
        assert sections[1].clause == "1"

    def test_unnumbered_heading_is_its_own_section(self):
        sections = build_sections(iter([("heading", "Foreword"), ("text", "fw"),
                                        ("heading", "1\tScope"), ("text", "s")]))
        assert sections[0].clause == "Foreword" and sections[0].blocks == ["fw"]
        assert sections[1].path == []


class TestPackBlocks:
    def test_small_clause_is_one_chunk(self):
        assert pack_blocks(["a" * 100, "b" * 100], size=1000) == ["a" * 100 + "\n" + "b" * 100]

    def test_splits_at_block_boundaries_and_carries_short_lead_in(self):
        lead = "The following applies:"
        blocks = ["x" * 600, lead, "y" * 600]
        chunks = pack_blocks(blocks, size=1000)
        assert len(chunks) == 2
        assert chunks[0].endswith(lead)
        assert chunks[1].startswith(lead)  # short block repeated as overlap

    def test_oversized_block_is_split(self):
        block = " ".join(["This is a sentence."] * 200)
        chunks = pack_blocks([block], size=500)
        assert len(chunks) > 1
        assert all(len(c) <= 600 for c in chunks)


class TestChunkSections:
    def _sections(self):
        return [Section(clause="8.4.1.1", title="EN-DC",
                        path=["Multi-Connectivity", "Secondary Node Addition"],
                        blocks=["x" * 700, "y" * 700])]

    def test_metadata_and_header(self):
        meta = {"source": "38401.docx", "spec_number": "38.401", "spec_title": "NG-RAN; Architecture"}
        chunks = chunk_sections(self._sections(), meta, chunk_size=1000)
        assert len(chunks) == 2
        m = chunks[0]["metadata"]
        assert m["clause"] == "8.4.1.1"
        assert m["section_id"] == "38401.docx#8.4.1.1"
        assert (m["part"], m["n_parts"]) == (0, 2)
        assert m["clause_path"] == "Multi-Connectivity > Secondary Node Addition > EN-DC"
        assert chunks[0]["text"].startswith(
            "TS 38.401 (NG-RAN; Architecture) §8.4.1.1: Multi-Connectivity > "
        )
        assert strip_header(chunks[0]["text"], m) == "x" * 700

    def test_no_context_header(self):
        chunks = chunk_sections(self._sections(), {"source": "s"}, contextual=False)
        assert chunks[0]["text"] == "x" * 700
        assert chunks[0]["metadata"]["header_len"] == 0
        assert strip_header(chunks[0]["text"], chunks[0]["metadata"]) == "x" * 700

    def test_context_header_unnumbered(self):
        header = context_header("38.401", "T", Section(clause="Foreword", title="Foreword"))
        assert header == "TS 38.401 (T): Foreword"


class TestFormatClauseRef:
    def test_numbered(self):
        assert format_clause_ref({"clause": "5.3.5", "spec_number": "38.331"}) == "TS 38.331 §5.3.5"

    def test_fixed_size_chunk_has_none(self):
        assert format_clause_ref({"spec_number": "38.331"}) is None
        assert format_clause_ref({"clause": "Foreword"}) is None


class TestDocx:
    @pytest.fixture
    def docx_path(self, tmp_path):
        docx = pytest.importorskip("docx")
        doc = docx.Document()
        doc.add_paragraph("Cover page text that precedes clause one. " * 3)
        doc.add_heading("1\tScope", level=1)
        doc.add_paragraph("The present document specifies the overall architecture. " * 2)
        doc.add_heading("5\tArchitecture", level=1)
        doc.add_heading("5.1\tInterfaces", level=2)
        doc.add_paragraph("The interfaces are listed in the following table:")
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text, table.cell(0, 1).text = "Interface", "Nodes"
        table.cell(1, 0).text, table.cell(1, 1).text = "F1", "gNB-CU and gNB-DU"
        doc.add_paragraph("Text after the table stays in clause 5.1.")
        path = tmp_path / "38401-test.docx"
        doc.save(path)
        return path

    def test_tables_stay_in_place(self, docx_path):
        blocks = list(iter_docx_blocks(docx_path))
        texts = [t for _, t in blocks]
        lead = texts.index("The interfaces are listed in the following table:")
        assert texts[lead + 1] == "Interface | Nodes"
        assert texts[lead + 2] == "F1 | gNB-CU and gNB-DU"
        assert texts[lead + 3] == "Text after the table stays in clause 5.1."

    def test_chunk_docx(self, docx_path):
        chunks = chunk_docx(docx_path, {"spec_number": "38.401", "spec_title": "Arch"})
        by_clause = {c["metadata"]["clause"]: c for c in chunks}
        # Clause 5 has no body of its own; its title lives in 5.1's breadcrumb.
        assert set(by_clause) == {"Front matter", "1", "5.1"}
        f1 = by_clause["5.1"]
        assert "F1 | gNB-CU and gNB-DU" in f1["text"]
        assert f1["metadata"]["clause_path"] == "Architecture > Interfaces"
        assert f1["metadata"]["source"] == "38401-test.docx"

    def test_short_sections_dropped(self, docx_path):
        chunks = chunk_docx(docx_path, {}, chunk_size=1000)
        assert all(len(strip_header(c["text"], c["metadata"])) >= 80 for c in chunks)
