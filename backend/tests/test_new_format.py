"""Adding a new format (.txt) = one new extractor class + one register() line. Nothing else changes."""

from pathlib import Path

import pytest

from app.api.dependencies import build_extractors
from app.db.models import Chunk
from app.extractor.base import DocumentExtractor, ExtractionResult
from app.extractor.factory import UnsupportedFileError
from tests.samples import make_docx, make_pdf


class TxtExtractor(DocumentExtractor):
    """Example new format. Text has no file signature: accept it if it decodes as UTF-8 text."""

    file_type = "txt"

    @classmethod
    def can_handle(cls, header: bytes, path: Path) -> bool:
        if not header or b"\x00" in header:  # empty / binary
            return False
        try:
            header.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False

    def extract(self, path, on_progress):
        paragraphs = [p.strip() for p in path.read_text(encoding="utf-8").split("\n\n") if p.strip()]
        on_progress(1.0)
        chunks = [Chunk(position=i, text=p) for i, p in enumerate(paragraphs)]
        return ExtractionResult(chunks=chunks, method="text")


@pytest.fixture
def factory():
    f = build_extractors()  # real PDF + Word extractors
    f.register(TxtExtractor())  # registered last: fallback after the specific formats
    return f


def write(tmp_path: Path, name: str, content: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_txt_file_uses_new_extractor(factory, tmp_path):
    path = write(tmp_path, "notes.txt", b"First paragraph.\n\nSecond paragraph.")
    extractor = factory.for_file(path)
    result = extractor.extract(path, on_progress=lambda _: None)

    assert extractor.file_type == "txt"
    assert [c.text for c in result.chunks] == ["First paragraph.", "Second paragraph."]


def test_existing_formats_still_win(factory, tmp_path):
    # PDF / Word are checked before the text fallback
    assert factory.for_file(write(tmp_path, "a.pdf", make_pdf(["text"]))).file_type == "pdf"
    assert factory.for_file(write(tmp_path, "b.docx", make_docx())).file_type == "docx"


def test_binary_file_still_unsupported(factory, tmp_path):
    with pytest.raises(UnsupportedFileError, match="pdf, docx, txt"):
        factory.for_file(write(tmp_path, "image.bin", b"\x89PNG\r\n\x1a\n\x00\x00"))
