import copy
import dataclasses
import threading

from app.models import Document, utc_now
from app.repository.base import DocumentRepository


class InMemoryDocumentRepository(DocumentRepository):
    # fast, no files: used in tests
    # lock: background jobs write from worker threads

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}
        self._lock = threading.Lock()

    def add(self, doc: Document) -> None:
        with self._lock:
            self._docs[doc.id] = copy.deepcopy(doc)

    def get(self, doc_id: str) -> Document | None:
        with self._lock:
            doc = self._docs.get(doc_id)
            return copy.deepcopy(doc) if doc else None

    def list(self) -> list[Document]:
        with self._lock:
            docs = sorted(self._docs.values(), key=lambda d: d.created_at, reverse=True)
            return [dataclasses.replace(copy.deepcopy(d), chunks=[]) for d in docs]

    def update(self, doc_id: str, **fields) -> None:
        with self._lock:
            doc = self._docs[doc_id]
            for name, value in fields.items():
                setattr(doc, name, copy.deepcopy(value))
            doc.updated_at = utc_now()

    def delete(self, doc_id: str) -> bool:
        with self._lock:
            return self._docs.pop(doc_id, None) is not None
