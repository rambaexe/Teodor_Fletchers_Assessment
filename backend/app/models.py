import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Status(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Chunk:
    position: int
    text: str
    kind: str = "paragraph"  # heading | paragraph | table | page
    page: int | None = None
    source: str = "text"  # text | ocr


@dataclass
class Document:
    filename: str
    file_path: str = ""
    size_bytes: int = 0
    sha256: str | None = None  # content hash; spots duplicate uploads
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_type: str | None = None  # detected from content, not extension
    status: Status = Status.QUEUED
    progress: int = 0  # 0-100
    error: str | None = None
    extraction_method: str | None = None  # text | ocr | mixed
    page_count: int | None = None
    metadata: dict = field(default_factory=dict)
    summary: str | None = None
    category: str | None = None
    keywords: list[str] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)  # bumped on every repository update
