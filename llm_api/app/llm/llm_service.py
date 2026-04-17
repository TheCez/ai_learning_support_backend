# This file bridges the public ask-the-AI flow to the RAG API and
# the OpenAI-compatible university API.

import os
import json
import logging
import re
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from .schemas import (
    AnswerPayload,
    AskResponse,
    ImageSelectionPayload,
    QuizPayload,
    QuizQuestion,
    QuizResponse,
    PresentationRequest,
    PresentationResponse,
    Slide,
    SlidePayload,
)
from .prompt_builder import (
    build_answer_messages,
    build_image_selection_messages,
    build_quiz_completion_messages,
    build_quiz_messages,
    build_slide_summarization_messages,
)

# Load environment variables from the .env file.
load_dotenv()

# Read API settings from environment.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
RAG_API_BASE_URL = os.getenv("RAG_API_BASE_URL", "http://rag_api:8000/api/v1")

# Create OpenAI-compatible client using university base URL.
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
logger = logging.getLogger(__name__)


def _is_allowed_image_url(url: str) -> bool:
    return url.startswith("/api/v1/images/")


def _sanitize_image_urls(urls: list[str]) -> list[str]:
    sanitized: list[str] = []
    for url in urls:
        value = str(url or "").strip()
        if not value or not _is_allowed_image_url(value):
            continue
        if value not in sanitized:
            sanitized.append(value)
    return sanitized


def fetch_retrieval_results(course_id: str, query: str, limit: int = 5) -> list[dict[str, object]]:
    retrieve_url = f"{RAG_API_BASE_URL.rstrip('/')}/courses/{quote(course_id, safe='')}/retrieve"

    with httpx.Client(timeout=30.0) as http_client:
        response = http_client.get(retrieve_url, params={"query": query, "limit": limit})
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
        if not image_url or not _is_allowed_image_url(image_url):
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


def _parse_quiz_payload(content: str) -> QuizPayload:
    payload = json.loads(content)
    return QuizPayload.model_validate(payload)


def _normalize_quiz_questions(questions: list[QuizQuestion]) -> list[QuizQuestion]:
    normalized: list[QuizQuestion] = []
    seen: set[str] = set()

    for question in questions:
        question_text = question.question.strip()
        if not question_text:
            continue

        dedupe_key = re.sub(r"\s+", " ", question_text.lower())
        if dedupe_key in seen:
            continue

        options = [str(option).strip() for option in question.options if str(option).strip()]
        if len(options) != 4:
            continue

        if question.answer_index < 0 or question.answer_index > 3:
            continue

        explanation = question.explanation.strip() or "Based on the uploaded study material."

        seen.add(dedupe_key)
        normalized.append(
            QuizQuestion(
                question=question_text,
                options=options,
                answer_index=int(question.answer_index),
                explanation=explanation,
            )
        )

    return normalized


def _build_quiz_context(results: list[dict[str, object]], max_chunks: int = 24, max_chars: int = 14000) -> str:
    lines: list[str] = []
    total_chars = 0

    for chunk in results[:max_chunks]:
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue

        page_no = chunk.get("page_no")
        prefix = f"[Page {page_no}] " if page_no is not None else ""
        line = f"{prefix}{text}"

        if total_chars + len(line) > max_chars:
            break

        lines.append(line)
        total_chars += len(line)

    return "\n\n".join(lines)


