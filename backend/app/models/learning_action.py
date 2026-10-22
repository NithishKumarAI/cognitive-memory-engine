from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    CheckConstraint, UniqueConstraint
)
from sqlalchemy.sql import func
from app.db.base import Base


class LearningAction(Base):
    __tablename__ = "learning_actions"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_learning_action_user_idempotency"),
        CheckConstraint("status IN ('completed', 'resolved', 'dismissed')", name="ck_learning_action_status"),
        CheckConstraint("action_type IN ('next_step', 'difficulty', 'question', 'review', 'recommendation')", name="ck_learning_action_type"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False)
    request_digest = Column(String(64), nullable=True)
    action_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    observation_id = Column(Integer, ForeignKey("learning_observations.id", ondelete="SET NULL"), nullable=True, index=True)
    capture_id = Column(Integer, ForeignKey("learning_captures.id", ondelete="SET NULL"), nullable=True, index=True)
    learning_track_id = Column(Integer, ForeignKey("learning_tracks.id", ondelete="SET NULL"), nullable=True)
    topic = Column(String(255), nullable=True, index=True)
    recommendation_id = Column(String(255), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
