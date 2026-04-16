import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    raw_pdf_storage_path: str = Field(
        default_factory=lambda: os.path.join(os.getcwd(), "data", "raw_pdfs")
    )
    extracted_image_storage_path: str = Field(
        default_factory=lambda: os.path.join(os.getcwd(), "data", "extracted_images")
    )
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "course_materials"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    vision_api_url: str = ""
    vision_api_key: str = ""
    vision_model: str = "gpt-4o-mini"

    @field_validator("qdrant_api_key", mode="before")
    @classmethod
    def empty_qdrant_key_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


settings = Settings()
