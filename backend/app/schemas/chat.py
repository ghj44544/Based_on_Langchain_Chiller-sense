from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    diagnosis_id: int = Field(..., ge=1)
    question: str = Field(..., min_length=1)


class ChatResponseData(BaseModel):
    answer: str

