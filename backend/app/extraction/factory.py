from pathlib import Path

from app.extraction.base import DocumentExtractor

HEADER_BYTES = 1024


class UnsupportedFileError(Exception):
    pass


class ExtractorFactory:
    """Picks the extractor for a file by asking each registered one if it can handle it.

    Extractors are registered as instances (with their dependencies already injected),
    shared across documents, so they must be stateless.
    """

    def __init__(self) -> None:
        self._extractors: list[DocumentExtractor] = []

    def register(self, extractor: DocumentExtractor) -> None:
        if extractor.file_type in self.supported_types:
            raise ValueError(f"Extractor for '{extractor.file_type}' already registered")
        self._extractors.append(extractor)

    @property
    def supported_types(self) -> list[str]:
        return [e.file_type for e in self._extractors]

    def for_file(self, path: Path) -> DocumentExtractor:
        with path.open("rb") as f:
            header = f.read(HEADER_BYTES)

        # chain of responsibility: first extractor that recognises the file wins
        for extractor in self._extractors:
            if extractor.can_handle(header, path):
                return extractor

        supported = ", ".join(self.supported_types) or "none"
        raise UnsupportedFileError(f"Unsupported file type (supported: {supported})")
