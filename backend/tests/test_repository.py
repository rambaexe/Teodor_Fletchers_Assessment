import time

import pytest

from app.db.models import Chunk, Document, Status
from app.db.repository import DocumentRepository


@pytest.fixture
def repo(tmp_path) -> DocumentRepository:
    return DocumentRepository(tmp_path / "test.db")


def test_add_get_update(repo):
    doc = Document(filename="a.pdf")
    repo.add(doc)
    repo.update(doc.id, status=Status.DONE, chunks=[Chunk(position=0, text="hello")])

    got = repo.get(doc.id)
    assert got.status == Status.DONE
    assert [c.text for c in got.chunks] == ["hello"]


def test_list_newest_first(repo):
    repo.add(Document(filename="first.pdf"))
    time.sleep(0.01)
    repo.add(Document(filename="second.pdf"))
    assert [d.filename for d in repo.list()] == ["second.pdf", "first.pdf"]


def test_delete_removes_document_and_chunks(repo):
    doc = Document(filename="a.pdf")
    repo.add(doc)
    repo.update(doc.id, chunks=[Chunk(position=0, text="x")])

    assert repo.delete(doc.id) is True
    assert repo.get(doc.id) is None
    assert repo.delete(doc.id) is False
