### Further questions

For this component you need only prepare brief written answers, which will then be discussed
in more detail in the interview

1. Give a brief overview of a scalable architecture which would support this pipeline
   being run in production.

Please see [ARCHITECTURE.md](ARCHITECTURE.md).


2. How would your design change if you needed to support plain text files?

Very little changes. I'd add a TxtExtractor and register it in the factory; the service, database and API would stay the same. The frontend would also then just add .txt to allowed types. Extraction splits the text into paragraph chunks; there are no pages, and metadata is basic (encoding, line and character counts).
One fallback would be detecting of the actual text: Almost any file can look like text (no signatures like PDF and word), so the text extractor would go last in the factory. That way PDF and Word are always recognised first, and anything left over that reads as text is handled as plain text.


3. How would your design change if the number of documents being uploaded went up 100x?

One thing that would definitely change is the database. I'd move from SQLite to a database that supports many writers at once (e.g. Postgres), since SQLite only allows one writer at a time. Chunks would stay linked to their document, but I'd additionally organise content by category / topic, so there's also a content-based database for retrieving information across documents, not just per document. I'd also avoid storing the same information twice, e.g. by hashing uploaded files and skipping ones already processed.
I'd add queuing of jobs: instead of processing documents inside the API, uploads would go onto a job queue and separate workers would process them, so the API stays fast and more workers can be added as volume grows.
I'd move all checks to the backend (file type, size, duplicates), so the frontend only does quick checks for user experience and the backend is the single source of truth.
I'd limit the API calls to the external tools we use (OCR / LLM), with rate limits and retries, since at 100x volume those calls are the slowest and most expensive part.
I'd also optimise the extraction so we keep the important information without repeating it or overloading the chunks sent to the database (not scaling but worth to mention when it comes to volume of data coming in).