# Architecture

## Frontend: React + TypeScript
- Upload PDF / Word files
- Table of documents (like a dataset preview): type, status + progress, extraction method (text / OCR / mixed), category
- Click a row: summary, keywords, metadata, extracted content

## Backend: Python + FastAPI
- Detects file type from content (not extension)
- Extracts text: PDF text layer, scanned pages via OCR; Word via python-docx
- Enriches: summary, category, keywords (LLM call, mocked)
- Runs in the background; status / progress stored per document
- REST API for upload + retrieval (incl. plain text for agent context)

```
upload -> detect type -> extract (text / OCR) -> enrich -> store
```

## Storage: SQLite
- `documents`: id, file info, status, extraction method, metadata, summary, category, keywords
- `chunks`: document_id (FK), page, text, source (text / OCR)

## Design
- Interfaces for everything swappable: extractors, OCR, enricher, repository
- Factory picks the extractor; new format = one new class
- Service runs the pipeline; routes stay thin; dependencies injected (SOLID)
