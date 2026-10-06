import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import build_extractors, get_repository, get_service, get_upload_dir
from app.main import app
from app.repository import DocumentRepository
from app.service import IngestionService
from tests.samples import DIGITAL_TEXT, docx_bytes, pdf_bytes


@pytest.fixture
def client(tmp_path):
    # fresh db + temp upload dir per test, swapped in via FastAPI DI
    repo = DocumentRepository(tmp_path / "test.db")
    service = IngestionService(repo, build_extractors())
    app.dependency_overrides = {
        get_repository: lambda: repo,
        get_service: lambda: service,
        get_upload_dir: lambda: tmp_path / "uploads",
    }
    yield TestClient(app)
    app.dependency_overrides = {}


def upload(client, name: str, content: bytes) -> str:
    res = client.post("/documents", files={"file": (name, content)})
    assert res.status_code == 202
    assert res.json()["status"] == "queued"
    return res.json()["id"]


# TestClient runs background tasks before returning, so processing is finished by the next request


def test_digital_pdf_end_to_end(client):
    doc_id = upload(client, "report.pdf", pdf_bytes(["text", "text"], title="Q3 Report"))
    doc = client.get(f"/documents/{doc_id}").json()

    assert doc["status"] == "done"
    assert doc["progress"] == 100
    assert doc["file_type"] == "pdf"
    assert doc["extraction_method"] == "text"
    assert doc["page_count"] == 2
    assert doc["metadata"]["title"] == "Q3 Report"
    assert [c["page"] for c in doc["chunks"]] == [1, 2]


def test_scanned_pdf_goes_through_ocr(client):
    doc_id = upload(client, "scan.pdf", pdf_bytes(["text", "image"]))
    doc = client.get(f"/documents/{doc_id}").json()

    assert doc["extraction_method"] == "mixed"
    assert [c["source"] for c in doc["chunks"]] == ["text", "ocr"]


def test_docx_end_to_end(client):
    doc_id = upload(client, "letter.docx", docx_bytes())
    doc = client.get(f"/documents/{doc_id}").json()

    assert doc["status"] == "done"
    assert doc["file_type"] == "docx"
    assert doc["chunks"][0] == {"position": 0, "text": "Summary", "kind": "heading", "page": None, "source": "text"}


def test_text_endpoint_for_agents(client):
    doc_id = upload(client, "report.pdf", pdf_bytes(["text"]))
    text = client.get(f"/documents/{doc_id}/text").text
    assert DIGITAL_TEXT in text


def test_type_comes_from_bytes_not_extension(client):
    doc_id = upload(client, "fake.pdf", b"just some text")
    doc = client.get(f"/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert "Unsupported file type" in doc["error"]


def test_corrupt_pdf_fails_cleanly(client):
    doc_id = upload(client, "broken.pdf", b"%PDF-1.4\nnot really a pdf")
    doc = client.get(f"/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert doc["error"]


def test_list_newest_first(client):
    upload(client, "a.pdf", pdf_bytes(["text"]))
    upload(client, "b.pdf", pdf_bytes(["text"]))
    assert [d["filename"] for d in client.get("/documents").json()] == ["b.pdf", "a.pdf"]


def test_delete_removes_record_and_file(client, tmp_path):
    doc_id = upload(client, "a.pdf", pdf_bytes(["text"]))
    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get(f"/documents/{doc_id}").status_code == 404
    assert list((tmp_path / "uploads").iterdir()) == []


def test_unknown_document_404(client):
    assert client.get("/documents/nope").status_code == 404
