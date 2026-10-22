from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.schemas.validation import NonBlank


class LearningTrackBase(BaseModel):
    name: str
    description: Optional[str] = None


class LearningTrackCreate(
    LearningTrackBase
):
    name: NonBlank


class LearningTrackUpdate(BaseModel):
    name: NonBlank = None
    description: Optional[str] = None


class LearningTrackResponse(
    LearningTrackBase
):
    id: int
    user_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }