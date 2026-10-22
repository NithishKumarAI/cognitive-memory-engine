from datetime import datetime, timezone, timedelta, date
from sqlalchemy import func
from sqlalchemy.orm import Session
import zoneinfo

from app.models.study_log import StudyLog
from app.services.continuity_service import validate_timezone


def _to_user_date(dt: datetime, tz: zoneinfo.ZoneInfo) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).date()


def get_topic_distribution(db: Session, user_id: int):
    results = (
        db.query(
            StudyLog.topic,
            func.sum(StudyLog.duration_minutes).label("total_minutes"),
            func.count(StudyLog.id).label("session_count"),
        )
        .filter(StudyLog.user_id == user_id)
        .group_by(StudyLog.topic)
        .all()
    )

    return [
        {
            "topic": row.topic,
            "total_minutes": row.total_minutes or 0,
            "total_hours": round((row.total_minutes or 0) / 60.0, 2),
            "session_count": row.session_count,
        }
        for row in results
    ]


def get_study_hours(db: Session, user_id: int):
    total_minutes = (
        db.query(func.coalesce(func.sum(StudyLog.duration_minutes), 0))
        .filter(StudyLog.user_id == user_id)
        .scalar()
        or 0
    )

    return {
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60.0, 2),
    }


def get_overview(db: Session, user_id: int, tz_name: str = "UTC"):
    total_logs = (
        db.query(func.count(StudyLog.id))
        .filter(StudyLog.user_id == user_id)
        .scalar()
        or 0
    )

    total_topics = (
        db.query(func.count(func.distinct(StudyLog.topic)))
        .filter(StudyLog.user_id == user_id)
        .scalar()
        or 0
    )

    total_minutes = (
        db.query(func.coalesce(func.sum(StudyLog.duration_minutes), 0))
        .filter(StudyLog.user_id == user_id)
        .scalar()
        or 0
    )

    streak_data = get_study_streak(db, user_id, tz_name=tz_name)
    consistency_data = get_consistency_score(db, user_id, tz_name=tz_name)

    return {
        "total_study_logs": total_logs,
        "total_topics": total_topics,
        "total_hours": round(total_minutes / 60.0, 2),
        "current_streak": streak_data["current_streak"],
        "consistency_score": consistency_data["consistency_score"],
    }


def get_most_studied_topics(db: Session, user_id: int, limit: int = 5):
    results = (
        db.query(
            StudyLog.topic,
            func.sum(StudyLog.duration_minutes).label("total_minutes"),
        )
        .filter(StudyLog.user_id == user_id)
        .group_by(StudyLog.topic)
        .order_by(func.sum(StudyLog.duration_minutes).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "topic": row.topic,
            "total_minutes": row.total_minutes or 0,
        }
        for row in results
    ]


def get_least_studied_topics(db: Session, user_id: int, limit: int = 5):
    results = (
        db.query(
            StudyLog.topic,
            func.sum(StudyLog.duration_minutes).label("total_minutes"),
        )
        .filter(StudyLog.user_id == user_id)
        .group_by(StudyLog.topic)
        .order_by(func.sum(StudyLog.duration_minutes).asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "topic": row.topic,
            "total_minutes": row.total_minutes or 0,
        }
        for row in results
    ]


def get_daily_activity(db: Session, user_id: int, tz_name: str = "UTC"):
    tz = validate_timezone(tz_name)
    logs = (
        db.query(StudyLog.created_at, StudyLog.duration_minutes)
        .filter(StudyLog.user_id == user_id)
        .order_by(StudyLog.created_at.asc())
        .all()
    )

    activity_by_date: dict[date, int] = {}
    for created_at, duration in logs:
        if created_at is None:
            continue
        d = _to_user_date(created_at, tz)
        activity_by_date[d] = activity_by_date.get(d, 0) + (duration or 0)

    sorted_dates = sorted(activity_by_date.keys())
    return [
        {
            "date": d,
            "study_minutes": activity_by_date[d],
        }
        for d in sorted_dates
    ]


def get_weekly_study_hours(db: Session, user_id: int, tz_name: str = "UTC"):
    tz = validate_timezone(tz_name)
    seven_days_ago_dt = datetime.now(timezone.utc) - timedelta(days=7)
    logs = (
        db.query(StudyLog.created_at, StudyLog.duration_minutes)
        .filter(StudyLog.user_id == user_id)
        .all()
    )

    total_minutes = 0
    for created_at, duration in logs:
        if created_at is None:
            continue
        dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
        if dt >= seven_days_ago_dt:
            total_minutes += duration or 0

    return {
        "period": "last_7_days",
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60.0, 2),
    }


