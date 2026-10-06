import zipfile
from pathlib import Path


def detect_file_type(path: Path) -> str | None:
    """Type from file bytes (magic numbers); extension/content-type are untrusted."""
    with path.open("rb") as f:
        header = f.read(8)

    if header.startswith(b"%PDF-"):
        return "pdf"
    # docx = zip containing word/document.xml
    if header.startswith(b"PK\x03\x04") and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            if "word/document.xml" in z.namelist():
                return "docx"
    return None
