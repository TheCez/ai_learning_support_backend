# This file contains the simple routing logic for the study-support agent.
# It decides whether the student wants:
# - a normal answer
# - a summary
# - a quiz

from .schemas import LLMRequest


def decide_task(question: str) -> str:
    # Use simple keyword routing to keep the agent lightweight
    # and hackathon-friendly.
    q = question.lower()

    # Detect quiz-style requests using more specific keywords
    if "quiz" in q or "mcq" in q or "practice questions" in q:
        return "quiz"

    # Detect summary-style requests
    elif "summarize" in q or "summary" in q:
        return "summary"

    # Default behavior is normal answering
    else:
        return "answer"


def detect_task(data: LLMRequest) -> str:
    # Extract the task from the student's question.
    return decide_task(data.question)