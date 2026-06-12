from pydantic import BaseModel
from typing import Optional


class MemoryCreate(BaseModel):
    title: str
    content: str
    category: str
    study_log_id: Optional[int] = None


class MemoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
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