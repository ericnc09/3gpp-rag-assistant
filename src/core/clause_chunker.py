"""
Clause-aware chunking for 3GPP specifications (Sprint 2, ADR-014).

The original chunker (``document_processor_impl.chunk_text``) flattens a spec
to one whitespace-collapsed string, appends every table at the end of the
document, and cuts 1000-character windows. A chunk therefore has no idea
which clause it came from, can straddle two clauses, and a table row is
detached from the clause that introduces it.

This module walks the DOCX body in document order (paragraphs and tables
interleaved), uses the specs' own heading paragraphs ("Heading 1..9", text
"5.3.5.4<TAB>Reception of ...") as section boundaries, and packs each
clause's paragraphs into chunks that never cross a clause boundary.

Each chunk carries:
  * ``clause`` / ``clause_title`` / ``clause_path`` (breadcrumb of parent
    titles), so answers can cite "TS 38.401 §8.4.1.1" instead of a file;
  * ``section_id`` + ``part`` / ``n_parts``, so a retrieved part can be
    expanded to its whole clause ("small-to-big", see ``retriever``);
  * optionally a one-line *contextual header* prepended to the text that is
    embedded and BM25-indexed ("contextual retrieval"): spec number, spec
    title and clause breadcrumb. It is built from document structure, not
    an LLM summary, so it costs nothing at index time. ``header_len`` lets
    callers strip it again.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

# "5.3.5.4\tTitle", "5.2.2a\tVoid", "A.2.1 Title" (annex sub-clauses), "4 General"
_CLAUSE_RE = re.compile(r"^((?:\d+[a-z]?|[A-Z])(?:\.\d+[a-z]?)+|\d+[a-z]?)\s+(\S.*)$")
# "Annex A (normative):\tTitle"
_ANNEX_RE = re.compile(r"^Annex\s+([A-Z]{1,2})\b[^:]*:?\s*(.*)$", re.IGNORECASE)
_HEADING_STYLE_RE = re.compile(r"^(?:Heading\s*(\d)|H(\d))$", re.IGNORECASE)
_SKIP_STYLE_RE = re.compile(r"^(?:toc\s*\d|TT|ZA|ZB|ZT|ZU|ZV)\b", re.IGNORECASE)
_SENTENCE_END_RE = re.compile(r"(?<=[.;:])\s+")

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_MIN_CHUNK = 80
OVERLAP_MAX_BLOCK = 250  # carry the previous chunk's last block if it is this short


@dataclass
class Section:
    clause: str
    title: str
    path: List[str] = field(default_factory=list)  # parent titles, outermost first
    blocks: List[str] = field(default_factory=list)


def parse_heading(text: str) -> Optional[Tuple[str, str]]:
    """``"5.3.5.4\\tReception"`` -> ``("5.3.5.4", "Reception")``; None if not a clause."""
    text = text.strip()
    m = _ANNEX_RE.match(text)
    if m:
        return m.group(1).upper(), m.group(2).strip()
    m = _CLAUSE_RE.match(text)
    if m:
        return m.group(1), m.group(2).strip()
    return None


def clause_depth(clause: str) -> int:
    return clause.count(".") + 1


def is_numbered(clause: str) -> bool:
    return bool(re.match(r"^(?:\d+[a-z]?|[A-Z]{1,2})(?:\.\d+[a-z]?)*$", clause or ""))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _table_rows(table) -> Iterator[str]:
    for row in table.rows:
        try:
            cells: List[str] = []
            for cell in row.cells:
                value = _norm(cell.text)
                # Merged cells are repeated by python-docx; keep one copy.
                if value and (not cells or cells[-1] != value):
                    cells.append(value)
        except Exception:  # noqa: BLE001 - irregular spans in some tables
            continue
        if cells:
            yield " | ".join(cells)


def iter_docx_blocks(path: Path) -> Iterator[Tuple[str, str]]:
    """Yield ``(kind, text)`` in document order; kind is ``heading`` or ``text``.

    Tables become one ``text`` block per row, in place.
    """
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(path))
    for el in doc.element.body.iterchildren():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "p":
            para = Paragraph(el, doc)
            text = para.text.strip()
            if not text:
                continue
            style = para.style.name if para.style is not None else ""
            if _SKIP_STYLE_RE.match(style):
                continue
            if _HEADING_STYLE_RE.match(style):
                # Numbered clause, or an unnumbered heading such as
                # "Foreword" / "Introduction" (kept as its own section).
                yield "heading", _norm(text)
            else:
                yield "text", _norm(text)
        elif tag == "tbl":
            for row in _table_rows(Table(el, doc)):
                yield "text", row


def build_sections(blocks: Iterator[Tuple[str, str]]) -> List[Section]:
    """Group blocks under their clause heading, tracking the parent breadcrumb."""
    sections: List[Section] = []
    stack: List[Tuple[int, str]] = []  # (depth, title) of open ancestors
    current: Optional[Section] = None
    for kind, text in blocks:
        if kind == "heading":
            parsed = parse_heading(text)
            clause, title = parsed if parsed else (text[:60], text)
            depth = clause_depth(clause) if parsed else 1
            stack = [s for s in stack if s[0] < depth]
            current = Section(clause=clause, title=title, path=[t for _, t in stack])
            stack.append((depth, title))
            sections.append(current)
        else:
            if current is None:  # cover page / front matter before clause 1
                current = Section(clause="Front matter", title="Front matter")
                sections.append(current)
            current.blocks.append(text)
    return [s for s in sections if s.blocks]


def _split_long(block: str, size: int) -> List[str]:
    """Split one oversized paragraph at sentence ends, hard-cutting as a last resort."""
    pieces: List[str] = []
    buf = ""
    for sent in _SENTENCE_END_RE.split(block):
        if buf and len(buf) + 1 + len(sent) > size:
            pieces.append(buf)
            buf = sent
        else:
            buf = f"{buf} {sent}".strip()
    if buf:
        pieces.append(buf)
    out: List[str] = []
    for p in pieces:
        if len(p) > size * 1.5:  # no sentence boundary (e.g. a huge ASN.1 line)
            out.extend(p[i : i + size] for i in range(0, len(p), size))
        else:
            out.append(p)
    return out


def pack_blocks(blocks: List[str], size: int = DEFAULT_CHUNK_SIZE) -> List[str]:
    """Greedily pack a clause's blocks into ~``size``-char chunks.

    Chunks never leave the clause. When a chunk is closed, its last block is
    repeated at the start of the next one if it is short (a lead-in sentence
    or a table header row), which keeps "the following applies:" next to
    what follows it.
    """
    flat: List[str] = []
    for b in blocks:
        flat.extend(_split_long(b, size) if len(b) > size else [b])

    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for b in flat:
        if cur and cur_len + len(b) + 1 > size:
            chunks.append("\n".join(cur))
            carry = cur[-1] if len(cur[-1]) <= OVERLAP_MAX_BLOCK and len(cur) > 1 else None
            cur = [carry] if carry else []
            cur_len = len(carry) + 1 if carry else 0
        cur.append(b)
        cur_len += len(b) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def context_header(spec_number: str, spec_title: str, section: Section) -> str:
    crumbs = " > ".join(section.path + [section.title])
    spec = f"TS {spec_number}" if spec_number and spec_number != "unknown" else "3GPP spec"
    title = f" ({spec_title})" if spec_title and spec_title != "unknown" else ""
    where = f" §{section.clause}: " if is_numbered(section.clause) else ": "
    return f"{spec}{title}{where}{crumbs}"


def chunk_sections(
    sections: List[Section],
    base_metadata: Dict,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    min_chunk: int = DEFAULT_MIN_CHUNK,
    contextual: bool = True,
) -> List[Dict]:
    """Turn sections into chunk dicts (``text`` + ``metadata``) ready to embed."""
    spec_number = base_metadata.get("spec_number", "unknown")
    spec_title = base_metadata.get("spec_title", "unknown")
    source = base_metadata.get("source", "unknown")
    chunks: List[Dict] = []
    for section in sections:
        parts = [p for p in pack_blocks(section.blocks, chunk_size) if len(p) >= min_chunk]
        header = context_header(spec_number, spec_title, section)
        for i, body in enumerate(parts):
            text = f"{header}\n{body}" if contextual else body
            meta = dict(base_metadata)
            meta.update(
                {
                    "chunk_index": len(chunks),
                    "chunk_size": len(text),
                    "chunking": "clause",
                    "clause": section.clause,
                    "clause_title": section.title[:200],
                    "clause_path": " > ".join(section.path + [section.title])[:400],
                    "section_id": f"{source}#{section.clause}",
                    "part": i,
                    "n_parts": len(parts),
                    "header_len": len(header) + 1 if contextual else 0,
                }
            )
            chunks.append({"text": text, "metadata": meta, "chunk_id": len(chunks)})
    return chunks


def chunk_docx(
    path: Path,
    base_metadata: Dict,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    contextual: bool = True,
) -> List[Dict]:
    path = Path(path)
    meta = {"source": path.name, "format": "docx", **base_metadata}
    sections = build_sections(iter_docx_blocks(path))
    return chunk_sections(sections, meta, chunk_size=chunk_size, contextual=contextual)


def strip_header(text: str, metadata: Dict) -> str:
    """Body text of a chunk without its contextual header."""
    n = int(metadata.get("header_len") or 0)
    return text[n:] if n else text


def format_clause_ref(metadata: Dict) -> Optional[str]:
    """``"TS 38.401 §8.4.1.1"`` for clause chunks, else None."""
    clause = metadata.get("clause")
    if not clause or not is_numbered(clause):
        return None
    spec = metadata.get("spec_number")
    prefix = f"TS {spec} " if spec and spec != "unknown" else ""
    return f"{prefix}§{clause}"
