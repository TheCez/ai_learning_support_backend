from typing import Any


def build_context(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for chunk in results:
        text = str(chunk.get("text", "")).strip()
        if not text:
            continue

        page_no = chunk.get("page_no")
        prefix = f"[Page {page_no}] " if page_no is not None else ""
        if chunk.get("image_url"):
            prefix = f"{prefix}[Visual chunk] "

        parts.append(f"{prefix}{text}")

    return "\n\n".join(parts)


def build_image_candidates(candidates: list[dict[str, Any]]) -> str:
    lines: list[str] = []

    for candidate in candidates:
        candidate_id = str(candidate.get("id") or "").strip()
        image_url = str(candidate.get("url") or "").strip()
        if not candidate_id or not image_url:
            continue

        text = str(candidate.get("text", "")).strip()
        page_no = candidate.get("page_no")
        label = f"[{candidate_id}"
        if page_no is not None:
            label += f" | Page {page_no}"
        label += "]"

        if text:
            lines.append(f"{label} {image_url}\nCaption context: {text}")
        else:
            lines.append(f"{label} {image_url}")

    return "\n\n".join(lines)


def build_answer_messages(question: str, results: list[dict[str, Any]]):
    context = build_context(results)

    system_prompt = (
        "You are an AI study-support assistant for nursing students. "
        "Use only the retrieved study material provided. "
        "Do not mention retrieval scores or raw chunks. "
        "Write a concise, student-friendly answer. "
        "If the context is insufficient, say exactly: "
        "'This was not found in the uploaded material.'"
    )

    user_prompt = f"""
Question:
{question}

Retrieved Study Material:
{context}

Instructions:
- Answer clearly and naturally in 1-3 sentences.
- Use only the retrieved material above.
- Mention page references when they are useful.
- Return strict JSON with exactly one key: answer.
- Do not include markdown bullets unless they are necessary for clarity.
"""

    return system_prompt, user_prompt


def build_image_selection_messages(question: str, answer: str, candidates: list[dict[str, Any]]):
    image_candidates = build_image_candidates(candidates)

    system_prompt = (
        "You are selecting the most relevant source images for a nursing student answer. "
        "Choose only images that directly support the answer. "
        "Prefer fewer images over unrelated ones. "
        "If no image is clearly useful, return an empty list."
    )

    user_prompt = f"""
Question:
{question}

Draft Answer:
{answer}

Relevant Image Candidates:
{image_candidates or 'None'}

Instructions:
- Choose at most 2 image IDs that directly support the answer.
- Prefer the most specific and visually helpful figures.
- Do not pick loosely related overview diagrams if a more specific figure exists.
- Return strict JSON with exactly one key: selected_image_ids.
- selected_image_ids must be a list of candidate IDs like img_1, img_2.
- If no image is clearly relevant, return an empty list.
"""

    return system_prompt, user_prompt