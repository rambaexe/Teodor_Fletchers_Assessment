from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.extractor.base import DocumentExtractor, ExtractionResult, ProgressFn
from app.extractor.ocr import OcrProvider
from app.models import Chunk

PDF_MAGIC = b"%PDF-"
MIN_TEXT_CHARS = 20  # fewer chars on a page -> treat as scanned, use OCR


class PdfExtractor(DocumentExtractor):
    """PDF, one chunk per page. Per page: text layer if present, else OCR its images."""

    file_type = "pdf"

    def __init__(self, ocr: OcrProvider) -> None:
        self.ocr = ocr  # injected: mock now, real OCR service later

    @classmethod
    def can_handle(cls, header: bytes, path: Path) -> bool:
        return PDF_MAGIC in header  # spec allows junk before the marker

    def extract(self, path: Path, on_progress: ProgressFn) -> ExtractionResult:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):  # "" = no user password set
            raise PdfReadError("PDF is password-protected")

        chunks: list[Chunk] = []
        total = len(reader.pages)
        for i, page in enumerate(reader.pages):
            chunk = self._read_page(page, page_number=i + 1)
            if chunk:  # blank pages are skipped
                chunk.position = len(chunks)
                chunks.append(chunk)
            on_progress((i + 1) / total)

        return ExtractionResult(
            chunks=chunks,
            method=_method(chunks),
            page_count=total,
            metadata=_metadata(reader),
        )

    def _read_page(self, page, page_number: int) -> Chunk | None:
        text = (page.extract_text() or "").strip()
        if len(text) >= MIN_TEXT_CHARS:
            return Chunk(position=0, text=text, kind="page", page=page_number, source="text")

        # little/no text layer -> scanned page: OCR each embedded image
        ocr_text = "\n".join(self.ocr.extract_text(img.data) for img in page.images).strip()
        if ocr_text:
            return Chunk(position=0, text=ocr_text, kind="page", page=page_number, source="ocr")

        # short text, no images (e.g. a page with just a title): keep what's there
        return Chunk(position=0, text=text, kind="page", page=page_number) if text else None


def _method(chunks: list[Chunk]) -> str:
    sources = {c.source for c in chunks}
    if sources == {"ocr"}:
        return "ocr"
    return "mixed" if "ocr" in sources else "text"


def _metadata(reader: PdfReader) -> dict:
    info = reader.metadata
    if not info:
        return {}
    try:
        created = info.creation_date.isoformat() if info.creation_date else None
    except ValueError:  # malformed date strings are common in the wild
        created = None
    meta = {
        "title": info.title,
        "author": info.author,
        "subject": info.subject,
        "creator": info.creator,  # authoring app, e.g. "Microsoft Word"
        "created": created,
    }
    return {k: v for k, v in meta.items() if v}
