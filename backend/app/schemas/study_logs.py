from datetime import datetime

from pydantic import BaseModel, PositiveInt
from app.schemas.validation import NonBlank


class StudyLogCreate(BaseModel):
    topic: NonBlank
    duration_minutes: PositiveInt
    notes: str

    learning_track_id: int | None = None


class StudyLogUpdate(BaseModel):
    topic: NonBlank = None
    duration_minutes: PositiveInt = None
    notes: str = None

    learning_track_id: int | None = None

class StudyLogResponse(BaseModel):
    id: int
    user_id: int

    topic: str
    duration_minutes: int
    notes: str

    learning_track_id: int | None = None

    created_at: datetime

    class Config:
        from_attributes = True