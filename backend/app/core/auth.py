from datetime import datetime, timedelta, UTC

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core import config
import jwt
from jwt import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer

from fastapi import Depends, HTTPException, Request
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
        demo = config.APP_EDITION == "demo"
        payload = jwt.decode(
            token,
            config.DEMO_SECRET_KEY if demo else SECRET_KEY,
            algorithms=["HS256" if demo else ALGORITHM],
            audience="learntrack-demo" if demo else None,
            options={"require": ["exp", "sub"]},
        )

        email = payload.get("sub")

        if demo and payload.get("edition") != "demo" or not demo and payload.get("edition") == "demo":
            return None

        if email is None:
            return None

        return email

    except InvalidTokenError:
        return None

async def get_current_user(
    request: Request,
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

    if config.APP_EDITION == "demo":
        from app.services.demo_service import valid_guest
        if not await run_in_threadpool(valid_guest, db, user.id):
            raise HTTPException(401, "Demo session expired; start a new demo")
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.url.path != "/demo/reset":
            from app.services.demo_service import reserve_mutation
            await run_in_threadpool(reserve_mutation, db, user.id)

    from app.services.ai_credentials import provider_owner
    context = provider_owner.set((user.id, db.get_bind()))
    try:
        yield user
    finally:
        provider_owner.reset(context)
