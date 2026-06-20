from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User

from app.services.analytics_service import (
    get_topic_distribution,
    get_study_hours,
    get_overview,
    get_most_studied_topics,
    get_least_studied_topics,
    get_daily_activity,
    get_weekly_study_hours,
    get_monthly_study_hours,
    get_study_streak,
    get_study_frequency,
    get_consistency_score,
    get_topic_recency,
    get_neglected_topics

)
from app.schemas.analytics import (
    TopicDistributionItem,
    StudyHoursResponse,
    DailyActivityItem,
    FrequencyResponse,
    ConsistencyResponse,
    TopicRecencyResponse,
    NeglectedTopicItem,
    OverviewResponse
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get(
    "/topic-distribution",
    response_model=list[TopicDistributionItem]
)
def topic_distribution(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_topic_distribution(
        db,
        current_user.id
    )


@router.get(
    "/study-hours",
    response_model=StudyHoursResponse
)
def study_hours(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_study_hours(
        db,
        current_user.id
    )


@router.get(
    "/overview",
    response_model=OverviewResponse
)
def overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_overview(
        db,
        current_user.id
    )

@router.get("/most-studied-topics")
def most_studied_topics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_most_studied_topics(
        db,
        current_user.id
    )


@router.get("/least-studied-topics")
def least_studied_topics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_least_studied_topics(
        db,
        current_user.id
    )

@router.get(
    "/daily-activity",
    response_model=list[DailyActivityItem]
)
def daily_activity(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_daily_activity(
        db,
        current_user.id
    )

@router.get("/weekly-study-hours")
def weekly_study_hours(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_weekly_study_hours(
        db,
        current_user.id
    )

@router.get("/monthly-study-hours")
def monthly_study_hours(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_monthly_study_hours(
        db,
        current_user.id
    )

@router.get("/streak")
def streak(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_study_streak(
        db,
        current_user.id
    )

@router.get(
    "/frequency",
    response_model=FrequencyResponse
)
def frequency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_study_frequency(
        db,
        current_user.id
    )

@router.get(
    "/consistency",
    response_model=ConsistencyResponse
)
def consistency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_consistency_score(
        db,
        current_user.id
    )

@router.get(
    "/topic-recency",
    response_model=list[TopicRecencyResponse]
)
def topic_recency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_topic_recency(
        db,
        current_user.id
    )

@router.get(
    "/neglected-topics",
    response_model=list[NeglectedTopicItem]
)
def neglected_topics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    return get_neglected_topics(
        db,
        current_user.id
    )