import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_repository, get_service, get_upload_dir
from app.api.schemas import DocumentDetailOut, DocumentOut
from app.db.models import Document
from app.db.repository import DocumentRepository
from app.service import IngestionService

router = APIRouter()


def _get_or_404(repository: DocumentRepository, doc_id: str) -> Document:
    doc = repository.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/documents", response_model=DocumentOut, status_code=202)
def upload_document(
    file: UploadFile,
    background: BackgroundTasks,
    repository: DocumentRepository = Depends(get_repository),
    service: IngestionService = Depends(get_service),
    upload_dir: Path = Depends(get_upload_dir),
):
    doc = Document(filename=file.filename or "upload")

    # stored under the doc id: avoids name clashes / path tricks in user filenames
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{doc.id}{Path(doc.filename).suffix.lower()}"
    with path.open("wb") as out:
        shutil.copyfileobj(file.file, out)  # streams in blocks
    doc.file_path = str(path)
    doc.size_bytes = path.stat().st_size

    repository.add(doc)
    background.add_task(service.process, doc.id)  # runs after response is sent
    return doc


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(repository: DocumentRepository = Depends(get_repository)):
    return repository.list()


@router.get("/documents/{doc_id}", response_model=DocumentDetailOut)
def get_document(doc_id: str, repository: DocumentRepository = Depends(get_repository)):
    return _get_or_404(repository, doc_id)


@router.get("/documents/{doc_id}/text", response_class=PlainTextResponse)
def get_document_text(doc_id: str, repository: DocumentRepository = Depends(get_repository)):
    # plain text, ready to drop into an agent's context
    return "\n\n".join(chunk.text for chunk in _get_or_404(repository, doc_id).chunks)


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str, repository: DocumentRepository = Depends(get_repository)):
    doc = _get_or_404(repository, doc_id)
    repository.delete(doc_id)
    Path(doc.file_path).unlink(missing_ok=True)
