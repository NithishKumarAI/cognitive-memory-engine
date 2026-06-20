from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    type: str
    priority: Literal["high", "medium", "low"]
    message: str


class RecommendationListResponse(BaseModel):
    recommendations: List[RecommendationResponse]


class DailyRecommendationResponse(BaseModel):
    generated_at: datetime
    recommendations: List[RecommendationResponse]