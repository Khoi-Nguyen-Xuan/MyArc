"""Turns an uploaded PDF or Word file into clean text.

Used by the syllabus agent, whose LLM reads the whole text, and later by RAG,
which chunks the same parts so every chunk keeps its page number.

- PDF: pypdf's layout mode, which keeps each table row on one line
  ("Quizzes    Quiz    2%*9"). Headers and footers repeated on every page
  (browser print dates, URLs, "3/16") are removed.
- Word (.docx): paragraphs and tables in reading order. Each table row becomes
  one line, with cells separated by " | ".
"""

from __future__ import annotations

import io
import re
import textwrap
import zipfile
from collections import Counter
from dataclasses import dataclass

import docx
import pypdf
from docx.table import Table
from pypdf.errors import PyPdfError

MAX_PAGES = 50  # syllabi are rarely over 20 pages; this stops huge uploads from running up LLM costs
HEADER_FOOTER_SHARE = 0.6  # a line found on at least 60% of pages is a header or footer

_DIGITS = re.compile(r"\d+")
_BLANK_LINES = re.compile(r"\n{3,}")


class DocumentError(Exception):
    """The file can't be turned into text. The message is written to be shown to the student."""


@dataclass(frozen=True, slots=True)
class DocumentPart:
    text: str
    page: int | None  # PDF page number, starting at 1; None for Word documents, which have no fixed pages


@dataclass(frozen=True, slots=True)
class Document:
    file_name: str
    parts: list[DocumentPart]

    def full_text(self) -> str:
        """All text in reading order. PDF pages start with an "=== Page N ===" line so the LLM can cite them."""
        return "\n\n".join(f"=== Page {part.page} ===\n{part.text}" if part.page else part.text for part in self.parts)


def load_document(data: bytes, file_name: str) -> Document:
    """Read a PDF or .docx file from its bytes. Raises DocumentError for other formats or when there is no text."""
    if b"%PDF-" in data[:1024]:
        parts = _read_pdf(data)
    elif _is_docx(data):
        parts = _read_docx(data)
    elif data.startswith(b"\xd0\xcf\x11\xe0"):  # the old binary .doc format
        raise DocumentError("This is an old-style .doc file. Save it as .docx or PDF and upload it again.")
    else:
        raise DocumentError("This file isn't a PDF or a Word (.docx) document.")

    parts = [part for part in parts if part.text]
    if not parts:
        raise DocumentError("This file has no readable text. It may be a scanned image, which we can't read yet.")
    return Document(file_name=file_name, parts=parts)


def _read_pdf(data: bytes) -> list[DocumentPart]:
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):  # many PDFs are "encrypted" with an empty password
            raise DocumentError("This PDF is password-protected. Upload a copy without a password.")
        if len(reader.pages) > MAX_PAGES:
            raise DocumentError(f"This PDF has {len(reader.pages)} pages. A syllabus should be under {MAX_PAGES}.")
        pages = [_page_text(page) for page in reader.pages]
    except PyPdfError as exc:
        raise DocumentError("This PDF is damaged and can't be read.") from exc

    pages = _drop_headers_and_footers(pages)
    return [DocumentPart(text=_tidy(text), page=number) for number, text in enumerate(pages, start=1)]


def _page_text(page: pypdf.PageObject) -> str:
    # pypdf's layout mode raises KeyError on pages with no content stream, such as blank pages.
    if "/Contents" not in page:
        return ""
    return page.extract_text(extraction_mode="layout")


def _drop_headers_and_footers(pages: list[str]) -> list[str]:
    """Remove lines that appear on most pages, ignoring spacing and numbers ("1/16" and "6/16" match)."""
    if len(pages) < 3:
        return pages  # too few pages to tell a header from real content

    pages_containing = Counter(
        line_key for page in pages for line_key in {_line_key(line) for line in page.splitlines()}
    )
    repeated = {
        line_key
        for line_key, count in pages_containing.items()
        if line_key and count >= HEADER_FOOTER_SHARE * len(pages)
    }
    return ["\n".join(line for line in page.splitlines() if _line_key(line) not in repeated) for page in pages]


def _line_key(line: str) -> str:
    """Compare lines ignoring spacing and numbers: "... 1/16" and "...   6/16" give the same key."""
    return _DIGITS.sub("#", " ".join(line.split()))


def _is_docx(data: bytes) -> bool:
    if not zipfile.is_zipfile(io.BytesIO(data)):
        return False
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return "word/document.xml" in archive.namelist()


def _read_docx(data: bytes) -> list[DocumentPart]:
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception as exc:  # python-docx raises many unrelated types for broken files
        raise DocumentError("This Word document is damaged and can't be read.") from exc

    blocks = [_table_text(block) if isinstance(block, Table) else block.text for block in document.iter_inner_content()]
    return [DocumentPart(text=_tidy("\n".join(blocks)), page=None)]


def _table_text(table: Table) -> str:
    """One line per row, cells joined by " | ".

    python-docx returns a merged cell once per grid column it spans. Those
    repeats share the same underlying cell element (`_tc`), so they're skipped
    by identity. Comparing text instead would wrongly merge two neighbouring
    cells that both say "30%".
    """
    lines = []
    for row in table.rows:
        seen_cells = set()
        texts = []
        for cell in row.cells:
            if id(cell._tc) in seen_cells:
                continue
            seen_cells.add(id(cell._tc))
            texts.append(" / ".join(line.strip() for line in cell.text.splitlines() if line.strip()))
        if any(texts):
            lines.append(" | ".join(texts))
    return "\n".join(lines)


def _tidy(text: str) -> str:
    """Strip trailing spaces, the page's shared left margin, and runs of blank lines."""
    text = textwrap.dedent("\n".join(line.rstrip() for line in text.splitlines()))
    return _BLANK_LINES.sub("\n\n", text).strip()
