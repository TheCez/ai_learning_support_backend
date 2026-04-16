import uuid

from qdrant_client.http import models

from app.services.pdf_processor import extract_page_chunks
from app.services.vector_db import get_embedding_model, upsert_points


def ingest_pdf_to_qdrant(course_id: str, week: int, doc_id: str, file_path: str) -> None:
    try:
        chunk_records = extract_page_chunks(file_path, doc_id=doc_id)
        if not chunk_records:
            return

        texts = [record["text"] for record in chunk_records]
        vectors = list(get_embedding_model().embed(texts))

        points: list[models.PointStruct] = []
        for record, vector in zip(chunk_records, vectors):
            page_no = int(record["page_no"])
            chunk_index = int(record["chunk_index"])

            metadata = {
                "course_id": course_id,
                "page_no": page_no,
                "week": week,
                "doc_id": doc_id,
                "text": record["text"],
            }
            if record.get("image_url"):
                metadata["image_url"] = record["image_url"]

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{course_id}:{doc_id}:{page_no}:{chunk_index}:{record.get('kind', 'text')}",
                )
            )

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector.tolist(),
                    payload=metadata,
                )
            )

        upsert_points(points)
    except Exception:
        # Background tasks should not fail the upload response path.
        return
