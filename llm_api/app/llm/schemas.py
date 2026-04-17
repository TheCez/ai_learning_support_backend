import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    course_id: str
    query: str
    persona: str = "standard"
    user_name: str | None = None


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


class BaseLearningRequest(BaseModel):
    course_id: str
    level: str | None = None
    student_context: str | None = None


class FlashcardsRequest(BaseLearningRequest):
    num_cards: int = Field(default=5, ge=1, le=20)


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardsResponse(BaseModel):
    flashcards: List[Flashcard] = Field(default_factory=list)


class LibrarySummaryRequest(BaseLearningRequest):
    pass


class LibrarySummaryResponse(BaseModel):
    summary: str


class LibraryCard(BaseModel):
    topic: str
    simple_text: str
    technical_text: str


class LibraryCardsRequest(BaseLearningRequest):
    pass


class LibraryCardsResponse(BaseModel):
    cards: List[LibraryCard] = Field(default_factory=list)


class AnswerPayload(BaseModel):
    answer: str


class ImageSelectionPayload(BaseModel):
    selected_image_ids: List[str] = Field(default_factory=list)


class QuizPayload(BaseModel):
    quiz: List[QuizQuestion] = Field(default_factory=list)


class FlashcardsPayload(BaseModel):
    flashcards: List[Flashcard] = Field(default_factory=list)


class LibrarySummaryPayload(BaseModel):
    summary: str


class LibraryCardsPayload(BaseModel):
    cards: List[LibraryCard] = Field(default_factory=list)


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
    source_page: Optional[int] = Field(
        default=None,
        description="The integer page number where the info was found. If unknown, missing, or multiple pages apply, you MUST return null.",
    )

    @field_validator("source_page", mode="before")
    @classmethod
    def normalize_source_page(cls, value):
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value if value > 0 else None

        if isinstance(value, float):
            normalized = int(value)
            return normalized if normalized > 0 else None

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"", "none", "null", "n/a", "unknown"}:
                return None

            match = re.search(r"\d+", normalized)
            if not match:
                return None

            parsed = int(match.group(0))
            return parsed if parsed > 0 else None

        return None


class PresentationRequest(BaseModel):
    course_id: str
    query: str
    persona: str = "standard"
    user_name: str | None = None


class PresentationResponse(BaseModel):
    slides: List[Slide] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)


class SlidePayload(BaseModel):
    slides: List[Slide] = Field(default_factory=list)