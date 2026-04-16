from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.llm.schemas import AskRequest, AskResponse
from app.llm.llm_service import generate_answer

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
    return generate_answer(course_id=data.course_id, query=data.query)