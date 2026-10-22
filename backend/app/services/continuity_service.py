import os
import hashlib
import json
from collections import defaultdict
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timezone, timedelta
from typing import Literal
import zoneinfo
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.models.learning_action import LearningAction
from app.schemas.continuity import (
    LearningActionCreate,
    LearningActionUpdate,
    LearningActionResponse,
    ObservationBrief,
    ResumableCheckpointResponse,
    EvidenceRecommendationResponse,
    TopicContinuityResponse,
    LearningOverviewResponse,
)

REVIEW_INITIAL_INTERVAL_DAYS = int(os.environ.get("LEARNING_REVIEW_INTERVAL_DAYS", "3"))


def normalize_topic(topic: str | None) -> str:
    if not topic:
        return ""
    return " ".join(topic.strip().split()).casefold()


def validate_timezone(tz_name: str | None) -> zoneinfo.ZoneInfo:
    if not tz_name or not tz_name.strip():
        return zoneinfo.ZoneInfo("UTC")
    try:
        return zoneinfo.ZoneInfo(tz_name.strip())
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid IANA timezone: {tz_name}")


def get_user_actions(db: Session, user_id: int):
    actions = db.query(LearningAction).filter(LearningAction.user_id == user_id).all()
    resolved_obs_ids = set()
    dismissed_obs_ids = set()
    completed_rec_ids = set()
    dismissed_rec_ids = set()
    recent_reviews = {}  # (track_id, norm_topic) -> latest_dt

    for a in actions:
        if a.observation_id:
            if a.status in ("completed", "resolved"):
                resolved_obs_ids.add(a.observation_id)
            elif a.status == "dismissed":
                dismissed_obs_ids.add(a.observation_id)
        if a.recommendation_id:
            if a.status in ("completed", "resolved"):
                completed_rec_ids.add(a.recommendation_id)
            elif a.status == "dismissed":
                dismissed_rec_ids.add(a.recommendation_id)
        if a.action_type == "review" and a.status == "completed" and a.topic:
            key = (a.learning_track_id, normalize_topic(a.topic))
            dt = a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=timezone.utc)
            if key not in recent_reviews or dt > recent_reviews[key]:
                recent_reviews[key] = dt

    return {
        "resolved_obs_ids": resolved_obs_ids,
        "dismissed_obs_ids": dismissed_obs_ids,
        "completed_rec_ids": completed_rec_ids,
        "dismissed_rec_ids": dismissed_rec_ids,
        "recent_reviews": recent_reviews,
    }


