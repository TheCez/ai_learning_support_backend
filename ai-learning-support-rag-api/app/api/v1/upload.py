from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.services.ingestion_pipeline import ingest_pdf_to_qdrant
from app.services.local_storage import save_pdf
import app.services.vector_db as vector_db

router = APIRouter()


@router.get("/courses/{course_id}/documents/{doc_id}/ready")
async def document_index_ready(course_id: str, doc_id: str):
    if not vector_db.probe_qdrant_connection():
        raise HTTPException(status_code=503, detail="Vector database is currently unreachable.")

    try:
        indexed_chunks = vector_db.count_vectors_for_doc(course_id=course_id, doc_id=doc_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Vector database is currently unreachable.") from exc

    return {
        "course_id": course_id,
        "doc_id": doc_id,
        "ready": indexed_chunks > 0,
        "indexed_chunks": indexed_chunks,
    }

@router.post("/courses/{course_id}/documents")
async def upload_pdf(
    course_id: str,
    background_tasks: BackgroundTasks,
    week: int = Form(...),
    file: UploadFile = File(...),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    saved_file = await save_pdf(course_id=course_id, file=file)
    doc_id = str(saved_file["doc_id"])

    background_tasks.add_task(
        ingest_pdf_to_qdrant,
        course_id=course_id,
        week=week,
        doc_id=doc_id,
        file_path=str(saved_file["file_path"]),
    )

    return {
        "message": "File uploaded. Ingestion started in background.",
        "metadata": {
            "course_id": course_id,
            "week": week,
            "doc_id": doc_id,
            "file_name": file.filename,
            "file_path": saved_file["file_path"],
            "file_size": saved_file["file_size"],
        },
    }