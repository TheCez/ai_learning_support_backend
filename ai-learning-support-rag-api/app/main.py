from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import health, upload, retrieve
from app.services.local_storage import ensure_raw_pdf_storage
from app.services.vector_db import ensure_collection


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_raw_pdf_storage()
    ensure_collection()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(retrieve.router, prefix="/api/v1", tags=["retrieve"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Learning Support RAG API"}