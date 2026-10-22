from pydantic import BaseModel
from app.schemas.validation import NonBlank
from typing import Optional


class MemoryCreate(BaseModel):
    title: NonBlank
    content: NonBlank
    category: str
    study_log_id: Optional[int] = None


class MemoryUpdate(BaseModel):
    title: NonBlank = None
    content: NonBlank = None
    category: str = None
    study_log_id: Optional[int] = None


class MemoryResponse(BaseModel):
    id: int
    user_id: int
    study_log_id: Optional[int]
    title: str
    content: str
    category: str

    class Config:
        from_attributes = True