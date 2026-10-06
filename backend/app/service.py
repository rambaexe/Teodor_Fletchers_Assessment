from pathlib import Path

from app.db.models import Status
from app.db.repository import DocumentRepository
from app.enricher.base import Enricher
from app.extractor.factory import ExtractorFactory

# cap text sent to the enricher (an LLM has a context / cost budget)
ENRICH_MAX_CHARS = 20_000


class IngestionService:
    """Runs one document through the pipeline: detect -> extract -> enrich -> store. Writes status/progress as it goes."""

    def __init__(self, repository: DocumentRepository, extractors: ExtractorFactory, enricher: Enricher) -> None:
        self.repository = repository
        self.extractors = extractors
        self.enricher = enricher

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

            # extractor reports 0..1 -> stored as 10..85%
            def on_progress(fraction: float) -> None:
                self.repository.update(doc_id, progress=10 + int(fraction * 75))

            result = extractor.extract(path, on_progress)

            # enrich: summary / category / keywords from the extracted text
            self.repository.update(doc_id, progress=90)
            text = "\n\n".join(c.text for c in result.chunks)[:ENRICH_MAX_CHARS]
            enrichment = self.enricher.enrich(text)

            self.repository.update(
                doc_id,
                chunks=result.chunks,
                extraction_method=result.method,
                page_count=result.page_count,
                doc_metadata=result.metadata,
                summary=enrichment.summary,
                category=enrichment.category,
                keywords=enrichment.keywords,
                status=Status.DONE,
                progress=100,
            )
        except Exception as e:
            self.repository.update(doc_id, status=Status.FAILED, error=str(e) or type(e).__name__)
