from contextlib import contextmanager
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.models.learning_capture import LearningCapture
from app.schemas.capture import AnalyzeInput, ConfirmInput, VersionInput, CaptureResponse
from app.services import capture_service as service
from app.services.audio_service import MAX_AUDIO_BYTES, validate_audio, transcribe
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/capture", tags=["Learning capture"])


@contextmanager
def safe_write(db):
    try:
        yield
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(503, "Unable to save capture; reload and retry") from None


@router.post("/manual", response_model=CaptureResponse)
def manual_new(payload: AnalyzeInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    with safe_write(db):
        service.check_track(db, payload.learning_track_id, user.id)
        capture = LearningCapture(user_id=user.id, original_text=payload.text,
            source_type=payload.source_type, learning_track_id=payload.learning_track_id,
            status="pending", version=1, processing_model=None, extraction_version="manual")
        db.add(capture)
        db.commit()
        return service.response(db, capture, "Manual draft saved. Add your observations, then confirm and save.")


@router.post("/analyze", response_model=CaptureResponse)
def analyze_new(payload: AnalyzeInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_id = user.id
    with safe_write(db):
        service.check_track(db, payload.learning_track_id, user_id)
        capture = LearningCapture(user_id=user_id, original_text=payload.text,
            source_type=payload.source_type, learning_track_id=payload.learning_track_id,
            status="pending", version=1)
        db.add(capture)
        db.flush()
        capture_id = capture.id
        db.commit()  # Raw input remains recoverable even if Gemini is unavailable.
        return service.analyze(db, capture_id, user_id, 1)


@router.post("/transcribe")
async def transcribe_audio(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.headers.get("x-audio-consent") != "true":
        raise HTTPException(400, "Explicit cloud audio processing consent is required")
    db.rollback()  # Authentication has completed; no open DB transaction during upload/provider work.
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Audio must be at most 4 MiB")
        data.extend(chunk)
    mime = validate_audio(bytes(data), request.headers.get("content-type", "").split(";")[0].lower())
    try:
        text = await run_in_threadpool(transcribe, bytes(data), mime)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Transcription unavailable; retry or type your update") from None
    return {"transcript": text}


@router.get("", response_model=list[CaptureResponse])
def list_captures(limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0, le=10000),
                  status: Literal["pending", "failed", "confirmed", "discarded"] | None = None,
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(LearningCapture).filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    captures = query.order_by(LearningCapture.id.desc()).offset(offset).limit(limit).all()
    return [service.response(db, capture) for capture in captures]


@router.get("/{capture_id}", response_model=CaptureResponse)
def get_capture(capture_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.response(db, service.owned(db, capture_id, user.id))


@router.post("/{capture_id}/analyze", response_model=CaptureResponse)
def retry_analysis(capture_id: int, payload: VersionInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_id = user.id
    with safe_write(db):
        return service.analyze(db, capture_id, user_id, payload.expected_version)


@router.post("/{capture_id}/confirm", response_model=CaptureResponse)
def confirm_capture(capture_id: int, payload: ConfirmInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user_id = user.id
    with safe_write(db):
        return service.confirm(db, capture_id, user_id, payload)


@router.post("/{capture_id}/discard", response_model=CaptureResponse)
def discard_capture(capture_id: int, payload: VersionInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    with safe_write(db):
        capture = service.owned(db, capture_id, user.id, lock=True)
        if capture.status == "discarded":
            return service.response(db, capture, "Already discarded.")
        if capture.status == "confirmed" or capture.version != payload.expected_version:
            raise HTTPException(409, "Capture changed; reload before discarding")
        capture.status = "discarded"
        capture.version += 1
        db.commit()
        return service.response(db, capture, "Draft discarded. Original text retained in your account.")
