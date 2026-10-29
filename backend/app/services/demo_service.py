"""Explicit demo storage only. Synthetic data feeds the unchanged learning engine."""
import hashlib
import hmac
from uuid import uuid4
from datetime import datetime, UTC, timedelta
import jwt
from fastapi import HTTPException
from sqlalchemy import func, update, delete
from app.core import config
from app.models.user import User
from app.models.demo_session import DemoSession, DemoBudget
from app.models.learning_track import LearningTrack
from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.study_log import StudyLog
from app.models.memory import Memory
from app.schemas.capture import Interpretation


def require_demo_storage(bind):
    database = bind.url.database or ""
    if (config.APP_EDITION != "demo" or not config.DEMO_STORAGE_ENABLED
            or bind.dialect.name != "postgresql" or not database.endswith("_demo")
            or len(config.DEMO_SECRET_KEY) < 32 or config.DEMO_SECRET_KEY == config.SECRET_KEY):
        raise RuntimeError("Demo requires explicit separate PostgreSQL storage ending _demo and a distinct demo signing secret")


def aware(value):
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def valid_guest(db, user_id):
    session = db.get(DemoSession, user_id)
    return session is not None and aware(session.expires_at) > datetime.now(UTC)


def reserve_mutation(db, user_id):
    reserved = db.execute(update(DemoSession).where(
        DemoSession.user_id == user_id, DemoSession.expires_at > datetime.now(UTC),
        DemoSession.mutations < 100).values(mutations=DemoSession.mutations + 1)).rowcount
    if reserved != 1:
        db.rollback()
        raise HTTPException(429, "This demo session reached its 100-change limit. Reset the demo to continue.")
    db.commit()


PATHS = [
    ("Python Foundations", ["Variables and data types", "Functions", "Decorators", "Closures", "Exception handling"],
     "Closures", "I still find it difficult to explain which variables a closure keeps.", "Trace a closure with two nested functions."),
    ("SQL Fundamentals", ["SELECT queries", "Filtering", "JOIN operations", "GROUP BY", "Subqueries"],
     "JOIN operations", "I am unsure why a LEFT JOIN sometimes returns repeated rows.", "Practice a LEFT JOIN with two small tables."),
    ("Data Structures", ["Lists and arrays", "Stacks", "Queues", "Searching", "Basic complexity"],
     "Basic complexity", "I need more practice comparing linear and binary search.", "Implement a stack and explain its push and pop operations."),
]


def seed_guest(db, user_id):
    require_demo_storage(db.get_bind())
    if not db.get(DemoSession, user_id):
        raise RuntimeError("Only explicitly issued demo identities may be seeded")
    if db.query(LearningCapture).filter_by(user_id=user_id).first():
        return  # Repeatable, never duplicates or deletes another account's records.
    now = datetime.now(UTC)
    for path_index, (name, topics, difficulty_topic, difficulty, intention) in enumerate(PATHS):
        track = LearningTrack(user_id=user_id, name=name, description=f"Synthetic learning history for {name}.")
        db.add(track); db.flush()
        for index, topic in enumerate(topics):
            date = now - timedelta(days=16 - index * 3, hours=path_index)
            minutes = [25, 30, 45, 35, 20][index]
            content = f"I studied {topic.lower()} in {name} and worked through a short example."
            if topic == "JOIN operations":
                content = "I studied SQL joins (JOIN operations) and worked through a short example."
            observations = [{"observation_type": "learned", "topic": topic, "content": content, "evidence": content}]
            if index == 4:
                observations += [
                    {"observation_type": "difficulty", "topic": difficulty_topic, "content": difficulty, "evidence": difficulty},
                    {"observation_type": "intended_next_step", "topic": difficulty_topic, "content": intention, "evidence": intention},
                    {"observation_type": "open_question", "topic": difficulty_topic, "content": f"How can I explain {difficulty_topic.lower()} with a smaller example?", "evidence": ""},
                ]
            interpretation = Interpretation(subject=name, topics=[topic], observations=observations, duration_minutes=minutes)
            original = " ".join([content] + ([difficulty, intention] if index == 4 else []) + [f"Studied for {minutes} minutes."])
            log = StudyLog(user_id=user_id, learning_track_id=track.id, topic=topic, duration_minutes=minutes,
                           notes="Synthetic demonstration study session", created_at=date)
            db.add(log); db.flush()
            capture = LearningCapture(user_id=user_id, source_type="text", original_text=original,
                confirmed_interpretation=interpretation.model_dump(mode="json"), status="confirmed", version=2,
                learning_track_id=track.id, study_log_id=log.id, created_at=date, confirmed_at=date,
                extraction_version="synthetic-demo-v1")
            db.add(capture); db.flush()
            for position, observation in enumerate(interpretation.observations):
                db.add(LearningObservation(user_id=user_id, capture_id=capture.id, position=position,
                    **observation.model_dump(), provenance="user_confirmed", created_at=date))
            if index == 4:
                db.add(Memory(user_id=user_id, study_log_id=log.id, title=f"Return to {name}",
                              content=f"{difficulty} Next: {intention}", category="synthetic learning"))
    db.flush()


def create_guest(db, peer):
    require_demo_storage(db.get_bind())
    now = datetime.now(UTC)
    peer_hash = hmac.new(config.DEMO_SECRET_KEY.encode(), peer.encode(), hashlib.sha256).hexdigest()
    # A single PostgreSQL row serializes issuance across every backend instance.
    budget = db.query(DemoBudget).filter_by(id=1).with_for_update().first()
    if budget is None:
        raise HTTPException(503, "Demo storage needs initialization")
    if budget.day != now.date().isoformat():
        budget.day, budget.issued = now.date().isoformat(), 0
    recent = db.query(func.count(DemoSession.user_id)).filter(
        DemoSession.ip_hash == peer_hash, DemoSession.created_at >= now - timedelta(hours=1)).scalar()
    if budget.issued >= 500 or recent >= 10:
        raise HTTPException(429, "Demo session limit reached. Try again later.")
    budget.issued += 1
    identity = uuid4().hex
    user = User(username=f"Avery-{identity[:8]}", email=f"demo-{identity}@example.com", hashed_password="!demo-no-password")
    db.add(user); db.flush()
    expires = now + timedelta(hours=2)
    db.add(DemoSession(user_id=user.id, ip_hash=peer_hash, created_at=now, expires_at=expires)); db.flush()
    seed_guest(db, user.id)
    token = jwt.encode({"sub": user.email, "exp": expires, "edition": "demo", "aud": "learntrack-demo"},
                       config.DEMO_SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer", "expires_at": expires}


def purge_expired(db, limit=100):
    """Delete only expired issued demo owners; never scan/delete other accounts."""
    from app.models.learning_action import LearningAction
    from app.models.conversation import Conversation
    from app.models.usage_limit import UsageLimit
    from app.models.ai_credential import AICredential
    require_demo_storage(db.get_bind())
    sessions = db.query(DemoSession).filter(DemoSession.expires_at < datetime.now(UTC)).order_by(
        DemoSession.expires_at).limit(min(max(limit, 1), 100)).with_for_update(skip_locked=True).all()
    owners = [session.user_id for session in sessions]
    if not owners:
        return 0
    for model in [LearningAction, LearningObservation, LearningCapture, Conversation, UsageLimit,
                  Memory, StudyLog, LearningTrack, AICredential, DemoSession]:
        db.execute(delete(model).where(model.user_id.in_(owners)), execution_options={"synchronize_session": False})
    db.execute(delete(User).where(User.id.in_(owners)), execution_options={"synchronize_session": False})
    db.commit()
    return len(owners)
