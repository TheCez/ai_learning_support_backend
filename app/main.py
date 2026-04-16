# This file creates the FastAPI app and exposes the API endpoint
# for the study-support agent.

from fastapi import FastAPI
from app.llm.schemas import LLMRequest
from app.llm.llm_service import generate_answer

app = FastAPI()


@app.post("/generate-answer")
def generate_answer_endpoint(data: LLMRequest):
    # Accept student request, send it to the agent,
    # and return the generated response.
    return generate_answer(data)