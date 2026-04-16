from fastapi import APIRouter, Query

from app.schemas.retrieve import RetrieveResponse
from app.services.vector_db import search_vectors

router = APIRouter()


@router.get("/courses/{course_id}/retrieve", response_model=RetrieveResponse)
async def retrieve_documents(course_id: str, query: str, limit: int = Query(default=5, ge=1, le=20)):
    results = search_vectors(query=query, course_id=course_id, limit=limit)
    return RetrieveResponse(results=results)