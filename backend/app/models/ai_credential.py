from sqlalchemy import Column, Integer, Text, ForeignKey
from app.db.base import Base


class AICredential(Base):
    __tablename__ = "ai_credentials"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    encrypted_key = Column(Text, nullable=False)
