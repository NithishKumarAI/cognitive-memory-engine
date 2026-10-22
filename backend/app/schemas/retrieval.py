from app.schemas.validation import NonBlank
from typing import Annotated
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: Annotated[NonBlank, Field(max_length=2000)]

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