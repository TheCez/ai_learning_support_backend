from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_retrieve_endpoint():
    course_id = "test_course"
    response = client.get(f"/api/v1/courses/{course_id}/retrieve", params={"query": "cells"})

    assert response.status_code == 200
    assert response.json()["course_id"] == course_id
    assert response.json()["query"] == "cells"


def test_retrieve_requires_query():
    response = client.get("/api/v1/courses/test_course/retrieve")
    assert response.status_code == 422