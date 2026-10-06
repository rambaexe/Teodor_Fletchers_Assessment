import zipfile
from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.extractor.base import DocumentExtractor, ExtractionResult, ProgressFn
from app.db.models import Chunk

ZIP_MAGIC = b"PK\x03\x04"


class DocxExtractor(DocumentExtractor):
    """Word (.docx): headings, paragraphs and tables in document order. No pages in docx."""

    file_type = "docx"

    @classmethod
    def can_handle(cls, header: bytes, path: Path) -> bool:
        # docx = zip with word/document.xml (plain zips / xlsx / pptx don't have it)
        if not header.startswith(ZIP_MAGIC) or not zipfile.is_zipfile(path):
            return False
        with zipfile.ZipFile(path) as z:
            return "word/document.xml" in z.namelist()

    def extract(self, path: Path, on_progress: ProgressFn) -> ExtractionResult:
        document = docx.Document(str(path))
        blocks = list(document.iter_inner_content())  # paragraphs + tables, in order

        chunks: list[Chunk] = []
        for i, block in enumerate(blocks):
            chunk = _paragraph_chunk(block) if isinstance(block, Paragraph) else _table_chunk(block)
            if chunk:
                chunk.position = len(chunks)
                chunks.append(chunk)
            on_progress((i + 1) / len(blocks))

        return ExtractionResult(chunks=chunks, method="text", metadata=_metadata(document))


def _paragraph_chunk(p: Paragraph) -> Chunk | None:
    text = p.text.strip()
    if not text:
        return None
    style = p.style.name if p.style is not None else ""
    if style.startswith(("Heading", "Title")):
        return Chunk(position=0, text=text, kind="heading")
    if style.startswith("List"):
        text = f"- {text}"
    return Chunk(position=0, text=text, kind="paragraph")


def _table_chunk(table: Table) -> Chunk | None:
    # rendered as markdown rows: readable for humans and LLMs
    rows = []
    for row in table.rows:
        cells, seen = [], set()
        for cell in row.cells:
            if cell._tc in seen:  # merged cells repeat the same underlying cell
                continue
            seen.add(cell._tc)
            cells.append(cell.text.strip().replace("\n", " "))
        if any(cells):
            rows.append("| " + " | ".join(cells) + " |")
    if not rows:
        return None
    return Chunk(position=0, text="\n".join(rows), kind="table")


def _metadata(document) -> dict:
    props = document.core_properties
    meta = {
        "title": props.title,
        "author": props.author,
        "subject": props.subject,
        "created": props.created.isoformat() if props.created else None,
        "modified": props.modified.isoformat() if props.modified else None,
    }
    return {k: v for k, v in meta.items() if v}  # drop empty fields
