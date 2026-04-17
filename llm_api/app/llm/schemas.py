from pydantic import BaseModel, Field
from typing import List


class AskRequest(BaseModel):
    course_id: str
    query: str
    persona: str = "standard"


class AskResponse(BaseModel):
    answer: str
    images: List[str] = Field(default_factory=list)


class QuizRequest(BaseModel):
    course_id: str


class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(default_factory=list)
    answer_index: int
    explanation: str


class QuizResponse(BaseModel):
    quiz: List[QuizQuestion] = Field(default_factory=list)


class AnswerPayload(BaseModel):
    answer: str


class ImageSelectionPayload(BaseModel):
    selected_image_ids: List[str] = Field(default_factory=list)


class QuizPayload(BaseModel):
    quiz: List[QuizQuestion] = Field(default_factory=list)


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


class Slide(BaseModel):
    title: str
    bullets: List[str] = Field(default_factory=list)
    image_url: str | None = None
    spoken_text: str = ""  # Narration specific to this slide


class PresentationRequest(BaseModel):
    course_id: str
    query: str
    persona: str = "standard"


class PresentationResponse(BaseModel):
    slides: List[Slide] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)


class SlidePayload(BaseModel):
    slides: List[Slide] = Field(default_factory=list)