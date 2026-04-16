from typing import List

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits the input text into chunks of specified size with a given overlap.

    Args:
        text (str): The text to be chunked.
        chunk_size (int): The maximum size of each chunk.
        overlap (int): The number of characters to overlap between chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # Move start to create overlap

    return chunks