import os
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
    # Check for existing action with same idempotency key
    existing = (
        db.query(LearningAction)
        .filter(
            LearningAction.user_id == user_id,
            LearningAction.idempotency_key == payload.idempotency_key,
        )
        .first()
    )
    if existing:
        return LearningActionResponse.model_validate(existing)

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

    action = LearningAction(
        user_id=user_id,
        idempotency_key=payload.idempotency_key,
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
    except Exception:
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
            return LearningActionResponse.model_validate(conflict)
        raise

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


def get_resumable_checkpoints(
    db: Session,
    user_id: int,
    track_id: int | None = None,
    limit: int = 20,
) -> list[ResumableCheckpointResponse]:
    actions_info = get_user_actions(db, user_id)
    resolved_obs_ids = actions_info["resolved_obs_ids"]
    dismissed_obs_ids = actions_info["dismissed_obs_ids"]
    recent_reviews = actions_info["recent_reviews"]

    # Query confirmed captures and their observations
    capture_query = (
        db.query(LearningCapture)
        .filter(
            LearningCapture.user_id == user_id,
            LearningCapture.status == "confirmed",
        )
    )
    if track_id is not None:
        capture_query = capture_query.filter(LearningCapture.learning_track_id == track_id)

    confirmed_captures = capture_query.order_by(LearningCapture.confirmed_at.desc(), LearningCapture.id.desc()).all()

    # Preload tracks for display names
    tracks = {t.id: t.name for t in db.query(LearningTrack).filter(LearningTrack.user_id == user_id).all()}

    # Group by (learning_track_id, normalized_topic)
    topic_groups: dict[tuple[int | None, str], dict] = {}

    for cap in confirmed_captures:
        cap_dt = cap.confirmed_at or cap.created_at
        if cap_dt.tzinfo is None:
            cap_dt = cap_dt.replace(tzinfo=timezone.utc)

        observations = (
            db.query(LearningObservation)
            .filter(LearningObservation.capture_id == cap.id, LearningObservation.user_id == user_id)
            .order_by(LearningObservation.position.asc())
            .all()
        )

        # In case a confirmed capture has no individual observations (rare/fallback)
        if not observations:
            interpretation = cap.confirmed_interpretation or {}
            topics = interpretation.get("topics", [])
            subject = interpretation.get("subject")
            all_topics = ([subject] if subject else []) + topics
            for top in all_topics:
                norm = normalize_topic(top)
                key = (cap.learning_track_id, norm)
                if key not in topic_groups:
                    topic_groups[key] = {
                        "display_topic": top,
                        "normalized_topic": norm,
                        "track_id": cap.learning_track_id,
                        "last_capture": cap,
                        "last_capture_at": cap_dt,
                        "observations": [],
                    }
            continue

        for obs in observations:
            norm = normalize_topic(obs.topic)
            key = (cap.learning_track_id, norm)
            if key not in topic_groups:
                topic_groups[key] = {
                    "display_topic": obs.topic,
                    "normalized_topic": norm,
                    "track_id": cap.learning_track_id,
                    "last_capture": cap,
                    "last_capture_at": cap_dt,
                    "observations": [],
                }
            topic_groups[key]["observations"].append(obs)

    # Legacy study logs context for topics without captures or for activity recency
    log_query = db.query(StudyLog).filter(StudyLog.user_id == user_id)
    if track_id is not None:
        log_query = log_query.filter(StudyLog.learning_track_id == track_id)
    legacy_logs = log_query.order_by(StudyLog.created_at.desc()).all()

    for log in legacy_logs:
        norm = normalize_topic(log.topic)
        key = (log.learning_track_id, norm)
        log_dt = log.created_at
        if log_dt.tzinfo is None:
            log_dt = log_dt.replace(tzinfo=timezone.utc)
        if key not in topic_groups:
            # Topic encountered only in legacy logs
            topic_groups[key] = {
                "display_topic": log.topic,
                "normalized_topic": norm,
                "track_id": log.learning_track_id,
                "last_capture": None,
                "last_capture_at": log_dt,
                "observations": [],
            }
        else:
            # Update last activity if log is newer
            if log_dt > topic_groups[key]["last_capture_at"]:
                topic_groups[key]["last_capture_at"] = log_dt

    now_utc = datetime.now(timezone.utc)
    checkpoints = []

    for key, data in topic_groups.items():
        track_id_val, norm = key
        observations = data["observations"]
        last_cap = data["last_capture"]
        last_dt = data["last_capture_at"]

        days_since_activity = max(0, (now_utc - last_dt).days)

        understood_briefs = []
        unresolved_difficulties = []
        unresolved_questions = []
        pending_next_steps = []

        latest_obs_id = None
        latest_obs_content = None

        if observations:
            # observations are collected newest capture first
            latest_obs = observations[0]
            latest_obs_id = latest_obs.id
            latest_obs_content = latest_obs.content

            for obs in observations:
                dt = obs.created_at
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                is_res = obs.id in resolved_obs_ids
                is_dism = obs.id in dismissed_obs_ids

                brief = ObservationBrief(
                    id=obs.id,
                    observation_type=obs.observation_type,
                    topic=obs.topic,
                    content=obs.content,
                    evidence=obs.evidence,
                    capture_id=obs.capture_id,
                    is_resolved=is_res,
                    is_completed=is_res,
                    is_dismissed=is_dism,
                    created_at=dt,
                )

                if obs.observation_type == "understood_self_report":
                    understood_briefs.append(brief)
                elif obs.observation_type == "difficulty":
                    if not is_res and not is_dism:
                        unresolved_difficulties.append(brief)
                elif obs.observation_type == "open_question":
                    if not is_res and not is_dism:
                        unresolved_questions.append(brief)
                elif obs.observation_type == "intended_next_step":
                    if not is_res and not is_dism:
                        pending_next_steps.append(brief)

        # Check review eligibility
        last_review_dt = recent_reviews.get(key)
        days_since_review = (now_utc - last_review_dt).days if last_review_dt else None
        
        # Topic is review-suggested if >= REVIEW_INITIAL_INTERVAL_DAYS since activity
        # and not reviewed within REVIEW_INITIAL_INTERVAL_DAYS
        is_review_due = (
            days_since_activity >= REVIEW_INITIAL_INTERVAL_DAYS
            and (days_since_review is None or days_since_review >= REVIEW_INITIAL_INTERVAL_DAYS)
            and len(observations) > 0
        )

        # Derive state
        if unresolved_difficulties or unresolved_questions:
            state: Literal["recorded", "exploring", "self_reported_understood", "needs_attention", "review_suggested", "insufficient_evidence"] = "needs_attention"
        elif is_review_due:
            state = "review_suggested"
        elif understood_briefs:
            state = "self_reported_understood"
        elif days_since_activity < 7 and observations:
            state = "exploring"
        elif observations or last_cap or legacy_logs:
            state = "recorded"
        else:
            state = "insufficient_evidence"

        excerpt = None
        if last_cap:
            raw = last_cap.original_text.strip()
            excerpt = (raw[:160] + "...") if len(raw) > 160 else raw

        checkpoints.append(
            ResumableCheckpointResponse(
                topic=data["display_topic"],
                normalized_topic=norm,
                learning_track_id=track_id_val,
                learning_track_name=tracks.get(track_id_val),
                state=state,
                last_capture_id=last_cap.id if last_cap else None,
                last_capture_at=last_dt,
                last_capture_excerpt=excerpt,
                latest_observation_id=latest_obs_id,
                latest_observation_content=latest_obs_content,
                understood_self_reports=understood_briefs,
                unresolved_difficulties=unresolved_difficulties,
                unresolved_questions=unresolved_questions,
                pending_next_steps=pending_next_steps,
                review_suggested=is_review_due,
                days_since_last_activity=days_since_activity,
            )
        )

    # Sort checkpoints by last_capture_at descending
    checkpoints.sort(key=lambda c: c.last_capture_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return checkpoints[:limit]


def get_topic_continuity_summaries(
    db: Session,
    user_id: int,
    track_id: int | None = None,
    limit: int = 50,
) -> list[TopicContinuityResponse]:
    checkpoints = get_resumable_checkpoints(db, user_id, track_id=track_id, limit=limit)
    summaries = []

    # Get total capture counts per topic
    for cp in checkpoints:
        norm = cp.normalized_topic
        # Count confirmed captures for this topic
        captures_count = (
            db.query(func.count(func.distinct(LearningCapture.id)))
            .join(LearningObservation, LearningObservation.capture_id == LearningCapture.id)
            .filter(
                LearningCapture.user_id == user_id,
                LearningCapture.status == "confirmed",
                func.lower(LearningObservation.topic) == norm,
            )
        )
        if cp.learning_track_id is not None:
            captures_count = captures_count.filter(LearningCapture.learning_track_id == cp.learning_track_id)
        c_count = captures_count.scalar() or 0

        # Total observations for this topic
        obs_count = (
            db.query(func.count(LearningObservation.id))
            .join(LearningCapture, LearningObservation.capture_id == LearningCapture.id)
            .filter(
                LearningObservation.user_id == user_id,
                LearningCapture.status == "confirmed",
                func.lower(LearningObservation.topic) == norm,
            )
        )
        if cp.learning_track_id is not None:
            obs_count = obs_count.filter(LearningCapture.learning_track_id == cp.learning_track_id)
        o_count = obs_count.scalar() or 0

        summaries.append(
            TopicContinuityResponse(
                topic=cp.topic,
                normalized_topic=cp.normalized_topic,
                learning_track_id=cp.learning_track_id,
                learning_track_name=cp.learning_track_name,
                state=cp.state,
                confirmed_capture_count=c_count,
                observations_count=o_count,
                difficulties_count=len(cp.unresolved_difficulties),
                unresolved_difficulties_count=len(cp.unresolved_difficulties),
                questions_count=len(cp.unresolved_questions),
                unresolved_questions_count=len(cp.unresolved_questions),
                pending_next_steps_count=len(cp.pending_next_steps),
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
                    link_url="/dashboard/capture",
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
                    link_url="/dashboard/capture",
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
                    link_url="/dashboard/capture",
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
                    action=f"Review {cp.topic} (last studied {cp.days_since_last_activity} days ago)",
                    reason=f"Scheduled review based on activity interval ({cp.days_since_last_activity} days elapsed)",
                    source_capture_id=cp.last_capture_id,
                    source_observation_id=cp.latest_observation_id,
                    evidence=evidence_snippet,
                    review_due_at=cp.last_capture_at,
                    link_url="/dashboard/capture",
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
                    source_capture_id=most_recent.last_capture_id,
                    source_observation_id=most_recent.latest_observation_id,
                    evidence=most_recent.latest_observation_content,
                    link_url="/dashboard/capture",
                    status="pending",
                ),
                category_rank=5,
            )

    # 5. Start an existing untouched learning track
    user_tracks = db.query(LearningTrack).filter(LearningTrack.user_id == user_id).all()
    for track in user_tracks:
        cap_count = db.query(LearningCapture).filter(LearningCapture.user_id == user_id, LearningCapture.learning_track_id == track.id).count()
        log_count = db.query(StudyLog).filter(StudyLog.user_id == user_id, StudyLog.learning_track_id == track.id).count()
        if cap_count == 0 and log_count == 0:
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
    checkpoints = get_resumable_checkpoints(db, user_id, limit=100)

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
    unresolved_difficulties_count = sum(len(cp.unresolved_difficulties) for cp in checkpoints)
    unresolved_questions_count = sum(len(cp.unresolved_questions) for cp in checkpoints)
    pending_next_actions_count = sum(len(cp.pending_next_steps) for cp in checkpoints)
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
