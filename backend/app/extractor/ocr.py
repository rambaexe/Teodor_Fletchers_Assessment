from abc import ABC, abstractmethod


class OcrProvider(ABC):
    """Image -> text. Swap the mock for Tesseract / Textract / Document AI without touching extractors."""

    @abstractmethod
    def extract_text(self, image: bytes) -> str: ...


class MockOcrProvider(OcrProvider):
    # brief allows mocking paid services; deterministic so tests can assert on it
    def extract_text(self, image: bytes) -> str:
        return f"[mock OCR text for {len(image):,}-byte image]"
