from typing import Any, Dict, List
from pydantic import BaseModel
import qdrant_client

class VectorStore:
    def __init__(self, db_client: qdrant_client.QdrantClient):
        self.db_client = db_client

    def insert_vector(self, vector: List[float], metadata: Dict[str, Any]) -> str:
        # Insert a vector into the database with associated metadata
        response = self.db_client.upsert(
            collection_name="vectors",
            points=[
                {
                    "id": metadata["page_id"],
                    "vector": vector,
                    "payload": metadata
                }
            ]
        )
        return response

    def retrieve_vector(self, vector_id: str) -> Dict[str, Any]:
        # Retrieve a vector from the database by its ID
        response = self.db_client.get(
            collection_name="vectors",
            ids=[vector_id]
        )
        return response

    def delete_vector(self, vector_id: str) -> None:
        # Delete a vector from the database by its ID
        self.db_client.delete(
            collection_name="vectors",
            ids=[vector_id]
        )

    def search_vectors(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        # Search for similar vectors in the database
        response = self.db_client.search(
            collection_name="vectors",
            query_vector=query_vector,
            limit=limit
        )
        return response["result"]