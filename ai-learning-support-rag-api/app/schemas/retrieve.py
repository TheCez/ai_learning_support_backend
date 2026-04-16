from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    text: str = Field(..., description="The retrieved document chunk text")
    score: float = Field(..., description="Similarity score from Qdrant")
    doc_id: str = Field(..., description="Saved document identifier")
    page_no: int = Field(..., description="Source PDF page number")
    week: int = Field(..., description="Course week number")


class RetrieveResponse(BaseModel):
    results: list[RetrievedChunk]


class RetrieveRequest(BaseModel):
    course_id: str
    query: str