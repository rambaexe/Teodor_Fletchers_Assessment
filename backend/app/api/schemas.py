"""Response schemas: the API contract, kept separate from domain models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import Status


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    text: str
    kind: str
    page: int | None
    source: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str | None
    size_bytes: int
    status: Status
    progress: int
    error: str | None
    extraction_method: str | None
    page_count: int | None
    category: str | None
    created_at: datetime
    updated_at: datetime


class DocumentDetailOut(DocumentOut):
    metadata: dict
    summary: str | None
    keywords: list[str]
    chunks: list[ChunkOut]
