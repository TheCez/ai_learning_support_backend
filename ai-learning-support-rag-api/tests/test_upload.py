from fastapi.testclient import TestClient
import fitz

from app.main import app
import app.services.vector_db as vector_db

client = TestClient(app)


def _make_pdf_bytes(text: str) -> bytes:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    content = pdf.tobytes()
    pdf.close()
    return content


def test_upload_pdf():
    response = client.post(
        "/api/v1/courses/test_course/documents",
        files={"file": ("test.pdf", _make_pdf_bytes("hello"), "application/pdf")},
        data={"week": "2"},
    )

    assert response.status_code == 200
    assert "metadata" in response.json()
    assert response.json()["metadata"]["course_id"] == "test_course"
    assert response.json()["metadata"]["week"] == 2
    assert response.json()["metadata"]["doc_id"].endswith(".pdf")


def test_upload_invalid_file_type():
    response = client.post(
        "/api/v1/courses/test_course/documents",
        files={"file": ("test_file.txt", b"This is not a PDF", "text/plain")},
        data={"week": "2"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF files are allowed."}


def test_upload_missing_file():
    response = client.post("/api/v1/courses/test_course/documents", data={"week": "2"})
    assert response.status_code == 422


def test_document_ready_endpoint(monkeypatch):
    monkeypatch.setattr(vector_db, "probe_qdrant_connection", lambda: True)
    monkeypatch.setattr(vector_db, "count_vectors_for_doc", lambda course_id, doc_id: 4)

    response = client.get("/api/v1/courses/test_course/documents/test_doc.pdf/ready")

    assert response.status_code == 200
    assert response.json() == {
        "course_id": "test_course",
        "doc_id": "test_doc.pdf",
        "ready": True,
        "indexed_chunks": 4,
    }


def test_document_ready_endpoint_503_when_unreachable(monkeypatch):
    monkeypatch.setattr(vector_db, "probe_qdrant_connection", lambda: False)

    response = client.get("/api/v1/courses/test_course/documents/test_doc.pdf/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Vector database is currently unreachable."}