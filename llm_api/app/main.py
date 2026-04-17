from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.llm.schemas import (
    AskRequest,
    AskResponse,
    FlashcardsRequest,
    FlashcardsResponse,
    LibraryCardsRequest,
    LibraryCardsResponse,
    LibrarySummaryRequest,
    LibrarySummaryResponse,
    PresentationRequest,
    PresentationResponse,
    QuizRequest,
    QuizResponse,
)
from app.llm.llm_service import (
    generate_answer,
    generate_flashcards,
    generate_library_cards,
    generate_library_summary,
    generate_presentation,
    generate_quiz,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate_answer", response_model=AskResponse)
def generate_answer_endpoint(data: AskRequest):
    return generate_answer(course_id=data.course_id, query=data.query, persona=data.persona)


@app.post("/generate_quiz", response_model=QuizResponse)
def generate_quiz_endpoint(data: QuizRequest):
    return generate_quiz(course_id=data.course_id)


@app.post("/generate_presentation", response_model=PresentationResponse)
def generate_presentation_endpoint(data: PresentationRequest):
    return generate_presentation(course_id=data.course_id, query=data.query, persona=data.persona)


@app.post("/generate_flashcards", response_model=FlashcardsResponse)
def generate_flashcards_endpoint(data: FlashcardsRequest):
    return generate_flashcards(
        course_id=data.course_id,
        num_cards=data.num_cards,
        level=data.level,
        student_context=data.student_context,
    )


@app.post("/generate_library_summary", response_model=LibrarySummaryResponse)
def generate_library_summary_endpoint(data: LibrarySummaryRequest):
    return generate_library_summary(
        course_id=data.course_id,
        level=data.level,
        student_context=data.student_context,
    )


@app.post("/generate_library_cards", response_model=LibraryCardsResponse)
def generate_library_cards_endpoint(data: LibraryCardsRequest):
    return generate_library_cards(
        course_id=data.course_id,
        level=data.level,
        student_context=data.student_context,
    )