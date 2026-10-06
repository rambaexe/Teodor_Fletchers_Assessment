from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.dependencies import get_service
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_service().recover_interrupted()  # background jobs don't survive a restart
    yield


app = FastAPI(title="Document Ingestion", lifespan=lifespan)
app.include_router(router)
