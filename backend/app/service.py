from pathlib import Path

from app.extractors import detect_file_type
from app.models import Status
from app.repository import DocumentRepository


class UnsupportedFileError(Exception):
    pass


class IngestionService:
    """Runs one document through the pipeline; writes status/progress as it goes."""

    def __init__(self, repository: DocumentRepository) -> None:
        self.repository = repository

    def process(self, doc_id: str) -> None:
        doc = self.repository.get(doc_id)
        if doc is None:
            return  # deleted before processing started

        try:
            self.repository.update(doc_id, status=Status.PROCESSING, progress=10)

            file_type = detect_file_type(Path(doc.file_path))
            if file_type is None:
                raise UnsupportedFileError("Unsupported file type (expected PDF or DOCX)")
            self.repository.update(doc_id, file_type=file_type, progress=30)

            # TODO(feat/extraction): extract chunks + metadata
            # TODO(feat/enrichment): summary, category, keywords

            self.repository.update(doc_id, status=Status.DONE, progress=100)
        except Exception as e:
            self.repository.update(doc_id, status=Status.FAILED, error=str(e))
