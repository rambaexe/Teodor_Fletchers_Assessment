"""SQLite via SQLAlchemy. Same code runs on Postgres by changing the URL."""

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.models import Chunk, Document, Status, utc_now
from app.repository.base import DocumentRepository


# --- tables (persistence shape; kept separate from domain dataclasses) ---


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str | None] = mapped_column(String(16))
    file_path: Mapped[str] = mapped_column(String(512))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)  # spot duplicates
    status: Mapped[str] = mapped_column(String(16), index=True)
    progress: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str | None] = mapped_column(String(16))
    page_count: Mapped[int | None] = mapped_column(Integer)
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSON)  # "metadata" is reserved by SQLAlchemy
    summary: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    keywords: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    chunks: Mapped[list["ChunkRow"]] = relationship(
        cascade="all, delete-orphan", order_by="ChunkRow.position"  # lazy: list() never loads chunks
    )


class ChunkRow(Base):
    __tablename__ = "chunks"
    __table_args__ = (UniqueConstraint("document_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(16))
    page: Mapped[int | None] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(8))


# --- repository ---

# domain field -> column attribute, where names differ
_RENAMED = {"metadata": "doc_metadata"}


class SqliteDocumentRepository(DocumentRepository):
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread off: background jobs use worker threads (one session per call)
        self._engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        event.listen(self._engine, "connect", _sqlite_pragmas)
        self._session = sessionmaker(self._engine, expire_on_commit=False)
        Base.metadata.create_all(self._engine)  # prototype: no migrations (Alembic in prod)

    def add(self, doc: Document) -> None:
        with self._session.begin() as s:
            s.add(_to_row(doc))

    def get(self, doc_id: str) -> Document | None:
        with self._session() as s:
            row = s.get(DocumentRow, doc_id)
            return _to_domain(row, with_chunks=True) if row else None

    def list(self) -> list[Document]:
        with self._session() as s:
            rows = s.scalars(
                select(DocumentRow).order_by(DocumentRow.created_at.desc())
            ).all()
            return [_to_domain(r, with_chunks=False) for r in rows]

    def update(self, doc_id: str, **fields) -> None:
        with self._session.begin() as s:
            row = s.get(DocumentRow, doc_id)
            if row is None:
                raise KeyError(doc_id)
            for name, value in fields.items():
                if name == "chunks":
                    # delete old rows first, else (document_id, position) clashes on insert
                    row.chunks.clear()
                    s.flush()
                    row.chunks.extend(_chunk_row(c) for c in value)
                elif name == "status":
                    row.status = Status(value).value
                else:
                    setattr(row, _RENAMED.get(name, name), value)
            row.updated_at = utc_now()

    def delete(self, doc_id: str) -> bool:
        with self._session.begin() as s:
            row = s.get(DocumentRow, doc_id)
            if row is None:
                return False
            s.delete(row)
            return True


def _sqlite_pragmas(dbapi_conn, _record) -> None:
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")  # off by default in SQLite; needed for cascade
    cur.execute("PRAGMA journal_mode=WAL")  # readers don't block the background writer
    cur.close()


# --- mapping: domain dataclass <-> row ---


def _to_row(doc: Document) -> DocumentRow:
    return DocumentRow(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_path=doc.file_path,
        size_bytes=doc.size_bytes,
        sha256=doc.sha256,
        status=Status(doc.status).value,
        progress=doc.progress,
        error=doc.error,
        extraction_method=doc.extraction_method,
        page_count=doc.page_count,
        doc_metadata=doc.metadata,
        summary=doc.summary,
        category=doc.category,
        keywords=doc.keywords,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=[_chunk_row(c) for c in doc.chunks],
    )


def _chunk_row(c: Chunk) -> ChunkRow:
    return ChunkRow(position=c.position, kind=c.kind, page=c.page, text=c.text, source=c.source)


def _to_domain(row: DocumentRow, with_chunks: bool) -> Document:
    return Document(
        id=row.id,
        filename=row.filename,
        file_type=row.file_type,
        file_path=row.file_path,
        size_bytes=row.size_bytes,
        sha256=row.sha256,
        status=Status(row.status),
        progress=row.progress,
        error=row.error,
        extraction_method=row.extraction_method,
        page_count=row.page_count,
        metadata=row.doc_metadata or {},
        summary=row.summary,
        category=row.category,
        keywords=row.keywords or [],
        created_at=_utc(row.created_at),
        updated_at=_utc(row.updated_at),
        chunks=[
            Chunk(position=c.position, text=c.text, kind=c.kind, page=c.page, source=c.source)
            for c in row.chunks
        ]
        if with_chunks
        else [],
    )


def _utc(dt: datetime) -> datetime:
    # SQLite drops tz info; values are always stored as UTC
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
