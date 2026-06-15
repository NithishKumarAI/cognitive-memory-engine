from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    study_log_id = Column(
        Integer,
        ForeignKey("study_logs.id", ondelete="SET NULL"),
        nullable=True
    )

    title = Column(String, nullable=False)

    content = Column(Text, nullable=False)

    category = Column(String, nullable=False)

    owner = relationship(
        "User",
        back_populates="memories"
    )

    study_log = relationship(
        "StudyLog",
        back_populates="memories"
    )
    embedding = relationship(
        "MemoryEmbedding",
        back_populates="memory",
        uselist=False,
        cascade="all, delete-orphan"
    )