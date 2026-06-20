from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str

    limit: int = Field(
        default=5,
        ge=1,
        le=20
    )


class SemanticSearchResult(BaseModel):
    memory_id: int
    title: str
    category: str
    distance: float