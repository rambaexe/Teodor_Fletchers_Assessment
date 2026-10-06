"""Response schemas: the API contract, kept separate from domain models."""

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.db.models import Status

# SQLite drops tz info; stored values are UTC -> mark them so clients don't read local time
UtcDatetime = Annotated[datetime, AfterValidator(lambda d: d if d.tzinfo else d.replace(tzinfo=timezone.utc))]


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
    created_at: UtcDatetime
    updated_at: UtcDatetime


class DocumentDetailOut(DocumentOut):
    metadata: dict = Field(validation_alias="doc_metadata")
    summary: str | None
    keywords: list[str]
    chunks: list[ChunkOut]
