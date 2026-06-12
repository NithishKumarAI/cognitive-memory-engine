from datetime import datetime

from pydantic import BaseModel


class StudyLogCreate(BaseModel):
    topic: str
    duration_minutes: int
    notes: str


class StudyLogUpdate(BaseModel):
    topic: str | None = None
    duration_minutes: int | None = None
    notes: str | None = None


class StudyLogResponse(BaseModel):
    id: int
    user_id: int

    topic: str
    duration_minutes: int
    notes: str

    created_at: datetime

    class Config:
        from_attributes = True