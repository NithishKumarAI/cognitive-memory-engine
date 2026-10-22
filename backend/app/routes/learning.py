from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.continuity import (
    LearningActionCreate,
    LearningActionUpdate,
    LearningActionResponse,
    ResumableCheckpointResponse,
    EvidenceRecommendationResponse,
    TopicContinuityResponse,
    LearningOverviewResponse,
)
from app.services import continuity_service as service

router = APIRouter(prefix="/learning", tags=["Learning continuity"])


@router.get("/overview", response_model=LearningOverviewResponse)
def get_learning_overview(
    timezone: str = Query("UTC"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.get_learning_overview(db, user.id, tz_name=timezone)


@router.get("/checkpoints", response_model=list[ResumableCheckpointResponse])
def get_checkpoints(
    track_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.get_resumable_checkpoints(db, user.id, track_id=track_id, limit=limit)


@router.get("/recommendations", response_model=list[EvidenceRecommendationResponse])
def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.generate_evidence_recommendations(db, user.id, limit=limit)


@router.get("/topics", response_model=list[TopicContinuityResponse])
def get_topics(
    track_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.get_topic_continuity_summaries(db, user.id, track_id=track_id, limit=limit)


@router.post("/actions", response_model=LearningActionResponse, status_code=status.HTTP_201_CREATED)
def record_action(
    payload: LearningActionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.record_user_action(db, user.id, payload)


@router.post("/actions/{action_id}/update", response_model=LearningActionResponse)
@router.patch("/actions/{action_id}", response_model=LearningActionResponse)
def update_action(
    action_id: int,
    payload: LearningActionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return service.update_user_action(db, user.id, action_id, payload)
