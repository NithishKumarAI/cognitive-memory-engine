from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.core.auth import get_current_user
from app.models.user import User

from app.schemas.study_logs import (
    StudyLogCreate,
    StudyLogUpdate,
    StudyLogResponse
)

from app.crud.study_logs import (
    create_study_log,
    get_user_study_logs,
    get_study_log,
    update_study_log,
    delete_study_log
)


router = APIRouter(
    prefix="/study-logs",
    tags=["Study Logs"]
)


@router.post(
    "/",
    response_model=StudyLogResponse
)
def create_new_study_log(
    study_log: StudyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_study_log(
        db=db,
        study_log=study_log,
        user_id=current_user.id
    )
@router.get(
    "/",
    response_model=list[StudyLogResponse]
)
def read_my_study_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_study_logs(
        db=db,
        user_id=current_user.id
    )

@router.get(
    "/{study_log_id}",
    response_model=StudyLogResponse
)
def read_study_log(
    study_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    study_log = get_study_log(
        db=db,
        study_log_id=study_log_id,
        user_id=current_user.id
    )

    if not study_log:
        raise HTTPException(
            status_code=404,
            detail="Study log not found"
        )

    return study_log

@router.put(
    "/{study_log_id}",
    response_model=StudyLogResponse
)
def update_user_study_log(
    study_log_id: int,
    study_log_update: StudyLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    study_log = get_study_log(
        db=db,
        study_log_id=study_log_id,
        user_id=current_user.id
    )

    if not study_log:
        raise HTTPException(
            status_code=404,
            detail="Study log not found"
        )

    return update_study_log(
        db=db,
        db_study_log=study_log,
        study_log_update=study_log_update
    )

@router.delete(
    "/{study_log_id}"
)
def delete_user_study_log(
    study_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    study_log = get_study_log(
        db=db,
        study_log_id=study_log_id,
        user_id=current_user.id
    )

    if not study_log:
        raise HTTPException(
            status_code=404,
            detail="Study log not found"
        )

    return delete_study_log(
        db=db,
        db_study_log=study_log
    )