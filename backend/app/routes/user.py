from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.user import UserCreate
from app.crud.user import (
    create_user,
    get_users,
    get_user
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
    return get_users(db)

@router.get(
    "/users/{user_id}",
    response_model=UserResponse
)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user(db, user_id)

@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_email = get_user_by_email(
        db,
        user.email
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    existing_username = get_user_by_username(
        db,
        user.username
    )

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    return create_user(
        db,
        user
    )

@router.post(
    "/login",
    response_model=Token
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        credentials.email,
        credentials.password
    )

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