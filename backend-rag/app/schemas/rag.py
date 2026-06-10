from typing import Literal

from pydantic import BaseModel, Field


RetrieverMode = Literal["keyword", "vector", "hybrid"]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    retriever: RetrieverMode | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)
    retriever: RetrieverMode | None = None
    chat_history: list[ChatTurn] = Field(default_factory=list)


class ReindexRequest(BaseModel):
    force: bool = False


class KnowledgeHit(BaseModel):
    source: str
    chunk_id: str
    score: float
    content: str

