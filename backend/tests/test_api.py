import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import build_extractors, get_repository, get_service, get_upload_dir
from app.db.repository import DocumentRepository
from app.enricher.mock import MockLlmEnricher
from app.main import app
from app.service import IngestionService
from tests.samples import PDF_TEXT, make_docx, make_pdf


@pytest.fixture
def client(tmp_path):
    # temp db + upload dir, swapped in via FastAPI dependency overrides
    repo = DocumentRepository(tmp_path / "test.db")
    service = IngestionService(repo, build_extractors(), MockLlmEnricher())
    app.dependency_overrides = {
        get_repository: lambda: repo,
        get_service: lambda: service,
        get_upload_dir: lambda: tmp_path / "uploads",
    }
    yield TestClient(app)
    app.dependency_overrides = {}


def upload(client, name: str, content: bytes) -> dict:
    res = client.post("/documents", files={"file": (name, content)})
    assert res.status_code == 202
    # TestClient runs the background job before returning, so it's already processed
    return client.get(f"/documents/{res.json()['id']}").json()


def test_pdf_upload_end_to_end(client):
    doc = upload(client, "report.pdf", make_pdf(["text"], title="Q3 Report"))
    assert doc["status"] == "done"
    assert doc["file_type"] == "pdf"
    assert doc["metadata"]["title"] == "Q3 Report"
    assert doc["summary"] and doc["category"]  # enriched
    assert PDF_TEXT in client.get(f"/documents/{doc['id']}/text").text


def test_docx_upload_end_to_end(client):
    doc = upload(client, "letter.docx", make_docx())
    assert doc["status"] == "done"
    assert doc["chunks"][0]["kind"] == "heading"


@pytest.mark.parametrize("content", [b"", b"just text renamed to pdf"])
def test_unsupported_or_empty_file_fails(client, content):
    doc = upload(client, "fake.pdf", content)
    assert doc["status"] == "failed"
    assert "Unsupported file type" in doc["error"]


def test_list_and_delete(client):
    doc = upload(client, "a.pdf", make_pdf(["text"]))
    assert [d["id"] for d in client.get("/documents").json()] == [doc["id"]]

    assert client.delete(f"/documents/{doc['id']}").status_code == 204
    assert client.get(f"/documents/{doc['id']}").status_code == 404
