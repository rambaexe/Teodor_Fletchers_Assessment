from pathlib import Path

from app.extractor.factory import ExtractorFactory
from app.models import Status
from app.repository import DocumentRepository


class IngestionService:
    """Runs one document through the pipeline: detect -> extract -> store. Writes status/progress as it goes."""

    def __init__(self, repository: DocumentRepository, extractors: ExtractorFactory) -> None:
        self.repository = repository
        self.extractors = extractors

    def process(self, doc_id: str) -> None:
        doc = self.repository.get(doc_id)
        if doc is None:
            return  # deleted before processing started

        try:
            self.repository.update(doc_id, status=Status.PROCESSING, progress=5)
            path = Path(doc.file_path)

            # factory picks the extractor from file content; service never checks the format itself
            extractor = self.extractors.for_file(path)
            self.repository.update(doc_id, file_type=extractor.file_type, progress=10)

            # extractor reports 0..1 -> stored as 10..90%
            def on_progress(fraction: float) -> None:
                self.repository.update(doc_id, progress=10 + int(fraction * 80))

            result = extractor.extract(path, on_progress)

            # TODO(enrichment): summary, category, keywords

            self.repository.update(
                doc_id,
                chunks=result.chunks,
                extraction_method=result.method,
                page_count=result.page_count,
                doc_metadata=result.metadata,
                status=Status.DONE,
                progress=100,
            )
        except Exception as e:
            self.repository.update(doc_id, status=Status.FAILED, error=str(e) or type(e).__name__)
