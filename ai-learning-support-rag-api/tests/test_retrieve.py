from fastapi.testclient import TestClient

from app.main import app
import app.services.vector_db as vector_db

client = TestClient(app)


def test_retrieve_endpoint(monkeypatch):
    captured = {}

    class FakeEmbeddingVector:
        def tolist(self):
            return [0.1, 0.2]

    class FakeEmbeddingModel:
        def embed(self, texts):
            assert texts == ["cells"]
            return iter([FakeEmbeddingVector()])

    class FakeQdrantClient:
        def query_points(self, **kwargs):
            captured["search_kwargs"] = kwargs
            return type(
                "QueryResponse",
                (),
                {
                    "points": [
                        type(
                            "Result",
                            (),
                            {
                                "score": 0.92,
                                "payload": {
                                    "text": "cell division notes",
                                    "doc_id": "doc-1.pdf",
                                    "page_no": 3,
                                    "week": 2,
                                    "image_url": None,
                                },
                            },
                        )()
                    ]
                },
            )()

    monkeypatch.setattr(vector_db, "get_qdrant_client", lambda: FakeQdrantClient())
    monkeypatch.setattr(vector_db, "get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr(vector_db, "probe_qdrant_connection", lambda: True)

    response = client.get("/api/v1/courses/test_course/retrieve", params={"query": "cells"})

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "text": "cell division notes",
                "score": 0.92,
                "doc_id": "doc-1.pdf",
                "page_no": 3,
                "week": 2,
                "image_url": None,
            }
        ]
    }

    search_kwargs = captured["search_kwargs"]
    assert search_kwargs["collection_name"] == "course_materials"
    assert search_kwargs["limit"] == 20
    assert search_kwargs["query"] == [0.1, 0.2]
    assert search_kwargs["query_filter"].must[0].key == "course_id"
    assert search_kwargs["query_filter"].must[0].match.value == "test_course"


def test_retrieve_balances_image_then_text(monkeypatch):
    class FakeEmbeddingVector:
        def tolist(self):
            return [0.1, 0.2]

    class FakeEmbeddingModel:
        def embed(self, texts):
            assert texts == ["heart"]
            return iter([FakeEmbeddingVector()])

    class FakeQdrantClient:
        def query_points(self, **kwargs):
            return type(
                "QueryResponse",
                (),
                {
                    "points": [
                        type(
                            "Result",
                            (),
                            {
                                "score": 0.98,
                                "payload": {
                                    "text": "image caption A",
                                    "doc_id": "doc-1.pdf",
                                    "page_no": 1,
                                    "week": 2,
                                    "image_url": "/api/v1/images/a.png",
                                    "kind": "image",
                                },
                            },
                        )(),
                        type(
                            "Result",
                            (),
                            {
                                "score": 0.97,
                                "payload": {
                                    "text": "image caption B",
                                    "doc_id": "doc-1.pdf",
                                    "page_no": 1,
                                    "week": 2,
                                    "image_url": "/api/v1/images/b.png",
                                    "kind": "image",
                                },
                            },
                        )(),
                        type(
                            "Result",
                            (),
                            {
                                "score": 0.96,
                                "payload": {
                                    "text": "text chunk C",
                                    "doc_id": "doc-1.pdf",
                                    "page_no": 1,
                                    "week": 2,
                                    "image_url": None,
                                    "kind": "text",
                                },
                            },
                        )(),
                    ]
                },
            )()

    monkeypatch.setattr(vector_db, "get_qdrant_client", lambda: FakeQdrantClient())
    monkeypatch.setattr(vector_db, "get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr(vector_db, "probe_qdrant_connection", lambda: True)

    response = client.get(
        "/api/v1/courses/test_course/retrieve",
        params={"query": "heart", "limit": 3},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
    assert results[0]["image_url"] is not None
    assert results[1]["image_url"] is None


def test_retrieve_requires_query():
    response = client.get("/api/v1/courses/test_course/retrieve")
    assert response.status_code == 422


def test_retrieve_returns_503_when_vector_db_unreachable(monkeypatch):
    monkeypatch.setattr(vector_db, "probe_qdrant_connection", lambda: True)

    def raise_connection_error(**kwargs):
        raise ConnectionError("Qdrant unavailable")

    monkeypatch.setattr(vector_db, "search_vectors", raise_connection_error)

    response = client.get("/api/v1/courses/test_course/retrieve", params={"query": "cells"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Vector database is currently unreachable."}


def test_retrieve_ui_page_served():
    response = client.get("/api/v1/retrieve-ui")
    assert response.status_code == 200
    assert "RAG Retrieval Test UI" in response.text


def test_rag_test_app_page_served():
    response = client.get("/api/v1/rag-test-app")
    assert response.status_code == 200
    assert "RAG Test App" in response.text
