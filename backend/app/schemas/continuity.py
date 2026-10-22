from datetime import datetime
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.validation import NonBlank

ActionType = Literal["next_step", "difficulty", "question", "review", "recommendation"]
ActionStatus = Literal["completed", "resolved", "dismissed"]
LearningState = Literal[
    "recorded",
    "exploring",
    "self_reported_understood",
    "needs_attention",
    "review_suggested",
    "insufficient_evidence",
]


class LearningActionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: Annotated[NonBlank, Field(max_length=128)]
    action_type: ActionType
    status: ActionStatus
    observation_id: int | None = None
    capture_id: int | None = None
    learning_track_id: int | None = None
    topic: Annotated[str, Field(max_length=255)] | None = None
    recommendation_id: Annotated[str, Field(max_length=255)] | None = None
    notes: Annotated[str, Field(max_length=2000)] | None = None


class LearningActionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ActionStatus
    notes: Annotated[str, Field(max_length=2000)] | None = None


class LearningActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    idempotency_key: str
    action_type: str
    status: str
    observation_id: int | None = None
    capture_id: int | None = None
    learning_track_id: int | None = None
    topic: str | None = None
    recommendation_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ObservationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    observation_type: str
    topic: str
    content: str
    evidence: str
    capture_id: int
    is_resolved: bool = False
    is_completed: bool = False
    is_dismissed: bool = False
    created_at: datetime


class ResumableCheckpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    topic: str
    normalized_topic: str
    learning_track_id: int | None = None
    learning_track_name: str | None = None
    state: LearningState
    last_capture_id: int | None = None
    last_capture_at: datetime | None = None
    last_capture_excerpt: str | None = None
    latest_observation_id: int | None = None
    latest_observation_content: str | None = None
    understood_self_reports: list[ObservationBrief] = Field(default_factory=list)
    unresolved_difficulties: list[ObservationBrief] = Field(default_factory=list)
    unresolved_questions: list[ObservationBrief] = Field(default_factory=list)
    pending_next_steps: list[ObservationBrief] = Field(default_factory=list)
    review_suggested: bool = False
    days_since_last_activity: int = 0


class EvidenceRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    type: str
    priority: Literal["high", "medium", "low"]
    topic: str
    learning_track_id: int | None = None
    learning_track_name: str | None = None
    action: str
    reason: str
    source_capture_id: int | None = None
    source_observation_id: int | None = None
    evidence: str | None = None
    review_due_at: datetime | None = None
    link_url: str | None = None
    status: str | None = None


class TopicContinuityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    topic: str
    normalized_topic: str
    learning_track_id: int | None = None
    learning_track_name: str | None = None
    state: LearningState
    confirmed_capture_count: int
    observations_count: int
    difficulties_count: int
    unresolved_difficulties_count: int
    questions_count: int
    unresolved_questions_count: int
    pending_next_steps_count: int
    last_studied_at: datetime | None = None
    is_review_due: bool = False


class LearningOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    confirmed_captures_count: int
    distinct_topics_count: int
    total_observations_count: int
    learned_count: int
    understood_count: int
    difficulties_count: int
    unresolved_difficulties_count: int
    questions_count: int
    unresolved_questions_count: int
    pending_next_actions_count: int
    total_logged_study_hours: float
    latest_activity_at: datetime | None = None
    current_streak: int = 0
    review_suggested_count: int = 0
    checkpoints_count: int = 0
