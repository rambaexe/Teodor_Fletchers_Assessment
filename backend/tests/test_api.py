import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app import main
from app.repository import InMemoryDocumentRepository
from app.service import IngestionService

PDF_BYTES = b"%PDF-1.4\n%minimal\n"


def make_docx_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document/>")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    # fresh repo + temp upload dir per test
    repo = InMemoryDocumentRepository()
    monkeypatch.setattr(main, "repository", repo)
    monkeypatch.setattr(main, "service", IngestionService(repo))
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path)
    return TestClient(main.app)


def upload(client, name: str, content: bytes):
    return client.post("/documents", files={"file": (name, content)})


def test_upload_pdf_is_processed(client):
    res = upload(client, "report.pdf", PDF_BYTES)
    assert res.status_code == 202
    assert res.json()["status"] == "queued"

    # TestClient runs background tasks before returning
    doc = client.get(f"/documents/{res.json()['id']}").json()
    assert doc["status"] == "done"
    assert doc["file_type"] == "pdf"
    assert doc["progress"] == 100


def test_docx_detected_from_content(client):
    doc_id = upload(client, "letter.docx", make_docx_bytes()).json()["id"]
    assert client.get(f"/documents/{doc_id}").json()["file_type"] == "docx"


def test_type_comes_from_bytes_not_extension(client):
    doc_id = upload(client, "fake.pdf", b"just some text").json()["id"]
    doc = client.get(f"/documents/{doc_id}").json()
    assert doc["status"] == "failed"
    assert "Unsupported" in doc["error"]


def test_list_newest_first(client):
    upload(client, "a.pdf", PDF_BYTES)
    upload(client, "b.pdf", PDF_BYTES)
    assert [d["filename"] for d in client.get("/documents").json()] == ["b.pdf", "a.pdf"]


def test_delete_removes_record_and_file(client, tmp_path):
    doc_id = upload(client, "a.pdf", PDF_BYTES).json()["id"]
    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get(f"/documents/{doc_id}").status_code == 404
    assert list(tmp_path.iterdir()) == []


def test_unknown_document_404(client):
    assert client.get("/documents/nope").status_code == 404
