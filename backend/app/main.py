from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Document Ingestion")
app.include_router(router)
