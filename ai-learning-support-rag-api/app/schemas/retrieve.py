from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    text: str = Field(..., description="The retrieved document chunk text")
    score: float = Field(..., description="Similarity score from Qdrant")
    doc_id: str = Field(..., description="Saved document identifier")
    page_no: int = Field(..., description="Source PDF page number")
    week: int = Field(..., description="Course week number")
    image_url: str | None = Field(default=None, description="Optional local image URL for extracted PDF images")


class RetrieveResponse(BaseModel):
    results: list[RetrievedChunk]


class RetrieveRequest(BaseModel):
    course_id: str
    query: str