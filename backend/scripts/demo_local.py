"""Separate explicit local demo configuration; never reads/writes product .env."""
import argparse
import os
import sys
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["check", "migrate", "serve", "cleanup"])
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env.demo.local")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    values = {key: value for key, value in dotenv_values(args.env_file).items() if value is not None}
    try:
        from check_local import local_url
        url = local_url(values.get("DATABASE_URL"))
        if (values.get("APP_EDITION") != "demo" or values.get("DEMO_STORAGE_ENABLED") != "true"
                or values.get("DATABASE_URL") != values.get("ALEMBIC_DATABASE_URL")
                or not url.database.endswith("_demo") or not 1 <= args.port <= 65535
                or "replace" in values.get("DEMO_SECRET_KEY", "").lower()):
            raise ValueError()
        os.environ.update(values)
        os.environ["PYTHON_DOTENV_DISABLED"] = "1"
        sys.path.insert(0, str(ROOT))
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session
        from app.services.demo_service import require_demo_storage, purge_expired
        engine = create_engine(url)
        require_demo_storage(engine)
        if args.action == "migrate":
            from alembic import command
            from alembic.config import Config
            configuration = Config(str(ROOT / "alembic.ini"))
            configuration.set_main_option("script_location", str(ROOT / "alembic"))
            configuration.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False).replace("%", "%%"))
            command.upgrade(configuration, "head")
            print("Demo migrations reached head; existing databases were not reset.")
        elif args.action == "check":
            with engine.connect() as connection:
                assert connection.scalar(text("SELECT 1")) == 1
                assert connection.scalar(text("SELECT count(*) FROM demo_budget WHERE id=1")) == 1
            print("Explicit separate demo storage is reachable. Live AI is disabled.")
        elif args.action == "cleanup":
            with Session(engine) as db:
                print(f"Expired demo sessions removed: {purge_expired(db)}")
        else:
            engine.dispose()
            import uvicorn
            uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, proxy_headers=False)
        engine.dispose()
        return 0
    except Exception:
        print("Demo configuration/storage is not ready. Check the separate demo env file, distinct secret, database role and migrations. Private details hidden.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
