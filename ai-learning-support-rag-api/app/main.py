import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1 import health, upload, retrieve
from app.core.config import settings
from app.services.local_storage import ensure_extracted_image_storage, ensure_raw_pdf_storage
from app.services.vector_db import initialize_qdrant


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_raw_pdf_storage()
    ensure_extracted_image_storage()
    asyncio.create_task(asyncio.to_thread(initialize_qdrant))
    yield

app = FastAPI(lifespan=lifespan)
ensure_extracted_image_storage()
app.mount(
    "/api/v1/images",
    StaticFiles(directory=settings.extracted_image_storage_path),
    name="images",
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(retrieve.router, prefix="/api/v1", tags=["retrieve"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Learning Support RAG API"}