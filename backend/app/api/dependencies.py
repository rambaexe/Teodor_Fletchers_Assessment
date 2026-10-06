"""Composition root: the only place concrete implementations are created and wired.

Routes get these via FastAPI Depends; tests swap them with app.dependency_overrides.
"""

import os
from pathlib import Path

from app.enricher.mock import MockLlmEnricher
from app.extractor.docx.extractor import DocxExtractor
from app.extractor.factory import ExtractorFactory
from app.extractor.ocr import MockOcrProvider
from app.extractor.pdf.extractor import PdfExtractor
from app.db.repository import DocumentRepository
from app.service import IngestionService

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
UPLOAD_DIR = DATA_DIR / "uploads"


def build_extractors() -> ExtractorFactory:
    # new format = one more register() line
    factory = ExtractorFactory()
    factory.register(PdfExtractor(ocr=MockOcrProvider()))
    factory.register(DocxExtractor())
    return factory


_repository = DocumentRepository(DATA_DIR / "documents.db")
_service = IngestionService(_repository, build_extractors(), MockLlmEnricher())


def get_repository() -> DocumentRepository:
    return _repository


def get_service() -> IngestionService:
    return _service


def get_upload_dir() -> Path:
    return UPLOAD_DIR
