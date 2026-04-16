# This file bridges the public ask-the-AI flow to the RAG API and
# the OpenAI-compatible university API.

import os
import json
import re
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from .schemas import AnswerPayload, AskResponse, ImageSelectionPayload
from .prompt_builder import build_answer_messages, build_image_selection_messages

# Load environment variables from the .env file.
load_dotenv()

# Read API settings from environment.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
RAG_API_BASE_URL = os.getenv("RAG_API_BASE_URL", "http://rag_api:8000/api/v1")

# Create OpenAI-compatible client using university base URL.
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


def fetch_retrieval_results(course_id: str, query: str) -> list[dict[str, object]]:
    retrieve_url = f"{RAG_API_BASE_URL.rstrip('/')}/courses/{quote(course_id, safe='')}/retrieve"

    with httpx.Client(timeout=30.0) as http_client:
        response = http_client.get(retrieve_url, params={"query": query})
        response.raise_for_status()

    payload = response.json()
    results = payload.get("results", [])
    return results if isinstance(results, list) else []


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "how", "in",
    "into", "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was", "what",
    "when", "where", "which", "who", "why", "with", "does", "do", "did", "than", "then", "also",
    "but", "about", "your", "you", "we", "they", "those", "these",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}


def _extract_image_candidates(results: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []

    for index, chunk in enumerate(results, start=1):
        image_url = str(chunk.get("image_url") or "").strip()
        if not image_url:
            continue

        candidate = {
            "id": f"img_{index}",
            "url": image_url,
            "text": str(chunk.get("text") or "").strip(),
            "page_no": chunk.get("page_no"),
        }
        candidates.append(candidate)

    return candidates


def _score_candidate(question: str, answer: str, candidate: dict[str, object]) -> int:
    question_terms = _tokenize(question)
    answer_terms = _tokenize(answer)
    candidate_text = f"{candidate.get('text', '')} {candidate.get('page_no', '')}"
    candidate_terms = _tokenize(candidate_text)

    overlap = len((question_terms | answer_terms) & candidate_terms)
    bonus_terms = {
        "heart",
        "chamber",
        "chambers",
        "atrium",
        "atria",
        "ventricle",
        "ventricles",
        "septum",
        "interior",
        "structure",
        "left",
        "right",
    }
    bonus = len(candidate_terms & bonus_terms)
    score = overlap * 2 + bonus * 3

    text = str(candidate.get("text") or "").lower()
    if "chamber" in text or "atrium" in text or "ventricle" in text:
        score += 4
    if "blood vessel" in text or "blood vessels" in text:
        score += 1

    return score


def _rank_image_candidates(question: str, answer: str, results: list[dict[str, object]], limit: int = 4) -> list[dict[str, object]]:
    candidates = _extract_image_candidates(results)
    if not candidates:
        return []

    scored_candidates = [
        (candidate, _score_candidate(question, answer, candidate))
        for candidate in candidates
    ]
    scored_candidates.sort(key=lambda item: (-item[1], str(item[0].get("page_no") or ""), str(item[0]["id"])))
    return [candidate for candidate, score in scored_candidates[:limit] if score > 0] or [candidate for candidate, _ in scored_candidates[:limit]]


def _parse_answer_payload(content: str) -> AnswerPayload:
    payload = json.loads(content)
    return AnswerPayload.model_validate(payload)


def _parse_image_selection(content: str) -> ImageSelectionPayload:
    payload = json.loads(content)
    return ImageSelectionPayload.model_validate(payload)


def generate_answer(course_id: str, query: str) -> AskResponse:
    try:
        results = fetch_retrieval_results(course_id=course_id, query=query)
        if not results:
            return AskResponse(answer="This was not found in the uploaded material.", images=[])

        answer_system_prompt, answer_user_prompt = build_answer_messages(question=query, results=results)

        answer_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": answer_system_prompt},
                {"role": "user", "content": answer_user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw_content = (
            answer_response.choices[0].message.content.strip()
            if answer_response.choices and answer_response.choices[0].message.content
            else ""
        )

        if not raw_content:
            return AskResponse(answer="No response generated.", images=[])

        model_answer = _parse_answer_payload(raw_content)
        answer_text = model_answer.answer.strip() or "No response generated."
        if answer_text == "This was not found in the uploaded material.":
            return AskResponse(answer=answer_text, images=[])

        ranked_candidates = _rank_image_candidates(query, answer_text, results)
        if not ranked_candidates:
            return AskResponse(answer=answer_text, images=[])

        selection_system_prompt, selection_user_prompt = build_image_selection_messages(
            question=query,
            answer=answer_text,
            candidates=ranked_candidates,
        )

        selection_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": selection_system_prompt},
                {"role": "user", "content": selection_user_prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        selection_content = (
            selection_response.choices[0].message.content.strip()
            if selection_response.choices and selection_response.choices[0].message.content
            else ""
        )

        selected_images: list[str] = []
        candidate_by_id = {str(candidate["id"]): str(candidate["url"]) for candidate in ranked_candidates}

        if selection_content:
            selection_payload = _parse_image_selection(selection_content)
            for image_id in selection_payload.selected_image_ids[:2]:
                normalized_id = str(image_id).strip()
                image_url = candidate_by_id.get(normalized_id)
                if image_url and image_url not in selected_images:
                    selected_images.append(image_url)

        if not selected_images:
            selected_images = [str(candidate["url"]) for candidate in ranked_candidates[:1]]

        return AskResponse(answer=answer_text, images=selected_images)

    except Exception as e:
        return AskResponse(answer=f"Unexpected error: {type(e).__name__}: {str(e)}", images=[])