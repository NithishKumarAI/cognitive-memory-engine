from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core import config
from app.core.auth import get_current_user
from app.db.dependencies import get_db
from app.models.demo_session import DemoSession
from app.models.learning_capture import LearningCapture
from app.services import demo_service
from app.services.capture_service import response

router = APIRouter(tags=["Demo"])


def demo_only():
    if config.APP_EDITION != "demo":
        raise HTTPException(404, "Not found")


@router.get("/edition")
def edition():
    return {"edition": config.APP_EDITION, "live_ai": False if config.APP_EDITION == "demo" else config.AI_ENABLED}


@router.post("/demo/session", dependencies=[Depends(demo_only)])
def guest(request: Request, db: Session = Depends(get_db)):
    try:
        result = demo_service.create_guest(db, request.client.host if request.client else "unknown")
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


@router.post("/demo/reset", dependencies=[Depends(demo_only)])
def reset(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        # Old token is revoked at the same commit that publishes the replacement.
        result = demo_service.create_guest(db, request.client.host if request.client else "unknown")
        db.get(DemoSession, user.id).expires_at = datetime.now(UTC)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


@router.post("/demo/example", dependencies=[Depends(demo_only)])
def guided_example(db: Session = Depends(get_db), user=Depends(get_current_user)):
    original = "I studied SQL joins. Repeated rows are confusing. Next I will practice a LEFT JOIN."
    proposal = {"subject": "SQL", "topics": ["JOIN operations"], "observations": [
        {"observation_type": "learned", "topic": "JOIN operations", "content": "Studied SQL joins", "evidence": "I studied SQL joins"},
        {"observation_type": "difficulty", "topic": "JOIN operations", "content": "Repeated rows are confusing", "evidence": "Repeated rows are confusing"},
        {"observation_type": "intended_next_step", "topic": "JOIN operations", "content": "Practice a LEFT JOIN", "evidence": "Next I will practice a LEFT JOIN"}]}
    capture = LearningCapture(user_id=user.id, original_text=original, source_type="text", status="pending", version=1,
                              proposed_interpretation=proposal, extraction_version="guided-example-v1")
    db.add(capture); db.commit()
    return response(db, capture, "Guided example: a scripted draft, not a live Gemini result. Review and confirm it yourself.")
