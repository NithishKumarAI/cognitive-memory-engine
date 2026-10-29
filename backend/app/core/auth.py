from datetime import datetime, timedelta, UTC

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
import jwt
from jwt import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.db.dependencies import get_db
from app.crud.user import get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)
def create_access_token(
    data: dict
):
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {"exp": expire}
    )

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt

def verify_access_token(
    token: str
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )

        email = payload.get("sub")

        if email is None:
            return None

        return email

    except InvalidTokenError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    email = verify_access_token(token)

    if not email:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user = await run_in_threadpool(get_user_by_email, db, email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    from app.services.ai_credentials import provider_owner
    context = provider_owner.set((user.id, db.get_bind()))
    try:
        yield user
    finally:
        provider_owner.reset(context)
