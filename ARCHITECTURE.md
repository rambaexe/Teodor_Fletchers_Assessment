# Architecture

## Frontend: React + TypeScript
- Upload PDF / Word files (checked before upload)
- Table of documents: type, status (queued / extracting / stored / error), last updated
- Click a row: file info, extraction method (text / OCR / mixed), metadata, extracted content
- Errors shown as toasts

## Backend: Python + FastAPI
```
upload -> save file + DB row -> background: pick extractor -> extract -> store chunks
```
- File type detected from content (first bytes), not the extension
- PDF: per page, text layer if present, otherwise OCR (mocked)
- Word: headings, paragraphs, lists, tables in order
- REST API for upload + retrieval, incl. plain text for agent context

## Storage: SQLite
- `documents`: id, file info, status, progress, extraction method, page count, metadata
- `chunks`: document_id (FK), position, kind, page, text, source (text / OCR)

## Design
- `DocumentExtractor` interface: one class per format (`extractor/pdf`, `extractor/docx`)
- `ExtractorFactory` picks the extractor by asking each one `can_handle()`; new format = new class + one `register()` line
- `OcrProvider` interface injected into the PDF extractor; mock now, real OCR service later
- `IngestionService` runs the pipeline; routes stay thin; everything wired in `api/dependencies.py`