def _fetch_quiz_results(course_id: str) -> list[dict[str, object]]:
    seed_queries = [
        "key concepts",
        "important definitions",
        "core topics",
        "clinical concepts",
        "summary of material",
    ]

    merged: list[dict[str, object]] = []
    seen: set[str] = set()

    for seed_query in seed_queries:
        try:
            batch = fetch_retrieval_results(course_id=course_id, query=seed_query, limit=8)
        except Exception:
            continue

        for item in batch:
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            dedupe_key = "|".join(
                [
                    str(item.get("doc_id") or ""),
                    str(item.get("page_no") or ""),
                    text[:240],
                ]
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged.append(item)

    merged.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
    return merged


def generate_answer(course_id: str, query: str, persona: str = "standard") -> AskResponse:
    try:
        results = fetch_retrieval_results(course_id=course_id, query=query)
        if not results:
            return AskResponse(answer="This was not found in the uploaded material.", images=[])

        answer_system_prompt, answer_user_prompt = build_answer_messages(
            question=query,
            results=results,
            persona=persona,
        )

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

        return AskResponse(answer=answer_text, images=_sanitize_image_urls(selected_images))

    except Exception as e:
        return AskResponse(answer=f"Unexpected error: {type(e).__name__}: {str(e)}", images=[])


def generate_quiz(course_id: str) -> QuizResponse:
    try:
        results = _fetch_quiz_results(course_id=course_id)
        if not results:
            return QuizResponse(quiz=[])

        context = _build_quiz_context(results)
        if not context:
            return QuizResponse(quiz=[])

        system_prompt, user_prompt = build_quiz_messages(context=context, question_count=10)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = (
            response.choices[0].message.content.strip()
            if response.choices and response.choices[0].message.content
            else ""
        )
        if not content:
            return QuizResponse(quiz=[])

        payload = _parse_quiz_payload(content)
        questions = _normalize_quiz_questions(payload.quiz)

        if len(questions) < 10:
            missing = 10 - len(questions)
            existing_questions = [question.question for question in questions]
            complete_system_prompt, complete_user_prompt = build_quiz_completion_messages(
                context=context,
                existing_questions=existing_questions,
                missing_count=missing,
            )

            completion_response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": complete_system_prompt},
                    {"role": "user", "content": complete_user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            completion_content = (
                completion_response.choices[0].message.content.strip()
                if completion_response.choices and completion_response.choices[0].message.content
                else ""
            )

            if completion_content:
                completion_payload = _parse_quiz_payload(completion_content)
                combined = _normalize_quiz_questions([*questions, *completion_payload.quiz])
                questions = combined

        return QuizResponse(quiz=questions[:10])

    except Exception:
        return QuizResponse(quiz=[])


def _parse_slide_payload(content: str) -> SlidePayload:
    payload = json.loads(content)
    return SlidePayload.model_validate(payload)


def _build_fallback_slide(spoken_text: str, results: list[dict[str, object]]) -> Slide:
    summary_text = str(spoken_text or "").strip()
    short_text = summary_text[:280].strip()
    if summary_text and len(summary_text) > 280:
        short_text = f"{short_text}..."

    source_page: int | None = None
    first_page = results[0].get("page_no") if results else None
    try:
        if first_page is not None:
            normalized = int(first_page)
            source_page = normalized if normalized > 0 else None
    except (TypeError, ValueError):
        source_page = None

    return Slide(
        title="Key Concepts Overview",
        bullets=["Core points from study material"],
        image_url=None,
        spoken_text=short_text or "Key concepts are summarized from the available context.",
        source_page=source_page,
    )


def generate_presentation(course_id: str, query: str, persona: str = "standard") -> PresentationResponse:
    """
    Generate a presentation deck where each slide contains its own narration.
    
    Flow:
    1. Fetch retrieval results for the query.
    2. Generate a complete answer to establish context.
    3. Pass the answer to slide generation with per-slide narration.
    4. Each slide includes title, bullets, image_url, and spoken_text.
    """
    try:
        # Step 1: Fetch reliable context
        results = fetch_retrieval_results(course_id=course_id, query=query)
        if not results:
            return PresentationResponse(slides=[], images=[])

        # Step 2: Generate a complete answer to establish narrative flow
        answer_response = generate_answer(course_id=course_id, query=query, persona=persona)
        spoken_text = answer_response.answer
        images = _sanitize_image_urls(answer_response.images)

        # Step 3: If no meaningful content, return empty presentation
        if spoken_text == "This was not found in the uploaded material.":
            return PresentationResponse(slides=[], images=[])

        # Step 4: Generate slides with per-slide narration
        slide_system_prompt, slide_user_prompt = build_slide_summarization_messages(
            spoken_text=spoken_text,
            image_urls=images,
            context_chunks=results,
            persona=persona,
        )

        slide_response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": slide_system_prompt},
                {"role": "user", "content": slide_user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        slide_content = (
            slide_response.choices[0].message.content.strip()
            if slide_response.choices and slide_response.choices[0].message.content
            else ""
        )

        if not slide_content:
            return PresentationResponse(slides=[], images=images)

        # Step 5: Parse and sanitize slides with per-slide narration
        try:
            slide_payload = _parse_slide_payload(slide_content)
            candidate_slides = slide_payload.slides
        except Exception:
            logger.exception("Slide payload validation failed. Raw content: %s", slide_content)
            raw_payload = json.loads(slide_content)
            raw_slides = raw_payload.get("slides", []) if isinstance(raw_payload, dict) else []
            candidate_slides = []
            for raw_slide in raw_slides[:4]:
                if not isinstance(raw_slide, dict):
                    continue
                candidate_slides.append(
                    Slide(
                        title=str(raw_slide.get("title") or "Summary"),
                        bullets=[str(item).strip() for item in (raw_slide.get("bullets") or []) if str(item).strip()],
                        image_url=raw_slide.get("image_url"),
                        spoken_text=str(raw_slide.get("spoken_text") or "").strip(),
                        source_page=raw_slide.get("source_page"),
                    )
                )

        sanitized_slides: list[Slide] = []
        for raw_slide in candidate_slides[:4]:
            title = str(raw_slide.title or "").strip() or "Summary"
            bullets = [str(bullet).strip() for bullet in raw_slide.bullets if str(bullet).strip()]
            image_url = str(raw_slide.image_url or "").strip() if raw_slide.image_url else None
            if image_url and not _is_allowed_image_url(image_url):
                image_url = None
            spoken_text_slide = str(raw_slide.spoken_text or "").strip() if hasattr(raw_slide, 'spoken_text') else ""
            source_page: int | None = None
            if hasattr(raw_slide, "source_page") and raw_slide.source_page is not None:
                try:
                    source_page_value = int(raw_slide.source_page)
                    source_page = source_page_value if source_page_value > 0 else None
                except (TypeError, ValueError):
                    source_page = None

            sanitized_slides.append(
                Slide(
                    title=title,
                    bullets=bullets[:5],
                    image_url=image_url,
                    spoken_text=spoken_text_slide,
                    source_page=source_page,
                )
            )

        if not sanitized_slides:
            sanitized_slides = [_build_fallback_slide(spoken_text=spoken_text, results=results)]

        return PresentationResponse(slides=sanitized_slides, images=images)

    except Exception:
        logger.exception("generate_presentation failed")
        return PresentationResponse(slides=[], images=[])