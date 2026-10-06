# Document Ingestion Pipeline - Fletchers Assessment

- Uploading `.pdf` / `.docx` files

- Extracting and store their content, and retrieve it through a web UI and REST API.


- Brief: [BRIEFING.md](BRIEFING.md)
- Written answers: [Follow-Up Questions.md](Follow-Up%20Questions.md)

**Stack:** Python + FastAPI (backend), React + TypeScript + Vite (frontend).

## Running

### Option 1: Docker

```bash
./start.sh
```

Docker picks free ports. The script prints the URLs and opens the app in your browser. On Windows, run it from Git Bash. Stop with `docker compose down`.

### Option 2: Locally (uv + npm)

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node 20+.

From the repo root:

```bash
npm install   # installs frontend + backend deps
npm run dev   # starts both, live reload
```

Open http://localhost:5173 (or the next free port Vite prints). Ctrl+C stops both.

## Flow

How an uploaded file moves through the code.

### 0. Startup (wiring, once)
- `backend/app/main.py` - creates the FastAPI `app`, includes the router from `api/routes.py`
- `backend/app/api/dependencies.py` - builds everything once (composition root):
  - `DocumentRepository(data/documents.db)` (`db/repository.py`) - creates SQLite tables from `db/models.py` if missing
  - `build_extractors()` - `ExtractorFactory` with `PdfExtractor(ocr=MockOcrProvider())` + `DocxExtractor()` registered
  - `MockLlmEnricher()` (`enricher/mock.py`)
  - `IngestionService(repository, factory, enricher)`

### 1. Upload (frontend)
1. `frontend/src/components/UploadArea.tsx` `uploadAll()` - user drops / picks files; `isAccepted()` (`api.ts`) checks the extension, wrong type -> toast, not uploaded
2. `frontend/src/api.ts` `api.upload(file)` - `POST /api/documents` (multipart form)
3. `frontend/vite.config.ts` - dev proxy forwards `/api/*` to the backend (`localhost:8000`), strips `/api`

### 2. Save (backend, during the request)
4. `backend/app/api/routes.py` `upload_document()`
   - gets repository / service / upload dir via `Depends(...)` from `dependencies.py`
   - creates a `Document` (`db/models.py`): new id, status `queued`
   - streams the file to `data/uploads/<id>.pdf`, sets path + size
   - `repository.add(doc)` - inserts the row in SQLite
   - `background.add_task(service.process, doc.id)` - schedules processing
   - returns `202` straight away, shaped by `DocumentOut` (`api/schemas.py`)

### 3. Process (backend, background)
5. `backend/app/service.py` `IngestionService.process(id)`
   - `repository.get(id)`, then status `processing`
   - **pick extractor**: `extractor/factory.py` `for_file(path)` reads the first 1 KB, asks each registered extractor `can_handle(header, path)`:
     - `extractor/pdf/extractor.py`: contains `%PDF-`?
     - `extractor/docx/extractor.py`: zip containing `word/document.xml`?
     - none -> `UnsupportedFileError`
   - **extract**: `extractor.extract(path, on_progress)`
     - PDF: `_read_page()` per page -> text layer if it has text, else images -> `ocr.extract_text()` (`extractor/ocr.py`, `MockOcrProvider`); `_method()` -> text / ocr / mixed; `_metadata()` from PDF info
     - DOCX: `_paragraph_chunk()` / `_table_chunk()` per block, in order; `_metadata()` from core properties
     - both return `ExtractionResult` (`extractor/base.py`) holding `Chunk`s (`db/models.py`)
     - `on_progress(fraction)` -> `repository.update(progress=10..85)` after each page / block
   - **enrich**: chunk text joined (capped at 20k chars) -> `enricher.enrich(text)` (`enricher/base.py` interface, `enricher/mock.py` `MockLlmEnricher`)
     - summary: first sentences
     - keywords: most frequent meaningful words
     - category: keyword hints -> invoice / contract / report / cv / letter / other
   - **store**: `repository.update(chunks, extraction_method, page_count, doc_metadata, summary, category, keywords, status=done, progress=100)` - replaces chunk rows in SQLite
   - any exception -> `update(status=failed, error=message)`

### 4. Show (frontend <-> backend)
6. `frontend/src/App.tsx` `refresh()` -> `api.list()` -> `GET /documents` -> `routes.list_documents()` -> `repository.list()` (newest first, no chunks) -> `DocumentOut`
   - repeats every 1s while anything is queued / processing; toast if a doc just failed
7. `frontend/src/components/DocumentTable.tsx` - a row per doc: file, type, status badge + progress bar, updated (`STATUS_LABEL`, `typeLabel()` in `api.ts`)
8. Click a row -> `frontend/src/components/DocumentDetail.tsx` -> `api.get(id)` -> `GET /documents/{id}` -> `routes.get_document()` -> `repository.get(id)` (with chunks) -> `DocumentDetailOut` -> file info, method, category, summary, keywords, metadata, chunks
9. "Copy as text" -> `api.text(id)` -> `GET /documents/{id}/text` -> `routes.get_document_text()` - chunks joined as plain text (agent-ready)
10. Delete -> `api.remove(id)` -> `DELETE /documents/{id}` -> `routes.delete_document()` -> `repository.delete()` (chunks cascade) + uploaded file removed
11. Errors anywhere -> `notify()` (`frontend/src/useToasts.ts`) -> `frontend/src/components/Toasts.tsx`
