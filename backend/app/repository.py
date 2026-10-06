"""All database access goes through here (SQLite; Postgres = change the URL)."""

from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import selectinload, sessionmaker

from app.models import Base, Document


class DocumentRepository:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread off: background jobs run in worker threads (one session per call)
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)  # creates tables on first run
        self._session = sessionmaker(engine, expire_on_commit=False)

    def add(self, doc: Document) -> None:
        with self._session.begin() as s:
            s.add(doc)

    def get(self, doc_id: str) -> Document | None:
        """With chunks."""
        with self._session() as s:
            query = select(Document).where(Document.id == doc_id).options(selectinload(Document.chunks))
            return s.scalar(query)

    def list(self) -> list[Document]:
        """Newest first, without chunks."""
        with self._session() as s:
            return list(s.scalars(select(Document).order_by(Document.created_at.desc())))

    def update(self, doc_id: str, **fields) -> None:
        """Set fields; chunks= replaces all chunks."""
        with self._session.begin() as s:
            doc = s.get(Document, doc_id)
            if doc is None:
                raise KeyError(doc_id)
            for name, value in fields.items():
                if name == "chunks":
                    doc.chunks.clear()
                    s.flush()  # delete old chunks before inserting new ones
                    doc.chunks.extend(value)
                else:
                    setattr(doc, name, value)

    def delete(self, doc_id: str) -> bool:
        with self._session.begin() as s:
            doc = s.get(Document, doc_id)
            if doc is None:
                return False
            s.delete(doc)  # chunks deleted too (cascade)
            return True
