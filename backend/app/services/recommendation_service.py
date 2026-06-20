from datetime import datetime
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.schemas.recommendation import RecommendationResponse

class RecommendationService:

    @staticmethod
    def sort_recommendations(recommendations: list):
        """
        Sort recommendations by priority.

        high -> medium -> low
        """

        priority_order = {
            "high": 3,
            "medium": 2,
            "low": 1
        }

        return sorted(
            recommendations,
            key=lambda recommendation:
            priority_order.get(
                recommendation.priority,
                0
            ),
            reverse=True
        )

    @staticmethod
    def get_neglected_recommendations(
            db: Session,
            user_id: int
    ):
        recommendations = []

        learning_tracks = (
            db.query(LearningTrack)
            .filter(LearningTrack.user_id == user_id)
            .all()
        )

        for track in learning_tracks:

            latest_log = (
                db.query(StudyLog)
                .filter(
                    StudyLog.user_id == user_id,
                    StudyLog.learning_track_id == track.id
                )
                .order_by(StudyLog.created_at.desc())
                .first()
            )

            if not latest_log:
                continue

            days_since_last_study = (
                datetime.now(timezone.utc) -
                latest_log.created_at.replace(
                    tzinfo=timezone.utc
                )
            ).days

            if days_since_last_study >= 7:

                priority = (
                    "high"
                    if days_since_last_study >= 14
                    else "medium"
                )

                recommendations.append(
                    RecommendationResponse(
                        type="neglected_track",
                        priority=priority,
                        message=(
                            f"You have not studied "
                            f"{track.name} for "
                            f"{days_since_last_study} days."
                        )
                    )
                )

        return RecommendationService.sort_recommendations(
            recommendations
        )
    @staticmethod
    def get_continue_learning_recommendations(
            db: Session,
            user_id: int
    ):

        latest_study_log = (
            db.query(StudyLog)
            .filter(
                StudyLog.user_id == user_id,
                StudyLog.learning_track_id.isnot(None)
            )
            .order_by(StudyLog.created_at.desc())
            .first()
        )

        if not latest_study_log:
            return []

        track = (
            db.query(LearningTrack)
            .filter(
                LearningTrack.id ==
                latest_study_log.learning_track_id
            )
            .first()
        )

        if not track:
            return []

        return [
            RecommendationResponse(
                type="continue_learning",
                priority="low",
                message=(
                    f"Continue your "
                    f"{track.name} learning journey."
                )
            )
        ]
    @staticmethod
    def get_weak_area_recommendations(
            db: Session,
            user_id: int
    ):

        recommendations = []

        learning_tracks = (
            db.query(LearningTrack)
            .filter(LearningTrack.user_id == user_id)
            .all()
        )

        for track in learning_tracks:

            study_count = (
                db.query(func.count(StudyLog.id))
                .filter(
                    StudyLog.user_id == user_id,
                    StudyLog.learning_track_id == track.id
                )
                .scalar()
            )

            if study_count == 0:

                recommendations.append(
                    RecommendationResponse(
                        type="start_learning",
                        priority="low",
                        message=(
                            f"Start your "
                            f"{track.name} learning journey."
                        )
                    )
                )

            elif study_count < 2:

                recommendations.append(
                    RecommendationResponse(
                        type="weak_area",
                        priority="medium",
                        message=(
                            f"You have studied "
                            f"{track.name} only "
                            f"{study_count} time(s). "
                            f"Spend more time on it."
                        )
                    )
                )

        return RecommendationService.sort_recommendations(
            recommendations
        )
    @staticmethod
    def get_daily_recommendations(
            db: Session,
            user_id: int
    ):

        recommendations = []

        recommendations.extend(
            RecommendationService
            .get_neglected_recommendations(
                db=db,
                user_id=user_id
            )
        )

        recommendations.extend(
            RecommendationService
            .get_continue_learning_recommendations(
                db=db,
                user_id=user_id
            )
        )

        recommendations.extend(
            RecommendationService
            .get_weak_area_recommendations(
                db=db,
                user_id=user_id
            )
        )

        recommendations = (
            RecommendationService
            .sort_recommendations(
                recommendations
            )
        )

        return recommendations