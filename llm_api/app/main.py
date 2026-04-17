from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.llm.schemas import AskRequest, AskResponse, QuizRequest, QuizResponse, PresentationRequest, PresentationResponse
from app.llm.llm_service import generate_answer, generate_quiz, generate_presentation

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