def get_monthly_study_hours(db: Session, user_id: int, tz_name: str = "UTC"):
    tz = validate_timezone(tz_name)
    thirty_days_ago_dt = datetime.now(timezone.utc) - timedelta(days=30)
    logs = (
        db.query(StudyLog.created_at, StudyLog.duration_minutes)
        .filter(StudyLog.user_id == user_id)
        .all()
    )

    total_minutes = 0
    for created_at, duration in logs:
        if created_at is None:
            continue
        dt = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
        if dt >= thirty_days_ago_dt:
            total_minutes += duration or 0

    return {
        "period": "last_30_days",
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60.0, 2),
    }


def get_study_streak(db: Session, user_id: int, tz_name: str = "UTC"):
    tz = validate_timezone(tz_name)
    logs = (
        db.query(StudyLog.created_at)
        .filter(StudyLog.user_id == user_id)
        .all()
    )

    study_dates = set()
    for (created_at,) in logs:
        if created_at is None:
            continue
        study_dates.add(_to_user_date(created_at, tz))

    if not study_dates:
        return {"current_streak": 0}

    now_user_date = datetime.now(timezone.utc).astimezone(tz).date()
    yesterday_user_date = now_user_date - timedelta(days=1)

    if now_user_date in study_dates:
        current_day = now_user_date
    elif yesterday_user_date in study_dates:
        current_day = yesterday_user_date
    else:
        return {"current_streak": 0}

    streak = 0
    while current_day in study_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return {"current_streak": streak}


def get_study_frequency(db: Session, user_id: int, tz_name: str = "UTC"):
    tz = validate_timezone(tz_name)
    today = datetime.now(timezone.utc).astimezone(tz).date()
    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    logs = (
        db.query(StudyLog.created_at)
        .filter(StudyLog.user_id == user_id)
        .all()
    )

    dates_last_7 = set()
    dates_last_30 = set()

    for (created_at,) in logs:
        if created_at is None:
            continue
        d = _to_user_date(created_at, tz)
        if d >= seven_days_ago:
            dates_last_7.add(d)
        if d >= thirty_days_ago:
            dates_last_30.add(d)

    return {
        "study_days_last_7_days": len(dates_last_7),
        "study_days_last_30_days": len(dates_last_30),
    }


def get_consistency_score(db: Session, user_id: int, tz_name: str = "UTC"):
    frequency_data = get_study_frequency(db, user_id, tz_name=tz_name)
    streak_data = get_study_streak(db, user_id, tz_name=tz_name)

    frequency_score = round(
        (frequency_data["study_days_last_30_days"] / 30.0) * 100,
        2,
    )

    streak_score = round(
        (min(streak_data["current_streak"], 30) / 30.0) * 100,
        2,
    )

    consistency_score = round(
        (frequency_score * 0.7) + (streak_score * 0.3),
        2,
    )

    return {
        "current_streak": streak_data["current_streak"],
        "frequency_percentage": frequency_score,
        "consistency_score": consistency_score,
    }


def get_topic_recency(db: Session, user_id: int, tz_name: str = "UTC"):
    tz = validate_timezone(tz_name)
    today = datetime.now(timezone.utc).astimezone(tz).date()

    logs = (
        db.query(StudyLog.topic, StudyLog.created_at)
        .filter(StudyLog.user_id == user_id)
        .all()
    )

    latest_by_topic: dict[str, date] = {}
    for topic, created_at in logs:
        if created_at is None:
            continue
        d = _to_user_date(created_at, tz)
        if topic not in latest_by_topic or d > latest_by_topic[topic]:
            latest_by_topic[topic] = d

    return [
        {
            "topic": topic,
            "last_studied": last_date,
            "days_since_last_study": (today - last_date).days,
        }
        for topic, last_date in latest_by_topic.items()
    ]


def get_neglected_topics(db: Session, user_id: int, tz_name: str = "UTC"):
    topics = get_topic_recency(db, user_id, tz_name=tz_name)
    return sorted(topics, key=lambda x: x["days_since_last_study"], reverse=True)
