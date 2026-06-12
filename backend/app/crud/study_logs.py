from sqlalchemy.orm import Session

from app.models.study_log import StudyLog
from app.schemas.study_logs import (
    StudyLogCreate,
    StudyLogUpdate
)


def create_study_log(
    db: Session,
    study_log: StudyLogCreate,
    user_id: int
):
    db_study_log = StudyLog(
        topic=study_log.topic,
        duration_minutes=study_log.duration_minutes,
        notes=study_log.notes,
        user_id=user_id
    )

    db.add(db_study_log)
    db.commit()
    db.refresh(db_study_log)

    return db_study_log


def get_user_study_logs(
    db: Session,
    user_id: int
):
    return (
        db.query(StudyLog)
        .filter(StudyLog.user_id == user_id)
        .all()
    )


def get_study_log(
    db: Session,
    study_log_id: int,
    user_id: int
):
    return (
        db.query(StudyLog)
        .filter(
            StudyLog.id == study_log_id,
            StudyLog.user_id == user_id
        )
        .first()
    )

def update_study_log(
    db: Session,
    db_study_log: StudyLog,
    study_log_update: StudyLogUpdate
):
    update_data = study_log_update.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            db_study_log,
            field,
            value
        )

    db.commit()
    db.refresh(db_study_log)

    return db_study_log

def delete_study_log(
    db: Session,
    db_study_log: StudyLog
):
    db.delete(db_study_log)

    db.commit()

    return {
        "message": "Study log deleted successfully"
    }