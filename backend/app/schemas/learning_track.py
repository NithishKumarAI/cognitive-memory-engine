from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LearningTrackBase(BaseModel):
    name: str
    description: Optional[str] = None


class LearningTrackCreate(
    LearningTrackBase
):
    pass


class LearningTrackUpdate(BaseModel):
    name: Optional[str] = None
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