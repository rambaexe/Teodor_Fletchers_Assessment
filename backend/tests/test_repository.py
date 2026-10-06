"""Contract tests: every DocumentRepository implementation must pass the same suite."""

import time

import pytest

from app.models import Chunk, Document, Status
from app.repository import DocumentRepository, InMemoryDocumentRepository, SqliteDocumentRepository


@pytest.fixture(params=["memory", "sqlite"])
def repo(request, tmp_path) -> DocumentRepository:
    if request.param == "memory":
        return InMemoryDocumentRepository()
    return SqliteDocumentRepository(tmp_path / "test.db")


def make_doc(name: str = "a.pdf") -> Document:
    return Document(filename=name, file_path=f"/tmp/{name}", size_bytes=10, sha256="abc")


def chunks(n: int) -> list[Chunk]:
    return [Chunk(position=i, text=f"chunk {i}", kind="page", page=i + 1) for i in range(n)]


def test_add_and_get_roundtrip(repo):
    doc = make_doc()
    doc.metadata = {"title": "Report"}
    doc.keywords = ["finance"]
    repo.add(doc)

    got = repo.get(doc.id)
    assert got.filename == "a.pdf"
    assert got.status == Status.QUEUED
    assert got.metadata == {"title": "Report"}
    assert got.keywords == ["finance"]
    assert got.sha256 == "abc"
    assert got.created_at.tzinfo is not None  # always timezone-aware (UTC)


def test_get_missing_returns_none(repo):
    assert repo.get("nope") is None


def test_update_fields_and_bumps_updated_at(repo):
    doc = make_doc()
    repo.add(doc)
    before = repo.get(doc.id).updated_at
    time.sleep(0.01)

    repo.update(doc.id, status=Status.DONE, progress=100, file_type="pdf", metadata={"author": "Jo"})

    got = repo.get(doc.id)
    assert (got.status, got.progress, got.file_type) == (Status.DONE, 100, "pdf")
    assert got.metadata == {"author": "Jo"}
    assert got.updated_at > before


def test_update_chunks_replaces_them(repo):
    doc = make_doc()
    repo.add(doc)
    repo.update(doc.id, chunks=chunks(3))
    repo.update(doc.id, chunks=chunks(2))

    got = repo.get(doc.id)
    assert [c.text for c in got.chunks] == ["chunk 0", "chunk 1"]
    assert [c.page for c in got.chunks] == [1, 2]


def test_list_newest_first_without_chunks(repo):
    first = make_doc("first.pdf")
    repo.add(first)
    time.sleep(0.01)  # created_at is set when the Document is built
    second = make_doc("second.pdf")
    repo.add(second)
    repo.update(first.id, chunks=chunks(2))

    listed = repo.list()
    assert [d.filename for d in listed] == ["second.pdf", "first.pdf"]
    assert all(d.chunks == [] for d in listed)  # summary view


def test_delete_removes_doc_and_chunks(repo):
    doc = make_doc()
    repo.add(doc)
    repo.update(doc.id, chunks=chunks(2))

    assert repo.delete(doc.id) is True
    assert repo.get(doc.id) is None
    assert repo.delete(doc.id) is False


def test_returned_docs_are_copies(repo):
    doc = make_doc()
    repo.add(doc)
    got = repo.get(doc.id)
    got.filename = "changed.pdf"  # mutating the result must not change storage
    assert repo.get(doc.id).filename == "a.pdf"


def test_sqlite_persists_across_instances(tmp_path):
    db = tmp_path / "persist.db"
    doc = make_doc()
    SqliteDocumentRepository(db).add(doc)
    assert SqliteDocumentRepository(db).get(doc.id).filename == "a.pdf"  # e.g. after a restart
