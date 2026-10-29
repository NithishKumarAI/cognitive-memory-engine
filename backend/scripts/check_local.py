"""Local-only configuration readiness. Never prints settings, credentials or SQL errors."""
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def settings():
    values = {} if os.environ.get("PYTHON_DOTENV_DISABLED") == "1" else dotenv_values(ROOT / ".env")
    return {**values, **os.environ}


def local_url(value):
    try:
        url = make_url(value or "")
        if url.get_backend_name() != "postgresql" or url.host not in ("127.0.0.1", "localhost") or not url.database or url.database in ("postgres", "template0", "template1"):
            raise ValueError()
        return url
    except Exception:
        raise ValueError("Use an explicit dedicated loopback PostgreSQL database. Remote targets are refused by this local helper.") from None


def main():
    values = settings()
    failures = []
    for key in ("DATABASE_URL", "ALEMBIC_DATABASE_URL"):
        try: local_url(values.get(key))
        except ValueError: failures.append(f"{key}: needs a dedicated local PostgreSQL URL")
    if values.get("DATABASE_URL") != values.get("ALEMBIC_DATABASE_URL"):
        failures.append("The app and migration URLs must name the same local development database")
    secret = values.get("SECRET_KEY") or ""
    if len(secret) < 32 or "replace" in secret.lower(): failures.append("SECRET_KEY: supply your own random value of at least 32 characters")
    if values.get("AI_ENABLED", "true").lower() == "true" and (not values.get("GEMINI_API_KEY") or "replace" in values["GEMINI_API_KEY"].lower()):
        failures.append("GEMINI_API_KEY: configure your own key or use AI_ENABLED=false")
    if not values.get("FRONTEND_ORIGINS"): failures.append("FRONTEND_ORIGINS: configure your browser origin")
    if failures:
        print("Local setup needs attention (values hidden):")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("Local configuration present. Values hidden; no provider calls.")
    if "--database" in sys.argv:
        from sqlalchemy import create_engine, text
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        try:
            engine = create_engine(local_url(values["DATABASE_URL"]), connect_args={"connect_timeout": 3})
            try:
                with engine.connect() as connection:
                    assert connection.execute(text("SELECT 1")).scalar_one() == 1
                    assert connection.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector'")).scalar() == 1
                    assert connection.execute(text("SELECT to_regclass('users')")).scalar() is not None
                    revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                    config = Config(str(ROOT / "alembic.ini"))
                    config.set_main_option("script_location", str(ROOT / "alembic"))
                    assert revision == ScriptDirectory.from_config(config).get_current_head()
            finally: engine.dispose()
        except Exception:
            print("Database/schema not ready. Check the local service, pgvector and migrations. Details hidden.")
            return 1
        print("Local database reachable; pgvector, users table and migration head verified (read-only).")
    else:
        print("Database not checked. Add --database after initializing the dedicated local database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
