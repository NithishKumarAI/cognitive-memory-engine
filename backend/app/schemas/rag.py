from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    question: str

    top_k: int = Field(
        default=5,
        ge=1,
        le=20
    )


class RAGSourceMemory(BaseModel):
    memory_id: int
    title: str
    category: str
    distance: float


class RAGResponse(BaseModel):
    answer: str

    sources: list[RAGSourceMemory]