import zipfile
from pathlib import Path

import pytest

from app.extractor.docx import DocxExtractor
from tests.samples import docx_bytes


@pytest.fixture
def sample_docx(tmp_path: Path) -> Path:
    path = tmp_path / "report.docx"
    path.write_bytes(docx_bytes())
    return path


def header(path: Path) -> bytes:
    return path.read_bytes()[:1024]


def test_can_handle_docx(sample_docx):
    assert DocxExtractor.can_handle(header(sample_docx), sample_docx)


def test_rejects_plain_zip(tmp_path):
    path = tmp_path / "archive.docx"  # misleading extension
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("readme.txt", "hi")
    assert not DocxExtractor.can_handle(header(path), path)


def test_rejects_non_zip(tmp_path):
    path = tmp_path / "fake.docx"
    path.write_bytes(b"%PDF-1.4 not a docx")
    assert not DocxExtractor.can_handle(header(path), path)


def test_extracts_blocks_in_order(sample_docx):
    result = DocxExtractor().extract(sample_docx, on_progress=lambda _: None)

    assert [(c.kind, c.text) for c in result.chunks] == [
        ("heading", "Summary"),
        ("paragraph", "Revenue grew this quarter."),
        ("paragraph", "- First point"),
        ("table", "| Region | Revenue |\n| EU | 1.2m |"),
        ("paragraph", "Closing note."),
    ]
    assert [c.position for c in result.chunks] == [0, 1, 2, 3, 4]
    assert all(c.source == "text" and c.page is None for c in result.chunks)


def test_result_fields(sample_docx):
    result = DocxExtractor().extract(sample_docx, on_progress=lambda _: None)
    assert result.method == "text"
    assert result.page_count is None
    assert result.metadata["title"] == "Quarterly Report"
    assert result.metadata["author"] == "Jane Doe"


def test_reports_progress_to_completion(sample_docx):
    progress: list[float] = []
    DocxExtractor().extract(sample_docx, on_progress=progress.append)
    assert progress == sorted(progress)
    assert progress[-1] == 1.0
