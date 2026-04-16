import logging
from functools import lru_cache

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
    )


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.embedding_model)


def ensure_collection() -> None:
    try:
        client = get_qdrant_client()
        collection_name = settings.qdrant_collection_name

        if client.collection_exists(collection_name=collection_name):
            return

        embedding_model = get_embedding_model()
        vector_size = len(next(embedding_model.embed(["dimension probe"])))

        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    except Exception as exc:
        logger.warning("Qdrant collection bootstrap failed - %s", exc)


def probe_qdrant_connection() -> bool:
    try:
        get_qdrant_client().get_collections()
        return True
    except Exception:
        return False


def initialize_qdrant() -> None:
    if not probe_qdrant_connection():
        logger.warning("Qdrant connection failed - Vector search will be unavailable")
        return

    ensure_collection()


def upsert_points(points: list[models.PointStruct]) -> None:
    if not points:
        return

    client = get_qdrant_client()
    client.upsert(collection_name=settings.qdrant_collection_name, points=points)


def search_vectors(query: str, course_id: str, limit: int = 5) -> list[dict[str, object]]:
    client = get_qdrant_client()
    embedding_model = get_embedding_model()
    query_vector = next(embedding_model.embed([query]))
    if hasattr(query_vector, "tolist"):
        query_vector = query_vector.tolist()
    else:
        query_vector = list(query_vector)

    course_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="course_id",
                match=models.MatchValue(value=course_id),
            )
        ]
    )

    query_response = client.query_points(
        collection_name=settings.qdrant_collection_name,
        query=query_vector,
        query_filter=course_filter,
        limit=limit,
        with_payload=True,
    )

    search_results = getattr(query_response, "points", query_response)

    mapped_results: list[dict[str, object]] = []
    for result in search_results:
        payload = result.payload or {}
        mapped_results.append(
            {
                "text": payload.get("text", ""),
                "score": float(result.score or 0.0),
                "doc_id": payload.get("doc_id"),
                "page_no": payload.get("page_no"),
                "week": payload.get("week"),
            }
        )

    return mapped_results
