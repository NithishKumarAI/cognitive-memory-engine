from sqlalchemy.orm import Session

from app.models.learning_track import LearningTrack
from app.schemas.learning_track import (
    LearningTrackCreate,
    LearningTrackUpdate
)


def create_learning_track(
    db: Session,
    track: LearningTrackCreate,
    user_id: int
):
    db_track = LearningTrack(
        **track.model_dump(),
        user_id=user_id
    )

    db.add(db_track)
    db.commit()
    db.refresh(db_track)

    return db_track


def get_learning_track(
    db: Session,
    track_id: int,
    user_id: int
):
    return (
        db.query(LearningTrack)
        .filter(
            LearningTrack.id == track_id,
            LearningTrack.user_id == user_id
        )
        .first()
    )


def get_learning_tracks(
    db: Session,
    user_id: int
):
    return (
        db.query(LearningTrack)
        .filter(
            LearningTrack.user_id == user_id
        )
        .order_by(
            LearningTrack.created_at.desc()
        )
        .all()
    )


def update_learning_track(
    db: Session,
    db_track: LearningTrack,
    track_update: LearningTrackUpdate
):
    update_data = track_update.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            db_track,
            field,
            value
        )

    db.commit()
    db.refresh(db_track)

    return db_track


def delete_learning_track(
    db: Session,
    db_track: LearningTrack
):
    db.delete(db_track)
    db.commit()