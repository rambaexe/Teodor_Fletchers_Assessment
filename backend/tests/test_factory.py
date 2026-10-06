from pathlib import Path

import pytest

from app.extraction.base import DocumentExtractor, ExtractionResult
from app.extraction.factory import ExtractorFactory, UnsupportedFileError


# fake extractors: test the factory without real file formats
class FakeAlpha(DocumentExtractor):
    file_type = "alpha"

    @classmethod
    def can_handle(cls, header: bytes, path: Path) -> bool:
        return header.startswith(b"ALPHA")

    def extract(self, path, on_progress):
        return ExtractionResult(chunks=[], method="text")


class FakeBeta(DocumentExtractor):
    file_type = "beta"

    @classmethod
    def can_handle(cls, header: bytes, path: Path) -> bool:
        return header.startswith(b"BETA")

    def extract(self, path, on_progress):
        return ExtractionResult(chunks=[], method="text")


@pytest.fixture
def factory():
    f = ExtractorFactory()
    f.register(FakeAlpha())
    f.register(FakeBeta())
    return f


def write(tmp_path: Path, name: str, content: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


def test_picks_extractor_by_content(factory, tmp_path):
    assert factory.for_file(write(tmp_path, "a.bin", b"ALPHA...")).file_type == "alpha"
    assert factory.for_file(write(tmp_path, "b.bin", b"BETA...")).file_type == "beta"


def test_ignores_misleading_extension(factory, tmp_path):
    # named like alpha, content is beta
    assert factory.for_file(write(tmp_path, "x.alpha", b"BETA...")).file_type == "beta"


def test_unknown_content_raises(factory, tmp_path):
    with pytest.raises(UnsupportedFileError, match="supported: alpha, beta"):
        factory.for_file(write(tmp_path, "c.bin", b"something else"))


def test_empty_file_raises(factory, tmp_path):
    with pytest.raises(UnsupportedFileError):
        factory.for_file(write(tmp_path, "empty.bin", b""))


def test_duplicate_registration_rejected(factory):
    with pytest.raises(ValueError):
        factory.register(FakeAlpha())


def test_supported_types(factory):
    assert factory.supported_types == ["alpha", "beta"]
