import os

from dotenv import load_dotenv

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 720)
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "30000"))

# Operational kill switches, not distributed quotas. Defaults preserve existing deployments.
REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "true").lower() == "true"
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

# Trusted backend configuration. Browser flags never select an edition.
APP_EDITION = os.getenv("APP_EDITION", "product")
if APP_EDITION not in ("product", "demo"):
    raise RuntimeError("APP_EDITION must be product or demo")
AI_KEY_ENCRYPTION_KEYS = os.getenv("AI_KEY_ENCRYPTION_KEYS", "")
DEMO_STORAGE_ENABLED = os.getenv("DEMO_STORAGE_ENABLED", "false").lower() == "true"
DEMO_SECRET_KEY = os.getenv("DEMO_SECRET_KEY", "")
