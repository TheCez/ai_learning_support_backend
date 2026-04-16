from qdrant_client import QdrantClient

class QdrantDB:
    def __init__(self, host: str, port: int, api_key: str):
        self.client = QdrantClient(host=host, port=port, api_key=api_key)

    def create_collection(self, collection_name: str, vector_size: int):
        self.client.recreate_collection(
            collection_name=collection_name,
            vector_size=vector_size,
            distance='Cosine'
        )

    def insert_vector(self, collection_name: str, vector: list, metadata: dict):
        self.client.upsert(
            collection_name=collection_name,
            points=[{
                'id': metadata['page_id'],
                'vector': vector,
                'payload': metadata
            }]
        )

    def search_vector(self, collection_name: str, vector: list, limit: int = 5):
        return self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )