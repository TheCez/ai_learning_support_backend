from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    course_id: str = Field(..., description="The ID of the course")
    week: int = Field(..., description="The week number of the course")
    doc_id: str = Field(..., description="The saved document identifier")


class UploadResponse(BaseModel):
    message: str
    metadata: dict