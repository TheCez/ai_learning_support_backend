from base64 import b64encode
from pathlib import Path

from openai import OpenAI

from app.core.config import settings


def _build_client() -> OpenAI | None:
    if not settings.vision_api_url or not settings.vision_api_key:
        return None

    return OpenAI(api_key=settings.vision_api_key, base_url=settings.vision_api_url)


def generate_image_caption(image_path: str) -> str:
    client = _build_client()
    if client is None:
        return f"Image extracted from PDF: {Path(image_path).name}"

    try:
        image_bytes = Path(image_path).read_bytes()
        image_b64 = b64encode(image_bytes).decode("utf-8")
        mime_type = "image/png"
        suffix = Path(image_path).suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            mime_type = "image/jpeg"
        elif suffix == ".webp":
            mime_type = "image/webp"
        response = client.chat.completions.create(
            model=settings.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image for retrieval indexing in one concise sentence."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                        },
                    ],
                }
            ],
            max_tokens=120,
        )
        caption = response.choices[0].message.content or ""
        return caption.strip() or f"Image extracted from PDF: {Path(image_path).name}"
    except Exception:
        return f"Image extracted from PDF: {Path(image_path).name}"
