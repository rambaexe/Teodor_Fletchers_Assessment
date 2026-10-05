from fastapi import FastAPI

app = FastAPI(title="Document Ingestion")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
