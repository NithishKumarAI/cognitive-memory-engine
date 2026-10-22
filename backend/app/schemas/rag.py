from app.schemas.validation import NonBlank
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class RAGRequest(BaseModel):
    question: Annotated[NonBlank, Field(max_length=4000)]
    top_k: int = Field(
        default=5,
        ge=1,
        le=20
    )


class RAGSourceMemory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    memory_id: int | None = None
    observation_id: int | None = None
    capture_id: int | None = None
    source_type: str = "memory"
    title: str
    category: str
    distance: float = 0.0
    evidence: str | None = None


class RAGResponse(BaseModel):
    answer: str
    sources: list[RAGSourceMemory]
