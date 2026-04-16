from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.services.ingestion_pipeline import ingest_pdf_to_qdrant
from app.services.local_storage import save_pdf

router = APIRouter()

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