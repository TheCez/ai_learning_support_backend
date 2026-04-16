from pydantic import BaseModel


class RetrieveResponse(BaseModel):
    course_id: str
    query: str
    message: str


class RetrieveRequest(BaseModel):
    course_id: str
    query: str