from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.db.database import Base
from sqlalchemy.orm import relationship

class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    memory_id = Column(
        Integer,
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    model_name = Column(
        String,
        nullable=False
    )

    embedding = Column(
        Vector(768)
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    memory = relationship(
        "Memory",
        back_populates="embedding"
    )
