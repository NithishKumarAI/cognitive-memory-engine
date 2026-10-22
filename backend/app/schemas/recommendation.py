from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    priority: Literal["high", "medium", "low"]
    message: str
    id: str | None = None
    topic: str | None = None
    learning_track_id: int | None = None
    learning_track_name: str | None = None
    action: str | None = None
    reason: str | None = None
    source_capture_id: int | None = None
    source_observation_id: int | None = None
    evidence: str | None = None
    review_due_at: datetime | None = None
    link_url: str | None = None
    status: str | None = None


class RecommendationListResponse(BaseModel):
    recommendations: List[RecommendationResponse]


class DailyRecommendationResponse(BaseModel):
    generated_at: datetime
    recommendations: List[RecommendationResponse]
