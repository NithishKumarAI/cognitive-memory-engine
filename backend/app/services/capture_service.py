import hashlib
import json
from datetime import datetime, UTC
from fastapi import HTTPException
from sqlalchemy import update
from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.schemas.capture import CaptureResponse, ObservationResponse
from app.schemas.memory import MemoryCreate
from app.crud.memory import stage_memory, validated_embedding
from app.services.extraction_service import extract_learning, EXTRACTION_VERSION
from app.core.config import GEMINI_MODEL


def normalize(value):
    return " ".join(value.split()).casefold()


def owned(db, capture_id, user_id, lock=False):
    query = db.query(LearningCapture).filter_by(id=capture_id, user_id=user_id)
    if lock:
        query = query.with_for_update()
    capture = query.populate_existing().first()
    if capture is None:
        raise HTTPException(404, "Capture not found")
    return capture


def check_track(db, track_id, user_id):
    if track_id is not None and not db.query(LearningTrack).filter_by(id=track_id, user_id=user_id).first():
        raise HTTPException(400, "Invalid learning_track_id")


def response(db, capture, message=None):
    result = CaptureResponse.model_validate(capture)
    result.observations = [ObservationResponse.model_validate(item) for item in
        db.query(LearningObservation).filter_by(capture_id=capture.id, user_id=capture.user_id).order_by(LearningObservation.position)]
    proposed = result.proposed_interpretation
    names = {normalize(name) for name in ([proposed.subject] + proposed.topics) if name} if proposed else set()
    result.matching_track_ids = [track.id for track in db.query(LearningTrack).filter_by(user_id=capture.user_id)
                                 if normalize(track.name) in names]
    result.message = message
    return result


def analyze(db, capture_id, user_id, expected_version):
    capture = owned(db, capture_id, user_id)
    if capture.status not in ("pending", "failed") or capture.version != expected_version:
        raise HTTPException(409, "Capture changed; reload before analyzing")
    original = capture.original_text
    db.rollback()  # Release the read transaction before the external LLM call.
    try:
        proposal = extract_learning(original).model_dump(mode="json")
        status, message = "pending", "Review and correct the proposal before confirming."
    except Exception:
        proposal, status = None, "failed"
        message = "Analysis unavailable or invalid. Retry analysis or enter your interpretation manually."
    changed = db.execute(update(LearningCapture).where(
        LearningCapture.id == capture_id, LearningCapture.user_id == user_id,
        LearningCapture.version == expected_version,
        LearningCapture.status.in_(["pending", "failed"])).values(
            proposed_interpretation=proposal, status=status, version=expected_version + 1,
            processing_model=GEMINI_MODEL, extraction_version=EXTRACTION_VERSION),
        execution_options={"synchronize_session": False}).rowcount
    if changed != 1:
        raise HTTPException(409, "Capture changed during analysis; reload")
    db.commit()
    return response(db, owned(db, capture_id, user_id), message)


def confirm(db, capture_id, user_id, payload):
    canonical = payload.model_dump(mode="json", exclude={"expected_version"})
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    capture = owned(db, capture_id, user_id)
    if capture.status == "confirmed":
        if capture.confirmation_digest != digest:
            raise HTTPException(409, "Capture already confirmed with different information")
        return response(db, capture, "Already saved; no duplicate records created.")
    if capture.status not in ("pending", "failed") or capture.version != payload.expected_version:
        raise HTTPException(409, "Capture changed; reload before confirming")
    check_track(db, payload.learning_track_id, user_id)
    interpretation = payload.interpretation
    topic = interpretation.subject or next(iter(interpretation.topics), None)
    if not topic and interpretation.observations:
        topic = interpretation.observations[0].topic
    if interpretation.duration_minutes is not None and not topic:
        raise HTTPException(422, "Provide a subject or topic to create a study log")
    db.rollback()
    # Embeddings are local, but can be slow: generate before acquiring the row lock.
    prepared = []
    if payload.create_memories:
        for observation in interpretation.observations:
            memory = MemoryCreate(title=observation.topic, content=observation.content,
                                  category=observation.observation_type)
            prepared.append((memory, validated_embedding(f"{memory.title}\n\n{memory.content}")))
    capture = owned(db, capture_id, user_id, lock=True)
    if capture.status == "confirmed" and capture.confirmation_digest == digest:
        return response(db, capture, "Already saved; no duplicate records created.")
    if capture.status not in ("pending", "failed") or capture.version != payload.expected_version:
        raise HTTPException(409, "Capture changed; reload before confirming")
    # Re-check link authorization after preparation; hold the selected track until commit.
    if payload.learning_track_id is not None:
        track = db.query(LearningTrack).filter_by(id=payload.learning_track_id, user_id=user_id).with_for_update().first()
        if not track:
            raise HTTPException(400, "Invalid learning_track_id")
    log = None
    if interpretation.duration_minutes is not None:
        log = StudyLog(user_id=user_id, topic=topic, duration_minutes=interpretation.duration_minutes,
                       notes=f"Confirmed learning capture #{capture_id}", learning_track_id=payload.learning_track_id)
        db.add(log)
        db.flush()
    for position, observation in enumerate(interpretation.observations):
        memory_id = None
        if payload.create_memories:
            memory, embedding = prepared[position]
            memory.study_log_id = log.id if log else None
            memory_id = stage_memory(db, memory, user_id, embedding).id
        db.add(LearningObservation(user_id=user_id, capture_id=capture_id, position=position,
            **observation.model_dump(), provenance="user_confirmed", memory_id=memory_id))
    capture.confirmed_interpretation = interpretation.model_dump(mode="json")
    capture.learning_track_id = payload.learning_track_id
    capture.study_log_id = log.id if log else None
    capture.confirmation_digest = digest
    capture.status = "confirmed"
    capture.confirmed_at = datetime.now(UTC)
    capture.version += 1
    db.flush()
    db.commit()
    return response(db, owned(db, capture_id, user_id), "Confirmed information saved.")
