"""PDF + Word extraction: normal files, empty files, images, metadata."""

from pathlib import Path

from app.extractor.docx.extractor import DocxExtractor
from app.extractor.ocr import MockOcrProvider
from app.extractor.pdf.extractor import PdfExtractor
from tests.samples import PDF_TEXT, make_docx, make_pdf


def extract_pdf(tmp_path: Path, pages: list[str], title: str | None = None):
    path = tmp_path / "doc.pdf"
    path.write_bytes(make_pdf(pages, title))
    return PdfExtractor(MockOcrProvider()).extract(path, on_progress=lambda _: None)


def extract_docx(tmp_path: Path, **kwargs):
    path = tmp_path / "doc.docx"
    path.write_bytes(make_docx(**kwargs))
    return DocxExtractor().extract(path, on_progress=lambda _: None)


# --- PDF ---


def test_pdf_digital_uses_text_layer(tmp_path):
    result = extract_pdf(tmp_path, ["text", "text"])
    assert result.method == "text"
    assert result.page_count == 2
    assert [c.page for c in result.chunks] == [1, 2]
    assert PDF_TEXT in result.chunks[0].text


def test_pdf_scanned_page_goes_to_ocr(tmp_path):
    result = extract_pdf(tmp_path, ["image"])
    assert result.method == "ocr"
    assert result.chunks[0].source == "ocr"
    assert result.chunks[0].text.startswith("[mock OCR text")


def test_pdf_mixed_text_and_scanned(tmp_path):
    result = extract_pdf(tmp_path, ["text", "image"])
    assert result.method == "mixed"
    assert [c.source for c in result.chunks] == ["text", "ocr"]


def test_pdf_blank_pages_skipped(tmp_path):
    result = extract_pdf(tmp_path, ["blank", "blank"])
    assert result.page_count == 2
    assert result.chunks == []


def test_pdf_metadata(tmp_path):
    result = extract_pdf(tmp_path, ["text"], title="Q3 Report")
    assert result.metadata["title"] == "Q3 Report"
    assert result.metadata["author"] == "Jane Doe"


# --- Word ---


def test_docx_blocks_in_order(tmp_path):
    result = extract_docx(tmp_path)
    assert [(c.kind, c.text) for c in result.chunks] == [
        ("heading", "Summary"),
        ("paragraph", "Revenue grew this quarter."),
        ("paragraph", "- First point"),
        ("table", "| Region | Revenue |\n| EU | 1.2m |"),
    ]
    assert result.page_count is None


def test_docx_empty(tmp_path):
    assert extract_docx(tmp_path, content=False).chunks == []


def test_docx_image_only_has_no_text(tmp_path):
    # images in Word are skipped (no OCR for docx)
    assert extract_docx(tmp_path, content=False, image=True).chunks == []


def test_docx_metadata(tmp_path):
    result = extract_docx(tmp_path, title="Contract")
    assert result.metadata["title"] == "Contract"
    assert result.metadata["author"] == "Jane Doe"