def record_user_action(db: Session, user_id: int, payload: LearningActionCreate) -> LearningActionResponse:
    payload = payload.model_copy(deep=True)
    # Validate ownership of related records if provided
    if payload.observation_id is not None:
        obs = (
            db.query(LearningObservation)
            .filter(
                LearningObservation.id == payload.observation_id,
                LearningObservation.user_id == user_id,
            )
            .first()
        )
        if not obs:
            raise HTTPException(status_code=404, detail="Observation not found")
        if payload.capture_id is not None and payload.capture_id != obs.capture_id:
            raise HTTPException(400, "Observation and capture do not match")
        if not payload.capture_id:
            payload.capture_id = obs.capture_id
        if not payload.topic:
            payload.topic = obs.topic

    if payload.capture_id is not None:
        capture = (
            db.query(LearningCapture)
            .filter(
                LearningCapture.id == payload.capture_id,
                LearningCapture.user_id == user_id,
            )
            .first()
        )
        if not capture:
            raise HTTPException(status_code=404, detail="Capture not found")

    if payload.learning_track_id is not None:
        track = (
            db.query(LearningTrack)
            .filter(
                LearningTrack.id == payload.learning_track_id,
                LearningTrack.user_id == user_id,
            )
            .first()
        )
        if not track:
            raise HTTPException(status_code=400, detail="Invalid learning_track_id")

    canonical = payload.model_dump(exclude={"idempotency_key"})
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    def replay(existing):
        matches = existing.request_digest == digest if existing.request_digest else all(
            getattr(existing, key) == value for key, value in canonical.items())
        if not matches:
            raise HTTPException(409, "Idempotency key was used with a different payload")
        return LearningActionResponse.model_validate(existing)
    existing = db.query(LearningAction).filter_by(user_id=user_id, idempotency_key=payload.idempotency_key).first()
    if existing:
        return replay(existing)

    action = LearningAction(
        user_id=user_id,
        idempotency_key=payload.idempotency_key,
        request_digest=digest,
        action_type=payload.action_type,
        status=payload.status,
        observation_id=payload.observation_id,
        capture_id=payload.capture_id,
        learning_track_id=payload.learning_track_id,
        topic=payload.topic,
        recommendation_id=payload.recommendation_id,
        notes=payload.notes,
    )
    db.add(action)
    try:
        db.commit()
        db.refresh(action)
    except IntegrityError:
        db.rollback()
        # Handle concurrent insertion with the same idempotency key
        conflict = (
            db.query(LearningAction)
            .filter(
                LearningAction.user_id == user_id,
                LearningAction.idempotency_key == payload.idempotency_key,
            )
            .first()
        )
        if conflict:
            return replay(conflict)
        raise HTTPException(503, "Unable to save action; please retry") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Unable to save action; please retry") from None

    return LearningActionResponse.model_validate(action)


