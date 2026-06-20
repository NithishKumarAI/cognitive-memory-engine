from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.models.user import User
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.recommendation import (
    RecommendationListResponse,
    DailyRecommendationResponse
)
from app.services.recommendation_service import (
    RecommendationService
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/test")
def test_recommendation_route(
        current_user: User = Depends(get_current_user)
):
    return {
        "message": "Recommendation router working",
        "user_id": current_user.id,
        "timestamp": datetime.utcnow()
    }

@router.get(
    "/neglected",
    response_model=RecommendationListResponse
)
def get_neglected_recommendations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    recommendations = (
        RecommendationService
        .get_neglected_recommendations(
            db=db,
            user_id=current_user.id
        )
    )

    return {
        "recommendations": recommendations
    }

@router.get(
    "/continue-learning",
    response_model=RecommendationListResponse
)
def get_continue_learning_recommendations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    recommendations = (
        RecommendationService
        .get_continue_learning_recommendations(
            db=db,
            user_id=current_user.id
        )
    )

    return {
        "recommendations": recommendations
    }

@router.get(
    "/weak-areas",
    response_model=RecommendationListResponse
)
def get_weak_area_recommendations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    recommendations = (
        RecommendationService
        .get_weak_area_recommendations(
            db=db,
            user_id=current_user.id
        )
    )

    return {
        "recommendations": recommendations
    }
@router.get(
    "/daily",
    response_model=DailyRecommendationResponse
)
def get_daily_recommendations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    recommendations = (
        RecommendationService
        .get_daily_recommendations(
            db=db,
            user_id=current_user.id
        )
    )

    return {
        "generated_at": datetime.utcnow(),
        "recommendations": recommendations
    }