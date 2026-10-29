from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.dependencies import get_db
from app.schemas.user import UserCreate
from app.crud.user import (
    create_user,
)
from fastapi import HTTPException

from app.schemas.user import UserCreate, UserResponse
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.schemas.user import UserLogin
from app.crud.user import authenticate_user

from app.schemas.user import Token
from app.core.auth import create_access_token
from app.core.config import REGISTRATION_ENABLED
from app.core import config

from app.core.auth import get_current_user
from app.models.user import User
router = APIRouter()


#@router.post("/users")
#def create_new_user(
#    user: UserCreate,
#   db: Session = Depends(get_db)
#):
#   return create_user(db, user)
@router.get(
    "/users",
    response_model=list[UserResponse]
)
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return [current_user]

@router.get(
    "/users/{user_id}",
    response_model=UserResponse
)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=404, detail="User not found")
    return current_user

@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    if config.APP_EDITION == "demo" or not REGISTRATION_ENABLED:
        raise HTTPException(403, "Registration is currently closed")

    try:
        if get_user_by_email(db, user.email):
            raise HTTPException(400, "Email already registered")
        if get_user_by_username(db, user.username):
            raise HTTPException(400, "Username already exists")
        return create_user(db, user)
    except IntegrityError:
        # A concurrent request can win after the preflight checks. No duplicate insert.
        db.rollback()
        try:
            if get_user_by_email(db, user.email):
                raise HTTPException(400, "Email already registered")
            if get_user_by_username(db, user.username):
                raise HTTPException(400, "Username already exists")
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(503, "Account service unavailable") from None
        raise HTTPException(409, "Account conflict; try signing in or use different details") from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Account service unavailable") from None

@router.post(
    "/login",
    response_model=Token
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    if config.APP_EDITION == "demo":
        raise HTTPException(403, "Use a temporary demo session")
    try:
        user = authenticate_user(db, credentials.email, credentials.password)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Account service unavailable") from None

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(
        get_current_user
    )
):
    return current_user
