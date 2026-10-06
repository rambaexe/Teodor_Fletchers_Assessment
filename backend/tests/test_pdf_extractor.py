from pathlib import Path

import pytest

from app.extractor.ocr import OcrProvider
from app.extractor.pdf.extractor import PdfExtractor
from tests.samples import DIGITAL_TEXT, make_pdf


class SpyOcr(OcrProvider):
    """Records calls so tests can check OCR only runs on scanned pages."""

    def __init__(self) -> None:
        self.calls = 0

    def extract_text(self, image: bytes) -> str:
        self.calls += 1
        return "scanned words"


def header(path: Path) -> bytes:
    return path.read_bytes()[:1024]


def extract(path: Path, ocr: OcrProvider | None = None):
    return PdfExtractor(ocr or SpyOcr()).extract(path, on_progress=lambda _: None)


def test_can_handle_pdf(tmp_path):
    path = make_pdf(tmp_path / "a.pdf", ["text"])
    assert PdfExtractor.can_handle(header(path), path)


def test_rejects_non_pdf(tmp_path):
    path = tmp_path / "fake.pdf"
    path.write_bytes(b"just text pretending to be a pdf")
    assert not PdfExtractor.can_handle(header(path), path)


def test_digital_pdf_uses_text_layer(tmp_path):
    ocr = SpyOcr()
    result = extract(make_pdf(tmp_path / "d.pdf", ["text", "text"]), ocr)

    assert result.method == "text"
    assert result.page_count == 2
    assert [(c.page, c.source) for c in result.chunks] == [(1, "text"), (2, "text")]
    assert DIGITAL_TEXT in result.chunks[0].text
    assert ocr.calls == 0


def test_scanned_pdf_uses_ocr(tmp_path):
    ocr = SpyOcr()
    result = extract(make_pdf(tmp_path / "s.pdf", ["image"]), ocr)

    assert result.method == "ocr"
    assert result.chunks[0].source == "ocr"
    assert result.chunks[0].text == "scanned words"
    assert ocr.calls == 1


def test_mixed_pdf(tmp_path):
    result = extract(make_pdf(tmp_path / "m.pdf", ["text", "image"]))
    assert result.method == "mixed"
    assert [c.source for c in result.chunks] == ["text", "ocr"]


def test_blank_pages_skipped_but_counted(tmp_path):
    result = extract(make_pdf(tmp_path / "b.pdf", ["text", "blank", "text"]))
    assert result.page_count == 3
    assert [c.page for c in result.chunks] == [1, 3]
    assert [c.position for c in result.chunks] == [0, 1]


def test_metadata(tmp_path):
    result = extract(make_pdf(tmp_path / "t.pdf", ["text"], title="Quarterly Report"))
    assert result.metadata["title"] == "Quarterly Report"
    assert result.metadata["author"] == "Jane Doe"


def test_reports_progress_per_page(tmp_path):
    progress: list[float] = []
    PdfExtractor(SpyOcr()).extract(make_pdf(tmp_path / "p.pdf", ["text"] * 4), progress.append)
    assert progress == [0.25, 0.5, 0.75, 1.0]


def test_mock_ocr_is_deterministic():
    from app.extractor.ocr import MockOcrProvider

    assert MockOcrProvider().extract_text(b"x" * 1500) == "[mock OCR text for 1,500-byte image]"


@pytest.mark.parametrize("pages", [["text"], ["image"]])
def test_chunks_are_pages(tmp_path, pages):
    result = extract(make_pdf(tmp_path / "k.pdf", pages))
    assert all(c.kind == "page" for c in result.chunks)
