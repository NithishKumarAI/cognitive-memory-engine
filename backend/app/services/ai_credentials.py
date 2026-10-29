"""Owner-bound encryption; no secrets returned to the browser or logs."""
import json
from contextvars import ContextVar
from cryptography.fernet import Fernet, MultiFernet
from sqlalchemy.orm import Session
from app.core import config
from app.models.ai_credential import AICredential

# Context is installed by an async auth dependency and copied into worker threads.
# Store identity/bind, never a process-global user's decrypted key.
provider_owner = ContextVar("provider_owner", default=None)


def cipher():
    keys = [key.strip() for key in config.AI_KEY_ENCRYPTION_KEYS.split(",") if key.strip()]
    if not keys:
        raise ValueError("Credential encryption is not configured")
    return MultiFernet([Fernet(key.encode()) for key in keys])


def encrypt(user_id, key):
    return cipher().encrypt(json.dumps({"owner": user_id, "key": key}).encode()).decode()


def personal_key():
    owner = provider_owner.get()
    if not owner:
        return None
    user_id, bind = owner
    with Session(bind) as db:
        record = db.get(AICredential, user_id)
        if not record:
            return None
        data = json.loads(cipher().decrypt(record.encrypted_key.encode()))
        if data.get("owner") != user_id:
            raise ValueError("Credential owner mismatch")
        return data["key"]
