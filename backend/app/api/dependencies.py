"""Composition root: the only place concrete implementations are chosen.

Routes get these via FastAPI Depends; tests swap them with app.dependency_overrides.
"""

import os
from pathlib import Path

from app.repository import DocumentRepository, InMemoryDocumentRepository
from app.service import IngestionService

UPLOAD_DIR = Path(os.environ.get("DATA_DIR", "data")) / "uploads"

_repository = InMemoryDocumentRepository()
_service = IngestionService(_repository)


def get_repository() -> DocumentRepository:
    return _repository


def get_service() -> IngestionService:
    return _service


def get_upload_dir() -> Path:
    return UPLOAD_DIR
