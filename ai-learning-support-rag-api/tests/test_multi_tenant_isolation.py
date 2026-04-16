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


def test_multi_tenant_isolation():
    course_id_1 = "course_1"
    course_id_2 = "course_2"

    response_1 = client.post(
        f"/api/v1/courses/{course_id_1}/documents",
        files={"file": ("test1.pdf", _make_pdf_bytes("course 1"), "application/pdf")},
        data={"week": "1"},
    )
    assert response_1.status_code == 200
    assert response_1.json()["metadata"]["course_id"] == course_id_1

    response_2 = client.post(
        f"/api/v1/courses/{course_id_2}/documents",
        files={"file": ("test2.pdf", _make_pdf_bytes("course 2"), "application/pdf")},
        data={"week": "2"},
    )
    assert response_2.status_code == 200
    assert response_2.json()["metadata"]["course_id"] == course_id_2

    retrieve_response_1 = client.get(
        f"/api/v1/courses/{course_id_1}/retrieve",
        params={"query": "intro"},
    )
    assert retrieve_response_1.status_code == 200
    assert retrieve_response_1.json()["course_id"] == course_id_1

    retrieve_response_2 = client.get(
        f"/api/v1/courses/{course_id_2}/retrieve",
        params={"query": "intro"},
    )
    assert retrieve_response_2.status_code == 200
    assert retrieve_response_2.json()["course_id"] == course_id_2