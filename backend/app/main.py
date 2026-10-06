import os
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict

from app.models import Document, Status
from app.repository import InMemoryDocumentRepository
from app.service import IngestionService

UPLOAD_DIR = Path(os.environ.get("DATA_DIR", "data")) / "uploads"

# composition root: only place concrete implementations are chosen
repository = InMemoryDocumentRepository()
service = IngestionService(repository)

app = FastAPI(title="Document Ingestion")


# --- response schemas (API contract, separate from domain models) ---


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
    status: Status
    progress: int
    error: str | None
    extraction_method: str | None
    page_count: int | None
    category: str | None
    created_at: datetime


class DocumentDetailOut(DocumentOut):
    metadata: dict
    summary: str | None
    keywords: list[str]
    chunks: list[ChunkOut]


# --- routes ---


def _get_or_404(doc_id: str) -> Document:
    doc = repository.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/documents", response_model=DocumentOut, status_code=202)
def upload_document(file: UploadFile, background: BackgroundTasks):
    doc = Document(filename=file.filename or "upload")

    # stored under the doc id: avoids name clashes / path tricks in user filenames
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{doc.id}{Path(doc.filename).suffix.lower()}"
    with path.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    doc.file_path = str(path)

    repository.add(doc)
    background.add_task(service.process, doc.id)  # runs after response is sent
    return doc


@app.get("/documents", response_model=list[DocumentOut])
def list_documents():
    return repository.list()


@app.get("/documents/{doc_id}", response_model=DocumentDetailOut)
def get_document(doc_id: str):
    return _get_or_404(doc_id)


@app.get("/documents/{doc_id}/text", response_class=PlainTextResponse)
def get_document_text(doc_id: str):
    # plain text, ready to drop into an agent's context
    return "\n\n".join(chunk.text for chunk in _get_or_404(doc_id).chunks)


@app.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str):
    doc = _get_or_404(doc_id)
    repository.delete(doc_id)
    Path(doc.file_path).unlink(missing_ok=True)
