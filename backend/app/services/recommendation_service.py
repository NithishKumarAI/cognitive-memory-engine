from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.schemas.recommendation import RecommendationResponse
from app.services.continuity_service import generate_evidence_recommendations


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
            key=lambda r: priority_order.get(r.priority, 0),
            reverse=True
        )

    @staticmethod
    def _to_legacy_response(ev_rec) -> RecommendationResponse:
        return RecommendationResponse(
            type=ev_rec.type,
            priority=ev_rec.priority,
            message=f"{ev_rec.action}. {ev_rec.reason}",
            id=ev_rec.id,
            topic=ev_rec.topic,
            learning_track_id=ev_rec.learning_track_id,
            learning_track_name=ev_rec.learning_track_name,
            action=ev_rec.action,
            reason=ev_rec.reason,
            source_capture_id=ev_rec.source_capture_id,
            source_observation_id=ev_rec.source_observation_id,
            evidence=ev_rec.evidence,
            review_due_at=ev_rec.review_due_at,
            link_url=ev_rec.link_url,
            status=ev_rec.status,
        )

    @staticmethod
    def get_daily_recommendations(db: Session, user_id: int):
        ev_recs = generate_evidence_recommendations(db=db, user_id=user_id)
        return [RecommendationService._to_legacy_response(r) for r in ev_recs]

    @staticmethod
    def get_neglected_recommendations(db: Session, user_id: int):
        ev_recs = generate_evidence_recommendations(db=db, user_id=user_id)
        # Filter review suggestions (neglected topics/intervals)
        filtered = [r for r in ev_recs if r.type in ("review_suggestion", "neglected_track")]
        return [RecommendationService._to_legacy_response(r) for r in filtered]

    @staticmethod
    def get_continue_learning_recommendations(db: Session, user_id: int):
        ev_recs = generate_evidence_recommendations(db=db, user_id=user_id)
        filtered = [r for r in ev_recs if r.type in ("continue_learning", "intended_next_step")]
        return [RecommendationService._to_legacy_response(r) for r in filtered]

    @staticmethod
    def get_weak_area_recommendations(db: Session, user_id: int):
        ev_recs = generate_evidence_recommendations(db=db, user_id=user_id)
        filtered = [r for r in ev_recs if r.type in ("unresolved_difficulty", "open_question", "start_track")]
        return [RecommendationService._to_legacy_response(r) for r in filtered]
