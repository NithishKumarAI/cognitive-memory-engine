from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

from app.models.study_log import StudyLog


def get_topic_distribution(
        db: Session,
        user_id: int
):
    results = (
        db.query(
            StudyLog.topic,
            func.sum(
                StudyLog.duration_minutes
            ).label("total_minutes"),
            func.count(
                StudyLog.id
            ).label("session_count")
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .group_by(
            StudyLog.topic
        )
        .all()
    )

    return [
        {
            "topic": row.topic,
            "total_minutes": row.total_minutes,
            "total_hours": round(
                row.total_minutes / 60,
                2
            ),
            "session_count": row.session_count
        }
        for row in results
    ]


def get_study_hours(
        db: Session,
        user_id: int
):
    total_minutes = (
        db.query(
            func.coalesce(
                func.sum(
                    StudyLog.duration_minutes
                ),
                0
            )
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .scalar()
    )

    return {
        "total_minutes": total_minutes,
        "total_hours": round(
            total_minutes / 60,
            2
        )
    }


def get_overview(
        db: Session,
        user_id: int
):
    total_logs = (
        db.query(
            func.count(
                StudyLog.id
            )
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .scalar()
    )

    total_topics = (
        db.query(
            func.count(
                func.distinct(
                    StudyLog.topic
                )
            )
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .scalar()
    )

    total_minutes = (
        db.query(
            func.coalesce(
                func.sum(
                    StudyLog.duration_minutes
                ),
                0
            )
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .scalar()
    )
    streak_data = get_study_streak(
        db,
        user_id
    )

    consistency_data = get_consistency_score(
        db,
        user_id
    )

    return {
        "total_study_logs": total_logs,

        "total_topics": total_topics,

        "total_hours": round(
            total_minutes / 60,
            2
        ),

        "current_streak":
            streak_data["current_streak"],

        "consistency_score":
            consistency_data["consistency_score"]
    }

def get_most_studied_topics(
        db,
        user_id,
        limit: int = 5
):
    results = (
        db.query(
            StudyLog.topic,
            func.sum(
                StudyLog.duration_minutes
            ).label("total_minutes")
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .group_by(
            StudyLog.topic
        )
        .order_by(
            func.sum(
                StudyLog.duration_minutes
            ).desc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "topic": row.topic,
            "total_minutes": row.total_minutes
        }
        for row in results
    ]


def get_least_studied_topics(
        db,
        user_id,
        limit: int = 5
):
    results = (
        db.query(
            StudyLog.topic,
            func.sum(
                StudyLog.duration_minutes
            ).label("total_minutes")
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .group_by(
            StudyLog.topic
        )
        .order_by(
            func.sum(
                StudyLog.duration_minutes
            ).asc()
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "topic": row.topic,
            "total_minutes": row.total_minutes
        }
        for row in results
    ]
def get_daily_activity(
        db,
        user_id
):
    results = (
        db.query(
            cast(
                StudyLog.created_at,
                Date
            ).label("study_date"),
            func.sum(
                StudyLog.duration_minutes
            ).label("total_minutes")
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .group_by(
            cast(
                StudyLog.created_at,
                Date
            )
        )
        .order_by(
            cast(
                StudyLog.created_at,
                Date
            )
        )
        .all()
    )

    return [
        {
            "date": row.study_date,
            "study_minutes": row.total_minutes
        }
        for row in results
    ]

def get_weekly_study_hours(
        db,
        user_id
):
    seven_days_ago = (
        datetime.now() - timedelta(days=7)
    )

    total_minutes = (
        db.query(
            func.coalesce(
                func.sum(
                    StudyLog.duration_minutes
                ),
                0
            )
        )
        .filter(
            StudyLog.user_id == user_id,
            StudyLog.created_at >= seven_days_ago
        )
        .scalar()
    )

    return {
        "period": "last_7_days",
        "total_minutes": total_minutes,
        "total_hours": round(
            total_minutes / 60,
            2
        )
    }

def get_monthly_study_hours(
        db,
        user_id
):
    thirty_days_ago = (
        datetime.now() - timedelta(days=30)
    )

    total_minutes = (
        db.query(
            func.coalesce(
                func.sum(
                    StudyLog.duration_minutes
                ),
                0
            )
        )
        .filter(
            StudyLog.user_id == user_id,
            StudyLog.created_at >= thirty_days_ago
        )
        .scalar()
    )

    return {
        "period": "last_30_days",
        "total_minutes": total_minutes,
        "total_hours": round(
            total_minutes / 60,
            2
        )
    }

def get_study_streak(
        db,
        user_id
):
    study_dates = (
        db.query(
            cast(
                StudyLog.created_at,
                Date
            )
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .distinct()
        .all()
    )

    study_dates = {
        row[0]
        for row in study_dates
    }

    if not study_dates:
        return {
            "current_streak": 0
        }

    today = date.today()
    yesterday = today - timedelta(days=1)

    if today in study_dates:
        current_day = today
    elif yesterday in study_dates:
        current_day = yesterday
    else:
        return {
            "current_streak": 0
        }

    streak = 0

    while current_day in study_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return {
        "current_streak": streak
    }

def get_study_frequency(
        db,
        user_id
):
    today = date.today()

    seven_days_ago = today - timedelta(days=7)
    thirty_days_ago = today - timedelta(days=30)

    study_days_last_7_days = (
        db.query(
            cast(
                StudyLog.created_at,
                Date
            )
        )
        .filter(
            StudyLog.user_id == user_id,
            StudyLog.created_at >= seven_days_ago
        )
        .distinct()
        .count()
    )

    study_days_last_30_days = (
        db.query(
            cast(
                StudyLog.created_at,
                Date
            )
        )
        .filter(
            StudyLog.user_id == user_id,
            StudyLog.created_at >= thirty_days_ago
        )
        .distinct()
        .count()
    )

    return {
        "study_days_last_7_days":
            study_days_last_7_days,
        "study_days_last_30_days":
            study_days_last_30_days
    }

def get_consistency_score(
        db,
        user_id
):
    frequency_data = get_study_frequency(
        db,
        user_id
    )

    streak_data = get_study_streak(
        db,
        user_id
    )

    frequency_score = round(
        (
            frequency_data[
                "study_days_last_30_days"
            ] / 30
        ) * 100,
        2
    )

    streak_score = round(
        (
            min(
                streak_data[
                    "current_streak"
                ],
                30
            ) / 30
        ) * 100,
        2
    )

    consistency_score = round(
        (
            frequency_score * 0.7
        ) +
        (
            streak_score * 0.3
        ),
        2
    )

    return {
        "current_streak":
            streak_data["current_streak"],

        "frequency_percentage":
            frequency_score,

        "consistency_score":
            consistency_score
    }

def get_topic_recency(
        db,
        user_id
):
    today = date.today()

    results = (
        db.query(
            StudyLog.topic,
            func.max(
                cast(
                    StudyLog.created_at,
                    Date
                )
            ).label(
                "last_studied"
            )
        )
        .filter(
            StudyLog.user_id == user_id
        )
        .group_by(
            StudyLog.topic
        )
        .all()
    )

    return [
        {
            "topic": row.topic,

            "last_studied":
                row.last_studied,

            "days_since_last_study":
                (
                        today -
                        row.last_studied
                ).days
        }
        for row in results
    ]

def get_neglected_topics(
        db,
        user_id
):
    topics = get_topic_recency(
        db,
        user_id
    )

    return sorted(
        topics,
        key=lambda x: x[
            "days_since_last_study"
        ],
        reverse=True
    )