# This file builds prompts for the study-support agent.
# It formats validated PDF chunks into context and creates
# task-specific instructions for Gemini.

from typing import List
from .schemas import ValidatedChunk


def build_context(chunks: List[ValidatedChunk]) -> str:
    # Convert validated chunks into a readable context block
    # with page numbers and retrieval scores.
    parts = []
    for chunk in chunks:
        parts.append(f"[Page {chunk.page} | Score {chunk.score}] {chunk.text}")
    return "\n\n".join(parts)


def build_messages(task: str, question: str, chunks: List[ValidatedChunk], retrieval_status: str):
    # Build a context string from the validated chunks.
    context = build_context(chunks)

    # System prompt defines the role and safety behavior.
    system_prompt = (
        "You are an AI study-support assistant for nursing students. "
        "Use only the validated study material provided. "
        "Do not invent facts. "
        "If the context is insufficient, say: "
        "'This was not found in the uploaded material.'"
    )

    # Add task-specific instruction based on agent routing.
    if task == "summary":
        instruction = (
            "Summarize the topic clearly for a nursing student. "
            "Use short and simple points."
        )
    elif task == "quiz":
        instruction = (
            "Create 5 quiz questions based only on the context. "
            "Include answers."
        )
    else:
        instruction = (
            "Answer the student's question clearly and simply using only the context."
        )

    # User prompt contains the task, question, retrieval state, and context.
    user_prompt = f"""
Task:
{task}

Question:
{question}

Retrieval status:
{retrieval_status}

Validated Study Material Context:
{context}

Instructions:
- Use only the validated context above.
- {instruction}
- Mention relevant page numbers when possible.
- If the answer is missing from context, clearly say so.
"""

    return system_prompt, user_prompt