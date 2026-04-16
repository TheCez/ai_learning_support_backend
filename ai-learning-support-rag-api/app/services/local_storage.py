from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


def ensure_raw_pdf_storage() -> None:
    Path(settings.raw_pdf_storage_path).mkdir(parents=True, exist_ok=True)


def _safe_suffix(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    return suffix if suffix == ".pdf" else ".pdf"


async def save_pdf(course_id: str, file: UploadFile) -> dict[str, str | int]:
    ensure_raw_pdf_storage()
    course_dir = Path(settings.raw_pdf_storage_path) / course_id
    course_dir.mkdir(parents=True, exist_ok=True)

    doc_id = f"{Path(file.filename or 'document').stem}_{uuid4().hex}{_safe_suffix(file.filename or '')}"
    file_path = course_dir / doc_id

    content = await file.read()
    with open(file_path, "wb") as output_file:
        output_file.write(content)

    return {
        "doc_id": doc_id,
        "file_path": str(file_path),
        "file_size": len(content),
    }