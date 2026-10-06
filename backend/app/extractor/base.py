from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from app.models import Chunk

# progress as a fraction 0..1; service maps it onto the document's progress
ProgressFn = Callable[[float], None]


@dataclass
class ExtractionResult:
    """Same shape for every format; the rest of the pipeline only sees this."""

    chunks: list[Chunk]
    method: str  # text | ocr | mixed
    page_count: int | None = None  # None for formats without pages (e.g. docx)
    metadata: dict = field(default_factory=dict)  # title, author, ...


class DocumentExtractor(ABC):
    """One subclass per format. New format = new subclass, nothing else changes."""

    file_type: ClassVar[str]  # e.g. "pdf"; stored on the document

    @classmethod
    @abstractmethod
    def can_handle(cls, header: bytes, path: Path) -> bool:
        """True if this extractor recognises the file. Decide from content (header), not extension."""

    @abstractmethod
    def extract(self, path: Path, on_progress: ProgressFn) -> ExtractionResult:
        """Read the file into ordered chunks + metadata."""
