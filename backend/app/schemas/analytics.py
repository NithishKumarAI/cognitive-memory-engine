from datetime import date
from pydantic import BaseModel


class TopicDistributionItem(BaseModel):
    topic: str
    total_minutes: int
    total_hours: float
    session_count: int


class StudyHoursResponse(BaseModel):
    total_minutes: int
    total_hours: float


class DailyActivityItem(BaseModel):
    date: date
    study_minutes: int


class FrequencyResponse(BaseModel):
    study_days_last_7_days: int
    study_days_last_30_days: int


class ConsistencyResponse(BaseModel):
    current_streak: int
    frequency_percentage: float
    consistency_score: float


class TopicRecencyResponse(BaseModel):
    topic: str
    last_studied: date
    days_since_last_study: int


class NeglectedTopicItem(BaseModel):
    topic: str
    days_since_last_study: int


class OverviewResponse(BaseModel):
    total_study_logs: int
    total_topics: int
    total_hours: float
    current_streak: int
    consistency_score: float