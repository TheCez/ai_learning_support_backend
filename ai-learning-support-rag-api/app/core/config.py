import os

class Settings:
    raw_pdf_storage_path: str = os.getenv(
        "RAW_PDF_STORAGE_PATH",
        os.path.join(os.getcwd(), "data", "raw_pdfs"),
    )
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str | None = os.getenv("QDRANT_API_KEY")
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "course_materials")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")


settings = Settings()