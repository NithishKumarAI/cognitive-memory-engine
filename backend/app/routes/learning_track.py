from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.core.auth import get_current_user

from app.models.user import User

from app.schemas.learning_track import (
    LearningTrackCreate,
    LearningTrackUpdate,
    LearningTrackResponse
)

from app.crud.learning_track import (
    create_learning_track,
    get_learning_track,
    get_learning_tracks,
    update_learning_track,
    delete_learning_track
)

router = APIRouter(
    prefix="/learning-tracks",
    tags=["Learning Tracks"]
)


@router.post(
    "",
    response_model=LearningTrackResponse,
    status_code=status.HTTP_201_CREATED
)
def create_track(
    track: LearningTrackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_learning_track(
        db=db,
        track=track,
        user_id=current_user.id
    )


@router.get(
    "",
    response_model=List[LearningTrackResponse]
)
def list_tracks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_learning_tracks(
        db=db,
        user_id=current_user.id
    )


@router.get(
    "/{track_id}",
    response_model=LearningTrackResponse
)
def get_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    track = get_learning_track(
        db=db,
        track_id=track_id,
        user_id=current_user.id
    )

    if not track:
        raise HTTPException(
            status_code=404,
            detail="Learning track not found"
        )

    return track


@router.put(
    "/{track_id}",
    response_model=LearningTrackResponse
)
def update_track(
    track_id: int,
    track_update: LearningTrackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_track = get_learning_track(
        db=db,
        track_id=track_id,
        user_id=current_user.id
    )

    if not db_track:
        raise HTTPException(
            status_code=404,
            detail="Learning track not found"
        )

    return update_learning_track(
        db=db,
        db_track=db_track,
        track_update=track_update
    )


@router.delete(
    "/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_track = get_learning_track(
        db=db,
        track_id=track_id,
        user_id=current_user.id
    )

    if not db_track:
        raise HTTPException(
            status_code=404,
            detail="Learning track not found"
        )

    delete_learning_track(
        db=db,
        db_track=db_track
    )