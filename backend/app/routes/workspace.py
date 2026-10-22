"""Small owner-scoped read APIs. No AI calls or persisted search index."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.models.memory import Memory
from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.conversation import Conversation

router = APIRouter(tags=["Workspace"])


class SearchResult(BaseModel):
    kind: Literal["track", "study_log", "memory", "capture", "observation"]
    id: int
    title: str
    excerpt: str
    url: str


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(min_length=2, max_length=120), limit: int = Query(20, ge=1, le=30),
           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = q.strip()
    if len(query) < 2:
        from fastapi import HTTPException
        raise HTTPException(422, "Enter at least two nonblank characters")
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    results = []
    definitions = [
        (LearningTrack, "track", [LearningTrack.name, LearningTrack.description]),
        (Memory, "memory", [Memory.title, Memory.content, Memory.category]),
        (StudyLog, "study_log", [StudyLog.topic, StudyLog.notes]),
        (LearningCapture, "capture", [LearningCapture.original_text]),
        (LearningObservation, "observation", [LearningObservation.topic, LearningObservation.content]),
    ]
    for model, kind, columns in definitions:
        statement = db.query(model).filter(model.user_id == user.id,
            or_(*(column.ilike(pattern, escape="\\") for column in columns)))
        if model is LearningCapture:
            statement = statement.filter(LearningCapture.status == "confirmed")
        if model is LearningObservation:
            statement = statement.join(LearningCapture, LearningCapture.id == LearningObservation.capture_id).filter(
                LearningCapture.user_id == user.id, LearningCapture.status == "confirmed")
        for row in statement.order_by(model.id.desc()).limit(limit - len(results)):
            if kind == "track": title, content, url = row.name, row.description or "Learning path", f"/dashboard/learning-tracks#track-{row.id}"
            elif kind == "memory": title, content, url = row.title, row.content, f"/dashboard/memories/{row.id}"
            elif kind == "study_log": title, content, url = row.topic, row.notes, f"/dashboard/study-logs#record-{row.id}"
            elif kind == "capture": title, content, url = f"Capture #{row.id}", row.original_text, f"/dashboard/capture?capture={row.id}"
            else: title, content, url = row.topic, row.content, f"/dashboard/capture?capture={row.capture_id}#observation-{row.id}"
            results.append(SearchResult(kind=kind, id=row.id, title=title[:255], excerpt=content[:180], url=url))
        if len(results) >= limit:
            break
    return results


class ConversationRead(BaseModel):
    id: int
    message: str
    response: str
    created_at: datetime | None


@router.get("/rag/history", response_model=list[ConversationRead])
def history(before_id: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Conversation).filter(Conversation.user_id == user.id)
    if before_id is not None:
        query = query.filter(Conversation.id < before_id)
    # Sources were never stored. Return only historical text; never reconstruct citations.
    return [ConversationRead(id=row.id, message=row.message, response=row.response, created_at=row.created_at)
            for row in query.order_by(Conversation.id.desc()).limit(limit)]
