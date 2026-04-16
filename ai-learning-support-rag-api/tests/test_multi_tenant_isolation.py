from fastapi.testclient import TestClient
import fitz

from app.main import app
import app.api.v1.retrieve as retrieve_module

client = TestClient(app)


def _make_pdf_bytes(text: str) -> bytes:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    content = pdf.tobytes()
    pdf.close()
    return content


def test_multi_tenant_isolation():
    def fake_search_vectors(query: str, course_id: str, limit: int = 5):
        return [
            {
                "text": f"chunk for {course_id}",
                "score": 0.9,
                "doc_id": f"{course_id}.pdf",
                "page_no": 1,
                "week": 1,
            }
        ]

    original_search_vectors = retrieve_module.search_vectors
    retrieve_module.search_vectors = fake_search_vectors

    course_id_1 = "course_1"
    course_id_2 = "course_2"

    try:
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
        assert retrieve_response_1.json()["results"][0]["doc_id"] == f"{course_id_1}.pdf"

        retrieve_response_2 = client.get(
            f"/api/v1/courses/{course_id_2}/retrieve",
            params={"query": "intro"},
        )
        assert retrieve_response_2.status_code == 200
        assert retrieve_response_2.json()["results"][0]["doc_id"] == f"{course_id_2}.pdf"
    finally:
        retrieve_module.search_vectors = original_search_vectors