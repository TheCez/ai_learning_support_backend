from pydantic import BaseModel, Field
from typing import List


class AskRequest(BaseModel):
    course_id: str
    query: str


class AskResponse(BaseModel):
    answer: str
    images: List[str] = Field(default_factory=list)


class AnswerPayload(BaseModel):
    answer: str


class ImageSelectionPayload(BaseModel):
    selected_image_ids: List[str] = Field(default_factory=list)


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