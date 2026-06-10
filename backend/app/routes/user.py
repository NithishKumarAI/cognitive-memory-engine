from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.user import UserCreate
from app.crud.user import (
    create_user,
    get_users,
    get_user
)

router = APIRouter()


@router.post("/users")
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    return create_user(db, user)

@router.get("/users")
def read_users(
    db: Session = Depends(get_db)
):
    return get_users(db)

@router.get("/users/{user_id}")
def read_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    return get_user(db, user_id)