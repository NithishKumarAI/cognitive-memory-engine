from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.core.auth import get_current_user

from app.models.user import User

from app.schemas.memory import (
    MemoryCreate,
    MemoryUpdate,
    MemoryResponse
)

from app.crud.memory import (
    create_memory,
    get_memory_by_id,
    get_user_memories,
    update_memory,
    delete_memory
)
from app.crud.study_logs import get_study_log

router = APIRouter(
    prefix="/memories",
    tags=["Memories"]
)

@router.post(
    "",
    response_model=MemoryResponse
)
def create_new_memory(
    memory: MemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if memory.study_log_id is not None:

        study_log = get_study_log(
            db=db,
            study_log_id=memory.study_log_id,
            user_id=current_user.id
        )

        if not study_log:
            raise HTTPException(
                status_code=400,
                detail="Invalid study_log_id"
            )

    return create_memory(
        db=db,
        memory=memory,
        user_id=current_user.id
    )

@router.get(
    "",
    response_model=List[MemoryResponse]
)
def get_my_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_memories(
        db,
        current_user.id
    )

@router.get(
    "/{memory_id}",
    response_model=MemoryResponse
)
def get_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    memory = get_memory_by_id(
        db,
        memory_id
    )

    if not memory:
        raise HTTPException(
            status_code=404,
            detail="Memory not found"
        )

    if memory.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return memory

@router.put(
    "/{memory_id}",
    response_model=MemoryResponse
)
def update_existing_memory(
    memory_id: int,
    memory_update: MemoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    memory = get_memory_by_id(
        db,
        memory_id
    )

    if not memory:
        raise HTTPException(
            status_code=404,
            detail="Memory not found"
        )

    if memory.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    return update_memory(
        db,
        memory,
        memory_update
    )

@router.delete(
    "/{memory_id}"
)
def delete_existing_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    memory = get_memory_by_id(
        db,
        memory_id
    )

    if not memory:
        raise HTTPException(
            status_code=404,
            detail="Memory not found"
        )

    if memory.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    delete_memory(
        db,
        memory
    )

    return {
        "message": "Memory deleted successfully"
    }