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


def build_answer_messages(question: str, results: list[dict[str, Any]], persona: str = "standard"):
    context = build_context(results)

    normalized_persona = (persona or "standard").strip().lower()
    if normalized_persona == "ki_professor":
        system_prompt = (
            "You are Prof. Wagner. Explain the core concepts accurately but concisely. "
            "Keep your spoken response conversational, engaging, and under 3 short paragraphs. "
            "Do not overwhelm the student with too much text at once. "
            "You are speaking directly to a student. "
            "Use the provided context as your foundation, but if the context is brief, "
            "you are allowed to be lenient and supplement the answer with your general medical/nursing knowledge. "
            "Do NOT mention 'pages', 'documents', 'uploaded material', or 'diagrams'. "
            "Do not tell the student where to look. "
            "You are a knowledgeable nursing professor. Synthesize the provided context and explain the actual concepts clearly. "
            "If the context mentions heart chambers, explain what the heart chambers are and how they work based on the text. "
            "Speak directly to the student naturally and comprehensively, while staying concise."
        )
    else:
        system_prompt = (
            "You are an AI study-support assistant for nursing students. "
            "Use only the retrieved study material provided. "
            "Do not mention retrieval scores or raw chunks. "
            "Write a concise, student-friendly answer. "
            "If the context is insufficient, say exactly: "
            "'This was not found in the uploaded material.'"
        )

    if normalized_persona == "ki_professor":
        instructions_block = """
Instructions:
- Explain the concepts directly to the student in a natural professor voice.
- Prioritize conceptual understanding and mechanisms, not source-location references.
- Keep the response concise and under 3 short paragraphs.
- Do NOT mention pages, documents, uploaded material, or diagrams.
- Do NOT tell the student where to look.
- Return strict JSON with exactly one key: answer.
"""
    else:
        instructions_block = """
Instructions:
- Answer clearly and naturally in 1-3 sentences.
- Use only the retrieved material above.
- Mention page references when they are useful.
- Return strict JSON with exactly one key: answer.
- Do not include markdown bullets unless they are necessary for clarity.
"""

    user_prompt = f"""
Question:
{question}

Retrieved Study Material:
{context}

{instructions_block}
"""

    return system_prompt, user_prompt


def build_image_selection_messages(question: str, answer: str, candidates: list[dict[str, Any]]):
    image_candidates = build_image_candidates(candidates)

    system_prompt = (
        "You are selecting the most relevant source images for a nursing student answer. "
        "Choose only images that directly support the answer. "
        "Prefer fewer images over unrelated ones. "
        "If no image is clearly useful, return an empty list. "
        "Under NO circumstances may you invent, generate, or hallucinate image URLs. "
        "You may ONLY select image URLs explicitly provided to you in the retrieved context. "
        "If there are no relevant images in the context, you MUST return an empty array []."
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
- Under NO circumstances may you invent, generate, or hallucinate image URLs.
- You may ONLY select from the exact candidate IDs shown above.
- Return strict JSON with exactly one key: selected_image_ids.
- selected_image_ids must be a list of candidate IDs like img_1, img_2.
- If no image is clearly relevant, return an empty list.
"""

    return system_prompt, user_prompt


def build_quiz_messages(context: str, question_count: int = 10):
    system_prompt = (
        "You are an AI nursing educator generating quiz questions from study material. "
        "Use only the provided context. "
        "Generate high-quality MCQs that test factual understanding, not trivia."
    )

    user_prompt = f"""
Study Material Context:
{context}

Instructions:
- Create exactly {question_count} multiple-choice questions.
- Each question must have exactly 4 options.
- Provide answer_index as an integer from 0 to 3.
- Include a short explanation (1 sentence) for why the correct option is right.
- Keep questions clear and student-friendly.
- Avoid duplicate questions.
- Return strict JSON with exactly one key: quiz.
- quiz must be an array of objects with keys: question, options, answer_index, explanation.
"""

    return system_prompt, user_prompt


def build_quiz_completion_messages(context: str, existing_questions: list[str], missing_count: int):
    existing_block = "\n".join(f"- {question}" for question in existing_questions) or "None"

    system_prompt = (
        "You are an AI nursing educator generating additional non-duplicate MCQs from study material. "
        "Use only provided context and avoid repeating existing questions."
    )

    user_prompt = f"""
Study Material Context:
{context}

Existing Questions (DO NOT REPEAT):
{existing_block}

Instructions:
- Generate exactly {missing_count} additional multiple-choice questions.
- Each question must have exactly 4 options.
- Provide answer_index as an integer from 0 to 3.
- Include a short explanation (1 sentence).
- Do not repeat or paraphrase existing questions.
- Return strict JSON with exactly one key: quiz.
- quiz must be an array of objects with keys: question, options, answer_index, explanation.
"""

    return system_prompt, user_prompt


def build_slide_summarization_messages(spoken_text: str, image_urls: list[str], persona: str = "standard"):
    normalized_persona = (persona or "standard").strip().lower()
    image_context = "\n".join(f"- {url}" for url in image_urls) if image_urls else "None"

    if normalized_persona == "ki_professor":
        system_prompt = (
            "You are an expert presentation designer. "
            "Break the professor's lecture down into a logical sequence of 2 to 4 presentation slides. "
            "Each slide must have a title, an array of 3-5 concise bullet fragments (NOT full sentences), and an image_url. "
            "CRITICAL CONSTRAINT: bullet fragments must be maximum 7 words each. "
            "Example: Use 'Four muscular chambers' instead of full-sentence bullets. "
            "Do NOT mention 'pages', 'documents', 'uploaded material', or 'diagrams'. "
            "Do not tell the student where to look. "
            "Use only the provided image URL candidates; if none fit a specific slide, set image_url to null."
        )
    else:
        system_prompt = (
            "You are an expert presentation designer and educator. "
            "Your task is to convert a detailed lecture transcript into a concise, visually-friendly multi-slide presentation. "
            "Extract core concepts and present them as clear, memorable bullet points."
        )

    user_prompt = f"""
Lecture Transcript:
{spoken_text}

Available Image URL Candidates (use only these exact values):
{image_context}

Instructions:
- Break the lecture into a logical sequence of 2 to 4 slides.
- Each slide must have: title, bullets, image_url.
- title should be clear and concise (3-10 words).
- bullets must contain 3 to 5 items per slide.
- Each bullet must be a concise fragment, not a full sentence.
- Each bullet must be 4 to 7 words only.
- Prioritize key facts and clinical relevance.
- Use simple, student-friendly language.
- Do NOT mention pages, documents, uploaded material, or diagrams.
- Do NOT tell the student where to look.
- image_url must be either one provided candidate URL or null.
- Return strict JSON with exactly one key: slides.
- slides must be an array of objects with keys: title, bullets, image_url.
"""

    return system_prompt, user_prompt