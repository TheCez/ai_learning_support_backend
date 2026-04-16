from pathlib import Path

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter


_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)


def extract_page_chunks(pdf_path: str) -> list[dict[str, int | str]]:
    chunks: list[dict[str, int | str]] = []

    if not Path(pdf_path).exists():
        return chunks

    with fitz.open(pdf_path) as document:
        for page_no, page in enumerate(document, start=1):
            page_text = page.get_text("text").strip()
            if not page_text:
                continue

            page_chunks = _splitter.split_text(page_text)
            for chunk_index, chunk_text in enumerate(page_chunks):
                if chunk_text.strip():
                    chunks.append(
                        {
                            "text": chunk_text,
                            "page_no": page_no,
                            "chunk_index": chunk_index,
                        }
                    )

    return chunks
