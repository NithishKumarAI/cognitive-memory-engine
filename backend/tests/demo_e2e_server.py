"""Disposable demo browser server. Real migrations and engine; no live provider."""
import os
import sys
import atexit
from pathlib import Path
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

value = os.environ.get("PHASE_DEMO_TEST_DATABASE_URL")
if not value:
    raise RuntimeError("Explicit disposable demo test database is required")
url = make_url(value)
if url.get_backend_name() != "postgresql" or url.host not in ("127.0.0.1", "localhost") or url.database != "cme_verification_demo":
    raise RuntimeError("Demo browser tests require the disposable loopback cme_verification_demo database")
schema = "demo_e2e_" + uuid4().hex
admin = create_engine(url)
with admin.begin() as connection:
    connection.execute(text(f'CREATE SCHEMA "{schema}"'))
test_url = url.update_query_dict({"options": f"-csearch_path={schema},public"})
os.environ.update(DATABASE_URL=test_url.render_as_string(hide_password=False),
    PYTHON_DOTENV_DISABLED="1", APP_EDITION="demo", DEMO_STORAGE_ENABLED="true",
    SECRET_KEY="synthetic-unused-product-signing-key-only",
    DEMO_SECRET_KEY="synthetic-demo-browser-signing-secret-only",
    AI_ENABLED="false", REGISTRATION_ENABLED="false", FRONTEND_ORIGINS="http://127.0.0.1:3100")
from alembic import command
from alembic.config import Config
configuration = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
configuration.set_main_option("sqlalchemy.url", test_url.render_as_string(hide_password=False).replace("%", "%%"))
command.upgrade(configuration, "head")
from app.services import llm_service, embedding_service
def forbidden(*args, **kwargs):
    raise AssertionError("Demo browser tests must not call AI or embedding models")
llm_service.genai.Client = forbidden
embedding_service.generate_embedding = forbidden
from app.main import app
from app.db.database import engine

def cleanup():
    engine.dispose()
    with admin.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    admin.dispose()
atexit.register(cleanup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8100, access_log=False, proxy_headers=False)