def update_user_action(db: Session, user_id: int, action_id: int, payload: LearningActionUpdate) -> LearningActionResponse:
    action = (
        db.query(LearningAction)
        .filter(LearningAction.id == action_id, LearningAction.user_id == user_id)
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.status = payload.status
    if payload.notes is not None:
        action.notes = payload.notes
    db.commit()
    db.refresh(action)
    return LearningActionResponse.model_validate(action)


def get_resumable_checkpoints(db: Session, user_id: int, track_id: int | None = None,
                             limit: int | None = 20, _summary_only: bool = False) -> list[ResumableCheckpointResponse]:
    """Scan narrow metadata for honest history-wide state; hydrate only selected evidence.

    A recent-capture cutoff would silently lose old unresolved questions. Instead
    rank topic keys first, then fetch bounded evidence bodies for the chosen keys.
    """
    from types import SimpleNamespace
    info = get_user_actions(db, user_id)
    cap_query = db.query(LearningCapture).filter_by(user_id=user_id, status="confirmed")
    obs_query = db.query(LearningObservation.id, LearningObservation.capture_id, LearningObservation.topic,
        LearningObservation.observation_type, LearningObservation.position, LearningObservation.created_at).join(
        LearningCapture, LearningCapture.id == LearningObservation.capture_id).filter(
        LearningObservation.user_id == user_id, LearningCapture.user_id == user_id, LearningCapture.status == "confirmed")
    log_query = db.query(StudyLog.topic, StudyLog.learning_track_id, StudyLog.created_at).filter_by(user_id=user_id)
    if track_id is not None:
        cap_query = cap_query.filter(LearningCapture.learning_track_id == track_id)
        obs_query = obs_query.filter(LearningCapture.learning_track_id == track_id)
        log_query = log_query.filter(StudyLog.learning_track_id == track_id)
    def aware(dt):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    captures = {row.id: row for row in cap_query.with_entities(LearningCapture.id, LearningCapture.learning_track_id,
        LearningCapture.confirmed_at, LearningCapture.created_at).order_by(LearningCapture.confirmed_at.desc(), LearningCapture.id.desc())}
    metadata = obs_query.order_by(LearningCapture.confirmed_at.desc(), LearningCapture.id.desc(), LearningObservation.position).all()
    groups = {}
    def group(topic, assigned, stamp, cap_id=None):
        key = (assigned, normalize_topic(topic))
        if key not in groups:
            groups[key] = {"topic": topic, "stamp": stamp, "cap_id": cap_id, "observations": []}
        else:
            groups[key]["stamp"] = max(groups[key]["stamp"], stamp)
        return groups[key]
    for obs in metadata:
        cap = captures[obs.capture_id]
        group(obs.topic, cap.learning_track_id, aware(cap.confirmed_at or cap.created_at), cap.id)["observations"].append(obs)
    # Captures without observations can still carry explicitly confirmed subject/topic metadata.
    empty_captures = cap_query.outerjoin(LearningObservation, LearningObservation.capture_id == LearningCapture.id).filter(
        LearningObservation.id.is_(None)).with_entities(LearningCapture.id, LearningCapture.confirmed_interpretation)
    for cap_id, interpretation in empty_captures:
        cap = captures[cap_id]
        for topic in ([interpretation.get("subject")] + interpretation.get("topics", [])) if interpretation else []:
            if topic:
                item = group(topic, cap.learning_track_id, aware(cap.confirmed_at or cap.created_at), cap_id)
                previous = captures.get(item["cap_id"])
                if previous is None or aware(cap.confirmed_at or cap.created_at) > aware(previous.confirmed_at or previous.created_at):
                    item["cap_id"] = cap_id
    for topic, assigned, created in log_query:
        if created:
            group(topic, assigned, aware(created))
    selected = sorted(groups.items(), key=lambda pair: (-pair[1]["stamp"].timestamp(), pair[0][1], pair[0][0] or 0))
    if limit is not None:
        selected = selected[:limit]
    needed_ids = set()
    for _, item in selected:
        if not item["observations"]:
            continue
        needed_ids.add(item["observations"][0].id)
        for kind in ("understood_self_report", "difficulty", "open_question", "intended_next_step"):
            matches = [obs for obs in item["observations"] if obs.observation_type == kind and
                (kind == "understood_self_report" or obs.id not in info["resolved_obs_ids"] | info["dismissed_obs_ids"])]
            needed_ids.update(obs.id for obs in matches[:10])
    if _summary_only:
        bodies = {row.id: SimpleNamespace(**row._asdict(), content="", evidence="") for row in metadata}
        originals = {}
    else:
        bodies = {row.id: row for row in db.query(LearningObservation).filter(
            LearningObservation.user_id == user_id, LearningObservation.id.in_(needed_ids))} if needed_ids else {}
        cap_ids = {item["cap_id"] for _, item in selected if item["cap_id"]}
        originals = dict(db.query(LearningCapture.id, LearningCapture.original_text).filter(
            LearningCapture.user_id == user_id, LearningCapture.id.in_(cap_ids))) if cap_ids else {}
    tracks = dict(db.query(LearningTrack.id, LearningTrack.name).filter_by(user_id=user_id))
    now = datetime.now(timezone.utc)
    checkpoints = []
    for (assigned, norm), item in selected:
        rows = item["observations"]
        buckets = {kind: [] for kind in ("understood_self_report", "difficulty", "open_question", "intended_next_step")}
        counts = {kind: 0 for kind in buckets}
        for row in rows:
            kind = row.observation_type
            if kind not in buckets or kind != "understood_self_report" and row.id in info["resolved_obs_ids"] | info["dismissed_obs_ids"]:
                continue
            counts[kind] += 1
            if row.id in bodies and len(buckets[kind]) < 10:
                body = bodies[row.id]
                buckets[kind].append(ObservationBrief(id=row.id, observation_type=kind, topic=row.topic,
                    content=body.content, evidence=body.evidence, capture_id=row.capture_id, created_at=aware(row.created_at)))
        days = max(0, (now - item["stamp"]).days)
        review = info["recent_reviews"].get((assigned, norm))
        due = bool(rows) and days >= REVIEW_INITIAL_INTERVAL_DAYS and (review is None or (now - review).days >= REVIEW_INITIAL_INTERVAL_DAYS)
        state = "needs_attention" if counts["difficulty"] or counts["open_question"] else "review_suggested" if due else "self_reported_understood" if counts["understood_self_report"] else "exploring" if rows and days < 7 else "recorded"
        latest = rows[0] if rows else None
        raw = originals.get(item["cap_id"], "").strip()
        checkpoints.append(ResumableCheckpointResponse(topic=item["topic"], normalized_topic=norm,
            learning_track_id=assigned, learning_track_name=tracks.get(assigned), state=state,
            last_capture_id=item["cap_id"], last_capture_at=item["stamp"], last_capture_excerpt=(raw[:160] + ("…" if len(raw) > 160 else "")) or None,
            latest_observation_id=latest.id if latest else None,
            latest_observation_capture_id=latest.capture_id if latest else None,
            latest_observation_content=bodies[latest.id].content if latest and latest.id in bodies else None,
            understood_self_reports=buckets["understood_self_report"], unresolved_difficulties=buckets["difficulty"],
            unresolved_questions=buckets["open_question"], pending_next_steps=buckets["intended_next_step"],
            unresolved_difficulties_count=counts["difficulty"], unresolved_questions_count=counts["open_question"],
            pending_next_steps_count=counts["intended_next_step"], review_suggested=due, days_since_last_activity=days))
    return checkpoints


def get_topic_continuity_summaries(
    db: Session,
    user_id: int,
    track_id: int | None = None,
    limit: int = 50,
) -> list[TopicContinuityResponse]:
    checkpoints = get_resumable_checkpoints(db, user_id, track_id=track_id, limit=limit)
    summaries = []

    counts = defaultdict(lambda: {"captures": set(), "observations": 0})
    rows = db.query(LearningObservation.topic, LearningCapture.id, LearningCapture.learning_track_id).join(
        LearningCapture, LearningObservation.capture_id == LearningCapture.id).filter(
        LearningObservation.user_id == user_id, LearningCapture.user_id == user_id, LearningCapture.status == "confirmed")
    if track_id is not None:
        rows = rows.filter(LearningCapture.learning_track_id == track_id)
    for topic, capture_id, assigned_track in rows:
        group = counts[(assigned_track, normalize_topic(topic))]
        group["captures"].add(capture_id)
        group["observations"] += 1
    for cp in checkpoints:
        group = counts[(cp.learning_track_id, cp.normalized_topic)]
        c_count, o_count = len(group["captures"]), group["observations"]

        summaries.append(
            TopicContinuityResponse(
                topic=cp.topic,
                normalized_topic=cp.normalized_topic,
                learning_track_id=cp.learning_track_id,
                learning_track_name=cp.learning_track_name,
                state=cp.state,
                confirmed_capture_count=c_count,
                observations_count=o_count,
                difficulties_count=cp.unresolved_difficulties_count,
                unresolved_difficulties_count=cp.unresolved_difficulties_count,
                questions_count=cp.unresolved_questions_count,
                unresolved_questions_count=cp.unresolved_questions_count,
                pending_next_steps_count=cp.pending_next_steps_count,
                last_studied_at=cp.last_capture_at,
                is_review_due=cp.review_suggested,
            )
        )

    return summaries


def generate_evidence_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10,
) -> list[EvidenceRecommendationResponse]:
    checkpoints = get_resumable_checkpoints(db, user_id, limit=50)
    actions_info = get_user_actions(db, user_id)
    completed_rec_ids = actions_info["completed_rec_ids"]
    dismissed_rec_ids = actions_info["dismissed_rec_ids"]

    recommendations: list[EvidenceRecommendationResponse] = []
    seen_topic_types: set[tuple[str, str]] = set()

    def add_rec(rec: EvidenceRecommendationResponse, category_rank: int):
        if rec.id in completed_rec_ids or rec.id in dismissed_rec_ids:
            return
        key = (rec.type, rec.topic.casefold())
        if key in seen_topic_types:
            return
        seen_topic_types.add(key)
        # Attach rank for sorting
        recommendations.append((rec, category_rank))

    now_utc = datetime.now(timezone.utc)

    # 1. Relevant pending user-intended next actions
    for cp in checkpoints:
        for step in cp.pending_next_steps:
            rec_id = f"rec_next_step_{step.id}"
            age_days = (now_utc - step.created_at).days
            priority = "high" if age_days < 7 else "medium"
            add_rec(
                EvidenceRecommendationResponse(
                    id=rec_id,
                    type="intended_next_step",
                    priority=priority,
                    topic=cp.topic,
                    learning_track_id=cp.learning_track_id,
                    learning_track_name=cp.learning_track_name,
                    action=f"Complete your intended next step: {step.content}",
                    reason=f"Based on your confirmed plan from Capture #{step.capture_id}",
                    source_capture_id=step.capture_id,
                    source_observation_id=step.id,
                    evidence=step.evidence,
                    link_url=f"/dashboard/capture?capture={step.capture_id}",
                    status="pending",
                ),
                category_rank=1,
            )

    # 2. Previously reported difficulties and open questions
    for cp in checkpoints:
        for diff in cp.unresolved_difficulties:
            rec_id = f"rec_difficulty_{diff.id}"
            add_rec(
                EvidenceRecommendationResponse(
                    id=rec_id,
                    type="unresolved_difficulty",
                    priority="high",
                    topic=cp.topic,
                    learning_track_id=cp.learning_track_id,
                    learning_track_name=cp.learning_track_name,
                    action=f"Work through reported difficulty with {cp.topic}: {diff.content}",
                    reason=f"You previously recorded this difficulty in Capture #{diff.capture_id}",
                    source_capture_id=diff.capture_id,
                    source_observation_id=diff.id,
                    evidence=diff.evidence,
                    link_url=f"/dashboard/capture?capture={diff.capture_id}",
                    status="pending",
                ),
                category_rank=2,
            )
        for q in cp.unresolved_questions:
            rec_id = f"rec_question_{q.id}"
            add_rec(
                EvidenceRecommendationResponse(
                    id=rec_id,
                    type="open_question",
                    priority="medium",
                    topic=cp.topic,
                    learning_track_id=cp.learning_track_id,
                    learning_track_name=cp.learning_track_name,
                    action=f"Resolve open question about {cp.topic}: {q.content}",
                    reason=f"You noted this open question in Capture #{q.capture_id}",
                    source_capture_id=q.capture_id,
                    source_observation_id=q.id,
                    evidence=q.evidence,
                    link_url=f"/dashboard/capture?capture={q.capture_id}",
                    status="pending",
                ),
                category_rank=3,
            )

    # 3. Useful review suggestions
    for cp in checkpoints:
        if cp.review_suggested:
            track_key = cp.learning_track_id if cp.learning_track_id is not None else "none"
            rec_id = f"rec_review_{track_key}_{cp.normalized_topic}"
            priority = "high" if cp.unresolved_difficulties or cp.days_since_last_activity >= 7 else "medium"
            evidence_snippet = cp.latest_observation_content or cp.last_capture_excerpt or ""
            add_rec(
                EvidenceRecommendationResponse(
                    id=rec_id,
                    type="review_suggestion",
                    priority=priority,
                    topic=cp.topic,
                    learning_track_id=cp.learning_track_id,
                    learning_track_name=cp.learning_track_name,
                    action=f"Review {cp.topic} (last recorded activity {cp.days_since_last_activity} days ago)",
                    reason=f"Scheduled review based on activity interval ({cp.days_since_last_activity} days elapsed)",
                    source_capture_id=cp.latest_observation_capture_id or cp.last_capture_id,
                    source_observation_id=cp.latest_observation_id,
                    evidence=evidence_snippet,
                    review_due_at=cp.last_capture_at,
                    link_url=f"/dashboard/capture?capture={cp.latest_observation_capture_id or cp.last_capture_id}" if cp.last_capture_id else "/dashboard/study-logs",
                    status="pending",
                ),
                category_rank=4,
            )

    # 4. Continue last active learning topic
    if checkpoints:
        most_recent = checkpoints[0]
        # Only suggest continue if no pending next step or difficulty on that checkpoint
        if not most_recent.pending_next_steps and not most_recent.unresolved_difficulties:
            track_key = most_recent.learning_track_id if most_recent.learning_track_id is not None else "none"
            rec_id = f"rec_continue_{track_key}_{most_recent.normalized_topic}"
            add_rec(
                EvidenceRecommendationResponse(
                    id=rec_id,
                    type="continue_learning",
                    priority="low",
                    topic=most_recent.topic,
                    learning_track_id=most_recent.learning_track_id,
                    learning_track_name=most_recent.learning_track_name,
                    action=f"Continue studying {most_recent.topic}",
                    reason=f"Most recently active learning topic ({most_recent.days_since_last_activity} days ago)",
                    source_capture_id=most_recent.latest_observation_capture_id or most_recent.last_capture_id,
                    source_observation_id=most_recent.latest_observation_id,
                    evidence=most_recent.latest_observation_content,
                    link_url=f"/dashboard/capture?capture={most_recent.latest_observation_capture_id or most_recent.last_capture_id}" if most_recent.last_capture_id else "/dashboard/study-logs",
                    status="pending",
                ),
                category_rank=5,
            )

    # 5. Start an existing untouched learning track
    user_tracks = db.query(LearningTrack).filter(LearningTrack.user_id == user_id).all()
    active_tracks = {row[0] for row in db.query(LearningCapture.learning_track_id).filter_by(user_id=user_id, status="confirmed").distinct()}
    active_tracks.update(row[0] for row in db.query(StudyLog.learning_track_id).filter_by(user_id=user_id).distinct())
    for track in user_tracks:
        if track.id not in active_tracks:
            rec_id = f"rec_start_track_{track.id}"
            add_rec(
                EvidenceRecommendationResponse(
                    id=rec_id,
                    type="start_track",
                    priority="low",
                    topic=track.name,
                    learning_track_id=track.id,
                    learning_track_name=track.name,
                    action=f"Start studying your new track: {track.name}",
                    reason="You created this learning track but have not recorded study activity yet",
                    source_capture_id=None,
                    source_observation_id=None,
                    evidence=track.description,
                    link_url="/dashboard/learning-tracks",
                    status="pending",
                ),
                category_rank=6,
            )

    priority_map = {"high": 3, "medium": 2, "low": 1}

    # Deterministic sorting
    recommendations.sort(
        key=lambda item: (
            -priority_map.get(item[0].priority, 0),
            item[1],  # category rank
            item[0].topic.casefold(),
            item[0].id,
        )
    )

    return [item[0] for item in recommendations[:limit]]


