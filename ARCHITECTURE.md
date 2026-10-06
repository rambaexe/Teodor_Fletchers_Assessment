# Architecture

## Flow

```
POST /documents
  -> save file, create record (status: queued)
  -> background: IngestionService.process(id)
       1. ExtractorFactory  sniff file bytes -> PdfExtractor / DocxExtractor
       2. Extractor         -> ExtractionResult (chunks + metadata)
                            PDF: per page, text layer if present else OCR (OcrProvider)
       3. Enricher          -> summary, category, keywords (mock LLM)
       4. Repository        -> save, status: done
     progress written at each step; any error -> status: failed + message
```

## Backend (`backend/app/`)

| File | Role |
|---|---|
| `main.py` | HTTP routes only; composition root (wires concrete classes) |
| `models.py` | shared data types |
| `extractors.py` | `DocumentExtractor` interface, PDF/DOCX extractors, `ExtractorFactory` |
| `ocr.py` | `OcrProvider` interface + mock |
| `enrichment.py` | `Enricher` interface + mock LLM |
| `repository.py` | `DocumentRepository` interface + implementations |
| `service.py` | `IngestionService`: orchestrates the pipeline |

## Patterns

| Pattern | Where |
|---|---|
| Interface (ABC) | `DocumentExtractor`, `OcrProvider`, `Enricher`, `DocumentRepository` |
| Factory + registry | `ExtractorFactory`; extractors self-register, chosen by file content not extension |
| Strategy | PDF page: text layer vs OCR |
| Dependency injection | service gets its collaborators via constructor; wired once in `main.py` |
| Repository | all persistence behind `DocumentRepository` |
| Service layer | `IngestionService`; routes stay thin |

## SOLID

- **S**: routes = HTTP, extractors = parsing, enricher = enrichment, repository = storage, service = orchestration
- **O**: new format (e.g. `.txt`) = one new registered extractor class, nothing else edited
- **L**: every extractor returns the same `ExtractionResult`; service never branches on format
- **I**: small single-method interfaces (`extract`, `extract_text`, `enrich`)
- **D**: service depends on interfaces only; mocks -> Textract / Claude / Postgres without touching it

## Storage

- `documents`: id (PK), filename, file_type, file_path, status, progress, error, extraction_method (text / ocr / mixed), page_count, metadata (JSON), summary, category, keywords (JSON), created_at
- `chunks`: id, document_id (FK, cascade), position, page, kind (heading / paragraph / table / page), text, source (text / ocr)

## API

| Method | Path | |
|---|---|---|
| POST | `/documents` | upload, returns record (202) |
| GET | `/documents` | list, newest first |
| GET | `/documents/{id}` | record + chunks |
| GET | `/documents/{id}/text` | plain text, ready for agent context |
| DELETE | `/documents/{id}` | remove record + file |
