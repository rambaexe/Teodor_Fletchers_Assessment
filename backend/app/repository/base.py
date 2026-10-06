from abc import ABC, abstractmethod

from app.models import Document


class DocumentRepository(ABC):
    """Persistence boundary; swap implementations without touching service/routes."""

    @abstractmethod
    def add(self, doc: Document) -> None: ...

    @abstractmethod
    def get(self, doc_id: str) -> Document | None:
        """Full document, including chunks."""

    @abstractmethod
    def list(self) -> list[Document]:
        """Newest first. Chunks not loaded (summary view)."""

    @abstractmethod
    def update(self, doc_id: str, **fields) -> None:
        """Set fields; passing chunks= replaces all chunks. Bumps updated_at."""

    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """True if it existed. Chunks go with it."""
