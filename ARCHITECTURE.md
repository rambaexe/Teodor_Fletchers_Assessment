# Architecture

## Frontend: React + TypeScript
- Upload PDF / Word files (checked before upload)
- Table of documents: type, status (queued / extracting / stored / error), last updated
- Click a row: file info, extraction method (text / OCR / mixed), metadata, extracted content

## Backend: Python + FastAPI
```
upload -> save file + DB row -> background: pick extractor -> extract -> enrich -> store
```
- File type detected from content (first bytes), not extension
- PDF: per page, text layer if present, otherwise OCR (mocked)
- Word: headings, paragraphs, lists, tables in order
- Enrich: summary, category, keywords (LLM call, mocked)
- REST API for upload + retrieval

## Storage: SQLite
- `documents`: id, file info, status, progress, extraction method, page count, metadata
- `chunks`: document_id (FK), position, kind, page, text, source (text / OCR)

## Design
- `DocumentExtractor` interface: one class per format (`extractor/pdf`, `extractor/docx`)
- `ExtractorFactory` picks the extractor by asking each one `can_handle()`; new format = new class + one `register()` line
- `OcrProvider` / `Enricher` interfaces injected; mocks now
- `IngestionService` runs the pipeline

## Pipeline / flow

**Upload**
- `UploadArea.tsx` -> `POST /documents`
- `api/routes.py` -> file saved to `data/uploads`, DB row created (queued), returns 202

**Process** (background, `service.py`)
- `extractor/factory.py` -> `for_file()`: first bytes -> PDF / Word extractor
- `extractor/pdf | docx` -> `extract()`: chunks + metadata (scanned pages -> `extractor/ocr.py`)
- `enricher/mock.py` -> `enrich()`: summary, category, keywords
- `db/repository.py` -> `update()`: chunks saved, status done (or failed + error)

**Show**
- `App.tsx` -> `GET /documents`: list, polled while anything is processing
- `DocumentDetail.tsx` -> `GET /documents/{id}`: document + chunks
- "Copy as text" -> `GET /documents/{id}/text`: plain text, agent-ready

**Wiring**
- everything created once in `api/dependencies.py`
