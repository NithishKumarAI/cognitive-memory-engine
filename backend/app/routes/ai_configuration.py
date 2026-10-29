from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, SecretStr, Field
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core import config
from app.db.dependencies import get_db
from app.models.ai_credential import AICredential
from app.services.ai_credentials import cipher, encrypt

router = APIRouter(prefix="/settings/ai", tags=["AI configuration"])


class KeyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr = Field(min_length=20, max_length=256)


def product_only():
    if config.APP_EDITION != "product":
        raise HTTPException(403, "Personal keys are unavailable in the demo")


@router.get("")
def status(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if config.APP_EDITION == "demo":
        return {"configured": False, "available": False, "storage_ready": False, "edition": "demo"}
    try:
        cipher()
        ready = True
    except Exception:
        ready = False
    configured = db.get(AICredential, user.id) is not None
    return {"configured": configured, "storage_ready": ready,
            "available": configured and ready and config.AI_ENABLED, "edition": "product"}


@router.put("")
def save(payload: KeyInput, db: Session = Depends(get_db), user=Depends(get_current_user)):
    product_only()
    key = payload.api_key.get_secret_value().strip()
    if len(key) < 20 or any(character.isspace() for character in key):
        raise HTTPException(422, "Enter a valid Gemini API key")
    try:
        encrypted = encrypt(user.id, key)
    except Exception:
        raise HTTPException(503, "Secure key storage is not configured by the operator") from None
    record = db.get(AICredential, user.id)
    if record:
        record.encrypted_key = encrypted
    else:
        db.add(AICredential(user_id=user.id, encrypted_key=encrypted))
    db.commit()
    return {"configured": True}


@router.delete("")
def remove(db: Session = Depends(get_db), user=Depends(get_current_user)):
    product_only()
    record = db.get(AICredential, user.id)
    if record:
        db.delete(record)
        db.commit()
    return {"configured": False}
