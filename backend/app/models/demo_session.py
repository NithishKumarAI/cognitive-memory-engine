from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class DemoSession(Base):
    __tablename__ = "demo_sessions"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    ip_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    mutations = Column(Integer, nullable=False, default=0)


class DemoBudget(Base):
    __tablename__ = "demo_budget"
    id = Column(Integer, primary_key=True)
    day = Column(String(10), nullable=False)
    issued = Column(Integer, nullable=False, default=0)
