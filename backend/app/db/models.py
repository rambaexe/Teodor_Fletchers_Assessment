"""Database tables. MappedAsDataclass: rows behave like plain dataclasses too."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Status(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Chunk(Base):
    """One piece of extracted content (page / heading / paragraph / table), in order."""

    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True, init=False)
    position: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), default="paragraph")  # heading | paragraph | table | page
    page: Mapped[int | None] = mapped_column(default=None)  # None for docx
    source: Mapped[str] = mapped_column(String(8), default="text")  # text | ocr


class Document(Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(512), default="")
    size_bytes: Mapped[int] = mapped_column(default=0)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default_factory=lambda: str(uuid.uuid4()))
    file_type: Mapped[str | None] = mapped_column(String(16), default=None)  # detected from content
    status: Mapped[Status] = mapped_column(default=Status.QUEUED, index=True)
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    error: Mapped[str | None] = mapped_column(Text, default=None)
    extraction_method: Mapped[str | None] = mapped_column(String(16), default=None)  # text | ocr | mixed
    page_count: Mapped[int | None] = mapped_column(default=None)
    # "metadata" is reserved by SQLAlchemy -> attribute doc_metadata, column "metadata"
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSON, default_factory=dict)
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    category: Mapped[str | None] = mapped_column(String(64), default=None)
    keywords: Mapped[list[str]] = mapped_column(JSON, default_factory=list)
    created_at: Mapped[datetime] = mapped_column(default_factory=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default_factory=utc_now, onupdate=utc_now)

    chunks: Mapped[list[Chunk]] = relationship(
        default_factory=list, cascade="all, delete-orphan", order_by=Chunk.position
    )
