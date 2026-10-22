from sqlalchemy import (Column, Integer, String, Text, JSON, DateTime, ForeignKey,
                        CheckConstraint, UniqueConstraint, ForeignKeyConstraint)
from sqlalchemy.sql import func
from app.db.base import Base


class LearningCapture(Base):
    __tablename__ = "learning_captures"
    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_capture_owner"),
        CheckConstraint("source_type IN ('text','voice')", name="ck_capture_source"),
        CheckConstraint("status IN ('pending','failed','confirmed','discarded')", name="ck_capture_status"),
        CheckConstraint("version > 0", name="ck_capture_version"),
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String, nullable=False)
    original_text = Column(Text, nullable=False)
    proposed_interpretation = Column(JSON)
    confirmed_interpretation = Column(JSON)
    status = Column(String, nullable=False, default="pending")
    version = Column(Integer, nullable=False, default=1)
    processing_model = Column(String)
    extraction_version = Column(String)
    confirmation_digest = Column(String)
    study_log_id = Column(Integer, ForeignKey("study_logs.id", ondelete="SET NULL"))
    learning_track_id = Column(Integer, ForeignKey("learning_tracks.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmed_at = Column(DateTime(timezone=True))


class LearningObservation(Base):
    __tablename__ = "learning_observations"
    __table_args__ = (
        ForeignKeyConstraint(["capture_id", "user_id"], ["learning_captures.id", "learning_captures.user_id"], ondelete="CASCADE"),
        UniqueConstraint("capture_id", "position", name="uq_capture_observation_position"),
        CheckConstraint("observation_type IN ('learned','understood_self_report','difficulty','open_question','intended_next_step')", name="ck_observation_type"),
        CheckConstraint("provenance = 'user_confirmed'", name="ck_observation_provenance"),
        CheckConstraint("position >= 0", name="ck_observation_position"),
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    capture_id = Column(Integer, nullable=False, index=True)
    position = Column(Integer, nullable=False)
    observation_type = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    provenance = Column(String, nullable=False, default="user_confirmed")
    memory_id = Column(Integer, ForeignKey("memories.id", ondelete="SET NULL"), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
