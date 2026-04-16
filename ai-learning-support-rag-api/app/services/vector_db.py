from functools import lru_cache

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings


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


def upsert_points(points: list[models.PointStruct]) -> None:
    if not points:
        return

    client = get_qdrant_client()
    client.upsert(collection_name=settings.qdrant_collection_name, points=points)
