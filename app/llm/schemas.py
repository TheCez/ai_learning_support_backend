from pydantic import BaseModel
from typing import List


class ValidatedChunk(BaseModel):
    chunk_id: str
    page: int
    text: str
    score: float


class LLMRequest(BaseModel):
    document_id: str
    question: str
    validated_chunks: List[ValidatedChunk]
    retrieval_status: str


class LLMResponse(BaseModel):
    task: str
    answer: str
    source_pages: List[int]