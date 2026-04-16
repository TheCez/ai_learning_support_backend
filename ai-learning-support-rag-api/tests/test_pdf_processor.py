import base64

import fitz

import app.services.pdf_processor as pdf_processor


# 1x1 transparent PNG.
_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7+0X8AAAAASUVORK5CYII="
)


def _make_pdf_with_text_and_image(output_path: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Image content below")
    page.insert_image(fitz.Rect(72, 100, 132, 160), stream=_PNG_BYTES)
    doc.save(output_path)
    doc.close()


def test_extract_page_chunks_includes_image_caption_and_url(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    image_root = tmp_path / "extracted_images"
    _make_pdf_with_text_and_image(str(pdf_path))

    monkeypatch.setattr(pdf_processor.settings, "extracted_image_storage_path", str(image_root))
    monkeypatch.setattr(pdf_processor, "generate_image_caption", lambda _: "A small transparent marker image")

    chunks = pdf_processor.extract_page_chunks(str(pdf_path), doc_id="doc-test.pdf")

    text_chunks = [chunk for chunk in chunks if chunk.get("kind") == "text"]
    image_chunks = [chunk for chunk in chunks if chunk.get("kind") == "image"]

    assert text_chunks
    assert image_chunks

    image_chunk = image_chunks[0]
    assert image_chunk["text"].startswith("A small transparent marker image")
    assert image_chunk["page_no"] == 1
    assert image_chunk["image_url"].startswith("/api/v1/images/doc-test.pdf/page-1/page-render-")

    text_chunk = text_chunks[0]
    assert text_chunk["image_url"].startswith("/api/v1/images/doc-test.pdf/page-1/page-render-")

    relative_path = image_chunk["image_url"].replace("/api/v1/images/", "", 1)
    stored_image_path = image_root / relative_path
    assert stored_image_path.exists()
