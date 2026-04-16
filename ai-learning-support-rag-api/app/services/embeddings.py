from typing import List, Dict
import numpy as np

class EmbeddingService:
    def __init__(self, model):
        self.model = model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = self.model.encode(text)  # Assuming the model has an encode method
            embeddings.append(embedding.tolist())
        return embeddings

    def attach_metadata(self, embeddings: List[List[float]], course_id: str, group_id: str, page_id: int, week: int) -> List[Dict]:
        metadata_embeddings = []
        for embedding in embeddings:
            metadata = {
                "embedding": embedding,
                "course_id": course_id,
                "group_id": group_id,
                "page_id": page_id,
                "week": week
            }
            metadata_embeddings.append(metadata)
        return metadata_embeddings