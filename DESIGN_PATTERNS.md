# Design patterns

What's implemented, where, and why. Each pattern maps to something that genuinely varies (file formats, OCR / LLM vendor, storage), not patterns for their own sake.

## Overview

| Pattern | Where | In one line |
|---|---|---|
| Interface (ABC) | `DocumentExtractor`, `OcrProvider`, `Enricher` | Contract every implementation must follow |
| Polymorphism | `service.py` calling `extractor.extract()` | Same call, each format does its own thing |
| Factory + registry | `ExtractorFactory` | Picks the right extractor for a file |
| Chain of Responsibility | `ExtractorFactory.for_file()` | Ask each extractor "can you handle this?" until one says yes |
| Strategy | `OcrProvider`, `Enricher` implementations | Swappable algorithms behind one interface |
| Dependency Injection | constructors + FastAPI `Depends` | Classes receive what they need, don't create it |
| Composition Root | `api/dependencies.py` | The one place concrete classes are chosen and wired |
| Facade / Service layer | `IngestionService.process()` | One call hides the whole pipeline |
| Repository | `db/repository.py` | All database access behind one class |
| Adapter | PDF / DOCX extractors | Wrap third-party libraries into our own shape |
| Observer (callback) | `on_progress` / `ProgressFn` | Extractors report progress; the service decides what to do with it |
| Common result object (DTO) | `ExtractionResult`, `Enrichment`, `api/schemas.py` | One shape for every format; API contract separate from DB |

---

## 1. Interface (Abstract Base Class)

**What:** a class that only defines *which methods must exist*. Python enforces it: a subclass missing a method can't be instantiated.

**Where:**
- [`extractor/base.py`](backend/app/extractor/base.py) `DocumentExtractor`: `file_type`, `can_handle(header, path)`, `extract(path, on_progress)`
- [`extractor/ocr.py`](backend/app/extractor/ocr.py) `OcrProvider`: `extract_text(image)`
- [`enricher/base.py`](backend/app/enricher/base.py) `Enricher`: `enrich(text)`

**Why:** the rest of the system depends on the contract, not on PDF / Word / a specific OCR or LLM vendor.

## 2. Polymorphism

**What:** one method call, different behaviour depending on the object's class.

**Where:** [`service.py`](backend/app/service.py):
```python
extractor = self.extractors.for_file(path)     # PdfExtractor or DocxExtractor
result = extractor.extract(path, on_progress)  # each runs its own extract()
```

**Why:** the service has no `if pdf / elif docx`. Adding a format never touches it.

## 3. Factory + registry

**What:** an object whose job is to create / pick the right implementation, so callers don't decide themselves.

**Where:** [`extractor/factory.py`](backend/app/extractor/factory.py) `ExtractorFactory`
- `register(extractor)`: add an extractor (duplicates rejected)
- `for_file(path)`: return the extractor for this file, or raise `UnsupportedFileError`
- `supported_types`: what's registered (used in the error message)

**Why:** **Open/Closed principle**. New format (e.g. `.txt`) = new `TxtExtractor` class + one `register()` line in `dependencies.py`. No existing code edited.

## 4. Chain of Responsibility

**What:** a request is passed along a list of handlers; the first that can handle it does.

**Where:** `ExtractorFactory.for_file()` reads the first 1 KB once, then asks each extractor `can_handle()` in order. First yes wins.

**Why:** each format owns its own detection logic (PDF: `%PDF-` marker; DOCX: zip containing `word/document.xml`). Type comes from **content, not the file extension**, so a renamed file can't fool it.

## 5. Strategy

**What:** a family of interchangeable algorithms behind one interface, chosen at runtime.

**Where:**
- `OcrProvider`: `MockOcrProvider` now; Tesseract / AWS Textract / Google Document AI later
- `Enricher`: `MockLlmEnricher` now; a real LLM (e.g. Claude) later
- Inside [`pdf/extractor.py`](backend/app/extractor/pdf/extractor.py) `_read_page()`: per page, text layer if present, otherwise OCR. Digital vs scanned PDFs (the case the brief calls out). *Honest note: this one is a simple per-page decision rather than separate strategy classes; it would become proper strategies if more page-reading methods were added.*

**Why:** swap vendors or algorithms without touching the code that uses them. Mocks satisfy the brief's "no paid APIs".

## 6. Dependency Injection

**What:** a class receives its collaborators (usually via its constructor) instead of creating them.

**Where:**
- `PdfExtractor(ocr=...)`: OCR passed in
- `IngestionService(repository, extractors, enricher)`
- Routes get repository / service / upload dir via FastAPI `Depends(get_repository)` etc. ([`api/routes.py`](backend/app/api/routes.py))

**Why:** **Dependency Inversion principle**. Classes depend on interfaces; implementations can be swapped (mock → real, SQLite → Postgres). Also makes testing easy: FastAPI's `app.dependency_overrides` can swap in a temp database.

## 7. Composition Root

**What:** the single place where all concrete classes are created and connected.

**Where:** [`api/dependencies.py`](backend/app/api/dependencies.py)
```python
factory.register(PdfExtractor(ocr=MockOcrProvider()))
factory.register(DocxExtractor())
_service = IngestionService(_repository, build_extractors(), MockLlmEnricher())
```

**Why:** going from mocks to real services, or adding a format, is a change in this one file.

## 8. Facade / Service layer

**What:** one simple entry point hiding a complicated subsystem.

**Where:** [`service.py`](backend/app/service.py) `IngestionService.process(id)`: routes make one call; behind it sit the factory, extractor, OCR, enricher and repository, plus status / progress / error handling.

**Why:** routes stay thin (HTTP only); pipeline logic lives in one place and doesn't know about HTTP.

## 9. Repository

**What:** a class that hides how data is stored behind simple methods.

**Where:** [`db/repository.py`](backend/app/db/repository.py) `DocumentRepository`: `add`, `get`, `list`, `update`, `delete`. Tables in [`db/models.py`](backend/app/db/models.py).

**Why:** no SQL / SQLAlchemy outside `db/`. Postgres = change the connection URL.
*Design choice: no repository interface. There's only one implementation; add an interface when a second one actually exists (YAGNI). Extractors / OCR / enricher do get interfaces because multiple implementations are real.*

## 10. Adapter

**What:** wraps something with an incompatible interface so it fits the one your code expects.

**Where:** `PdfExtractor` adapts `pypdf`, `DocxExtractor` adapts `python-docx`: both turn library-specific objects into our `ExtractionResult` / `Chunk`s.

**Why:** third-party libraries are imported only inside their extractor. Swapping `pypdf` for another PDF library touches one file.

## 11. Observer (callback)

**What:** a component notifies a listener of events without knowing what the listener does.

**Where:** `ProgressFn` in [`extractor/base.py`](backend/app/extractor/base.py). Extractors call `on_progress(fraction)` per page / block; the service's callback writes it to the database as 10–85%; the frontend polls and shows a progress bar.

**Why:** extractors don't know about databases or HTTP; they just report progress.

## 12. Common result objects (DTOs) + schema separation

**What:** plain data objects that carry data between layers in one agreed shape.

**Where:**
- `ExtractionResult` (chunks, method, page_count, metadata): every extractor returns this
- `Enrichment` (summary, category, keywords): every enricher returns this
- [`api/schemas.py`](backend/app/api/schemas.py) `DocumentOut` / `DocumentDetailOut`: what the API sends, kept separate from the DB tables

**Why:** **Liskov substitution**: any extractor can replace another since the output shape is identical. The API contract can stay stable while the database changes.

---

## SOLID summary

| Principle | How |
|---|---|
| **S**ingle responsibility | routes = HTTP, extractors = parsing, enricher = enrichment, repository = storage, service = orchestration |
| **O**pen/closed | new format = new extractor class + `register()`; nothing else edited |
| **L**iskov substitution | every extractor returns `ExtractionResult`; every enricher returns `Enrichment`; any can replace another |
| **I**nterface segregation | small interfaces: `extract` + `can_handle`, `extract_text`, `enrich` |
| **D**ependency inversion | service depends on interfaces; concrete classes chosen only in `dependencies.py` |

## Frontend

| Pattern | Where | Why |
|---|---|---|
| Container / presentational components | `App.tsx` owns state + polling; `DocumentTable`, `DocumentDetail`, `UploadArea`, `Toasts` mostly render props | UI pieces stay simple and reusable |
| Custom hook | `useToasts.ts` (`notify`, `dismiss`) | Toast logic reusable from anywhere, separate from rendering |
| API client module | `api.ts`: all `fetch` calls + types in one place | Components never build URLs; one place to change the API |

## Considered, not implemented

| Pattern | Idea | Why not (yet) |
|---|---|---|
| Decorator | `FallbackEnricher(primary=LLM, fallback=mock)` for resilience; `CachingEnricher` to avoid paying for the same LLM call twice | Most useful with a real LLM; ~15 lines each if wanted |
| Template Method | base class defines extraction steps, subclasses fill them in | PDF and Word differ too much; would be forced |
| Repository interface | `DocumentRepository` ABC + multiple implementations | Only one implementation (YAGNI) |
