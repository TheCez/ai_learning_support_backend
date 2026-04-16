from pathlib import Path
from uuid import uuid4

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.local_storage import ensure_extracted_image_storage
from app.services.vision_service import generate_image_caption


_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


def _image_extension(image_info: dict[str, object]) -> str:
    ext = str(image_info.get("ext") or "png").lower()
    return ext if ext.startswith(".") else f".{ext}"


def _save_image(document_id: str, page_no: int, image_index: int, image_info: dict[str, object]) -> str:
    ensure_extracted_image_storage()
    image_dir = Path(settings.extracted_image_storage_path) / document_id / f"page-{page_no}"
    image_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"image-{image_index}-{uuid4().hex}{_image_extension(image_info)}"
    image_path = image_dir / file_name
    image_path.write_bytes(image_info["image"])
    return str(image_path)


def _save_page_render(document_id: str, page_no: int, page: fitz.Page) -> str:
    ensure_extracted_image_storage()
    image_dir = Path(settings.extracted_image_storage_path) / document_id / f"page-{page_no}"
    image_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"page-render-{uuid4().hex}.png"
    image_path = image_dir / file_name
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image_path.write_bytes(pix.tobytes("png"))
    return str(image_path)


def extract_page_chunks(pdf_path: str, doc_id: str) -> list[dict[str, int | str]]:
    chunks: list[dict[str, int | str]] = []

    if not Path(pdf_path).exists():
        return chunks

    with fitz.open(pdf_path) as document:
        for page_no, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()
            if not page_text:
                page_chunks: list[str] = []
            else:
                page_chunks = _splitter.split_text(page_text)

            page_images = page.get_images(full=True)
            page_image_urls: list[str] = []
            image_chunks: list[dict[str, int | str]] = []

            page_render_url: str | None = None
            if page_text or page_images:
                rendered_page_path = _save_page_render(doc_id, page_no, page)
                page_render_url = f"/api/v1/images/{Path(rendered_page_path).relative_to(settings.extracted_image_storage_path).as_posix()}"
                page_image_urls.append(page_render_url)

            for image_index, image in enumerate(page_images):
                xref = image[0]
                image_info = document.extract_image(xref)
                if not image_info.get("image"):
                    continue

                image_path = _save_image(doc_id, page_no, image_index, image_info)
                raw_image_url = f"/api/v1/images/{Path(image_path).relative_to(settings.extracted_image_storage_path).as_posix()}"
                image_url = page_render_url or raw_image_url
                if image_url not in page_image_urls:
                    page_image_urls.append(image_url)
                caption = generate_image_caption(image_path)
                caption_text = caption
                if page_text:
                    caption_text = f"{caption}\nPage context: {page_text[:600]}"

                image_chunks.append(
                    {
                        "text": caption_text,
                        "page_no": page_no,
                        "chunk_index": image_index,
                        "kind": "image",
                        "image_url": image_url,
                    }
                )

            page_image_url = page_image_urls[0] if page_image_urls else None

            for chunk_index, chunk_text in enumerate(page_chunks):
                if chunk_text.strip():
                    chunks.append(
                        {
                            "text": chunk_text,
                            "page_no": page_no,
                            "chunk_index": chunk_index,
                            "kind": "text",
                            "image_url": page_image_url,
                        }
                    )

            chunks.extend(image_chunks)

    return chunks
