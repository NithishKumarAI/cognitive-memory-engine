"""Explicit local .env migration target; no app-URL fallback or destructive shortcuts."""
from check_local import settings, local_url, ROOT
from alembic import command
from alembic.config import Config


def main():
    values = settings()
    try:
        url = local_url(values.get("ALEMBIC_DATABASE_URL"))
        if values.get("ALEMBIC_DATABASE_URL") != values.get("DATABASE_URL"):
            raise ValueError()
    except ValueError:
        print("Set explicit, matching DATABASE_URL and ALEMBIC_DATABASE_URL for a dedicated local database. Target values hidden; remote targets refused.")
        return 1
    import sys
    sys.path.insert(0, str(ROOT))
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False).replace("%", "%%"))
    try:
        command.upgrade(config, "head")
    except Exception:
        print("Local migration failed. Verify the database role, installed pgvector and target configuration. Connection/SQL details hidden.")
        return 1
    print("Local migrations reached head. No reset or stamping performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
