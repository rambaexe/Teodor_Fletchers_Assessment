import time

import pytest

from app.db.models import Chunk, Document, Status
from app.db.repository import DocumentRepository


@pytest.fixture
def repo(tmp_path) -> DocumentRepository:
    return DocumentRepository(tmp_path / "test.db")


def chunks(n: int) -> list[Chunk]:
    return [Chunk(position=i, text=f"chunk {i}", kind="page", page=i + 1) for i in range(n)]


def test_add_and_get(repo):
    doc = Document(filename="a.pdf", doc_metadata={"title": "Report"})
    repo.add(doc)

    got = repo.get(doc.id)
    assert got.filename == "a.pdf"
    assert got.status == Status.QUEUED
    assert got.doc_metadata == {"title": "Report"}


def test_get_missing_returns_none(repo):
    assert repo.get("nope") is None


def test_update_fields(repo):
    doc = Document(filename="a.pdf")
    repo.add(doc)
    repo.update(doc.id, status=Status.DONE, progress=100, file_type="pdf")

    got = repo.get(doc.id)
    assert (got.status, got.progress, got.file_type) == (Status.DONE, 100, "pdf")
    assert got.updated_at > got.created_at


def test_update_chunks_replaces_them(repo):
    doc = Document(filename="a.pdf")
    repo.add(doc)
    repo.update(doc.id, chunks=chunks(3))
    repo.update(doc.id, chunks=chunks(2))

    assert [c.text for c in repo.get(doc.id).chunks] == ["chunk 0", "chunk 1"]


def test_list_newest_first(repo):
    repo.add(Document(filename="first.pdf"))
    time.sleep(0.01)
    repo.add(Document(filename="second.pdf"))
    assert [d.filename for d in repo.list()] == ["second.pdf", "first.pdf"]


def test_delete_removes_doc_and_chunks(repo):
    doc = Document(filename="a.pdf")
    repo.add(doc)
    repo.update(doc.id, chunks=chunks(2))

    assert repo.delete(doc.id) is True
    assert repo.get(doc.id) is None
    assert repo.delete(doc.id) is False


def test_persists_across_restarts(tmp_path):
    doc = Document(filename="a.pdf")
    DocumentRepository(tmp_path / "db.sqlite").add(doc)
    assert DocumentRepository(tmp_path / "db.sqlite").get(doc.id) is not None
