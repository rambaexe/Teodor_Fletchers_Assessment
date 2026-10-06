"""Composition root: the only place concrete implementations are created.

Routes get these via FastAPI Depends; tests swap them with app.dependency_overrides.
"""

import os
from pathlib import Path

from app.repository import DocumentRepository
from app.service import IngestionService

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
UPLOAD_DIR = DATA_DIR / "uploads"

_repository = DocumentRepository(DATA_DIR / "documents.db")
_service = IngestionService(_repository)


def get_repository() -> DocumentRepository:
    return _repository


def get_service() -> IngestionService:
    return _service


def get_upload_dir() -> Path:
    return UPLOAD_DIR
