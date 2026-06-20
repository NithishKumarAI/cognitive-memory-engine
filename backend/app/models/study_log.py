from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class StudyLog(Base):
    __tablename__ = "study_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    learning_track_id = Column(
        Integer,
        ForeignKey(
            "learning_tracks.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    topic = Column(
        String(255),
        nullable=False
    )

    duration_minutes = Column(
        Integer,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    notes = Column(
        String,
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="study_logs"
    )

    learning_track = relationship(
        "LearningTrack",
        back_populates="study_logs"
    )

    memories = relationship(
        "Memory",
        back_populates="study_log"
    )