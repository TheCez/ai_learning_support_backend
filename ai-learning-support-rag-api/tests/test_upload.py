from fastapi.testclient import TestClient
import fitz

from app.main import app

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