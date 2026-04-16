# This file handles the OpenAI-compatible university API call.
# Flow:
# 1. detect task
# 2. build prompt from validated chunks
# 3. call university OpenAI-compatible API
# 4. return grounded answer with source pages

import os
from dotenv import load_dotenv
from openai import OpenAI

from .schemas import LLMRequest, LLMResponse
from .prompt_builder import build_messages
from .agent_service import detect_task

# Load environment variables from the .env file.
load_dotenv()

# Read API settings from environment.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = 'gpt-5.4'

# Create OpenAI-compatible client using university base URL.
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)


def generate_answer(data: LLMRequest) -> LLMResponse:
    # Default task value in case an exception happens early.
    task = "error"

    try:
        # Detect whether the request is for answer, summary, or quiz.
        task = detect_task(data)

        # Safe fallback if retrieval failed or no validated chunks are available.
        if data.retrieval_status.lower() == "insufficient" or not data.validated_chunks:
            return LLMResponse(
                task=task,
                answer="This was not found in the uploaded material.",
                source_pages=[],
            )

        # Build prompts using validated context returned by CRAG / retrieval.
        system_prompt, user_prompt = build_messages(
            task=task,
            question=data.question,
            chunks=data.validated_chunks,
            retrieval_status=data.retrieval_status,
        )

        # Call the OpenAI-compatible chat endpoint.
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        # Extract answer text safely from the first response choice.
        answer = (
            response.choices[0].message.content.strip()
            if response.choices and response.choices[0].message.content
            else "No response generated."
        )

        # Collect unique source page numbers from the validated chunks.
        source_pages = sorted({chunk.page for chunk in data.validated_chunks})

        # Return the final structured response.
        return LLMResponse(
            task=task,
            answer=answer,
            source_pages=source_pages,
        )

    except Exception as e:
        # Return a readable error instead of crashing the API.
        return LLMResponse(
            task=task,
            answer=f"Unexpected error: {type(e).__name__}: {str(e)}",
            source_pages=[],
        )