from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.schemas.retrieve import RetrieveResponse
import app.services.vector_db as vector_db

router = APIRouter()
UI_FILE = Path(__file__).resolve().parents[2] / "static" / "retrieve_test_ui.html"
RAG_TEST_APP_FILE = Path(__file__).resolve().parents[2] / "static" / "rag_test_app.html"


@router.get("/retrieve-ui", include_in_schema=False)
async def retrieve_ui() -> FileResponse:
    return FileResponse(UI_FILE)


@router.get("/rag-test-app", include_in_schema=False)
async def rag_test_app() -> FileResponse:
    return FileResponse(RAG_TEST_APP_FILE)


@router.get("/courses/{course_id}/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(course_id: str, query: str, limit: int = Query(default=5, ge=1, le=20)):
    if not vector_db.probe_qdrant_connection():
        raise HTTPException(status_code=503, detail="Vector database is currently unreachable.")

    try:
        results = vector_db.search_vectors(query=query, course_id=course_id, limit=limit)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Vector database is currently unreachable.") from exc

    return RetrieveResponse(results=results)