def calculate_timezone_streak(db: Session, user_id: int, target_tz: zoneinfo.ZoneInfo) -> int:
    logs = (
        db.query(StudyLog.created_at)
        .filter(StudyLog.user_id == user_id)
        .all()
    )
    if not logs:
        return 0

    study_dates = set()
    for (created_at,) in logs:
        if created_at is None:
            continue
        dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
        user_local_date = dt.astimezone(target_tz).date()
        study_dates.add(user_local_date)

    now_user_date = datetime.now(timezone.utc).astimezone(target_tz).date()
    yesterday_user_date = now_user_date - timedelta(days=1)

    if now_user_date in study_dates:
        current_day = now_user_date
    elif yesterday_user_date in study_dates:
        current_day = yesterday_user_date
    else:
        return 0

    streak = 0
    while current_day in study_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return streak


def get_learning_overview(db: Session, user_id: int, tz_name: str = "UTC") -> LearningOverviewResponse:
    target_tz = validate_timezone(tz_name)
    checkpoints = get_resumable_checkpoints(db, user_id, limit=None, _summary_only=True)

    # Confirmed captures count
    confirmed_captures_count = (
        db.query(func.count(LearningCapture.id))
        .filter(LearningCapture.user_id == user_id, LearningCapture.status == "confirmed")
        .scalar()
        or 0
    )

    # Total logged study hours from actual study logs only (no invented minutes!)
    total_minutes = (
        db.query(func.coalesce(func.sum(StudyLog.duration_minutes), 0))
        .filter(StudyLog.user_id == user_id)
        .scalar()
        or 0
    )
    total_logged_study_hours = round(total_minutes / 60.0, 2)

    # Distinct topics count
    distinct_topics = {cp.normalized_topic for cp in checkpoints if cp.normalized_topic}

    # Observation counts by type from confirmed captures only
    obs_query = (
        db.query(LearningObservation.observation_type, func.count(LearningObservation.id))
        .join(LearningCapture, LearningObservation.capture_id == LearningCapture.id)
        .filter(
            LearningObservation.user_id == user_id,
            LearningCapture.status == "confirmed",
        )
        .group_by(LearningObservation.observation_type)
        .all()
    )
    type_counts = dict(obs_query)

    learned_count = type_counts.get("learned", 0)
    understood_count = type_counts.get("understood_self_report", 0)
    difficulties_count = type_counts.get("difficulty", 0)
    questions_count = type_counts.get("open_question", 0)
    total_observations_count = sum(type_counts.values())

    # Count unresolved from checkpoints
    unresolved_difficulties_count = sum(cp.unresolved_difficulties_count for cp in checkpoints)
    unresolved_questions_count = sum(cp.unresolved_questions_count for cp in checkpoints)
    pending_next_actions_count = sum(cp.pending_next_steps_count for cp in checkpoints)
    review_suggested_count = sum(1 for cp in checkpoints if cp.review_suggested)

    # Latest activity timestamp
    latest_capture_dt = (
        db.query(func.max(LearningCapture.confirmed_at))
        .filter(LearningCapture.user_id == user_id, LearningCapture.status == "confirmed")
        .scalar()
    )
    latest_log_dt = (
        db.query(func.max(StudyLog.created_at))
        .filter(StudyLog.user_id == user_id)
        .scalar()
    )
    latest_activity_at = None
    if latest_capture_dt and latest_log_dt:
        c_dt = latest_capture_dt if latest_capture_dt.tzinfo else latest_capture_dt.replace(tzinfo=timezone.utc)
        l_dt = latest_log_dt if latest_log_dt.tzinfo else latest_log_dt.replace(tzinfo=timezone.utc)
        latest_activity_at = max(c_dt, l_dt)
    elif latest_capture_dt:
        latest_activity_at = latest_capture_dt if latest_capture_dt.tzinfo else latest_capture_dt.replace(tzinfo=timezone.utc)
    elif latest_log_dt:
        latest_activity_at = latest_log_dt if latest_log_dt.tzinfo else latest_log_dt.replace(tzinfo=timezone.utc)

    current_streak = calculate_timezone_streak(db, user_id, target_tz)

    return LearningOverviewResponse(
        confirmed_captures_count=confirmed_captures_count,
        distinct_topics_count=len(distinct_topics),
        total_observations_count=total_observations_count,
        learned_count=learned_count,
        understood_count=understood_count,
        difficulties_count=difficulties_count,
        unresolved_difficulties_count=unresolved_difficulties_count,
        questions_count=questions_count,
        unresolved_questions_count=unresolved_questions_count,
        pending_next_actions_count=pending_next_actions_count,
        total_logged_study_hours=total_logged_study_hours,
        latest_activity_at=latest_activity_at,
        current_streak=current_streak,
        review_suggested_count=review_suggested_count,
        checkpoints_count=len(checkpoints),
    )
