"""Explicitly isolated browser-test server. Never import this from app startup."""
import os
import sys
import json
import re
import atexit
from uuid import uuid4
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
value = os.environ.get("PHASE4_E2E_DATABASE_URL")
if not value:
    raise RuntimeError("An explicitly disposable E2E database is required")
url = make_url(value)
if url.host not in ("127.0.0.1", "localhost") or url.database != "cme_phase1_test" or url.get_backend_name() != "postgresql":
    raise RuntimeError("E2E requires a local disposable cme_phase1_test database")
schema = "phase4_e2e_" + uuid4().hex
admin = create_engine(url)
with admin.begin() as connection:
    connection.execute(text(f'CREATE SCHEMA "{schema}"'))
test_url = url.update_query_dict({"options": f"-csearch_path={schema},public"})
os.environ.update(DATABASE_URL=test_url.render_as_string(hide_password=False), PYTHON_DOTENV_DISABLED="1",
    SECRET_KEY="synthetic-e2e-signing-key-only-at-least-32-bytes", AI_ENABLED="true", REGISTRATION_ENABLED="true", GEMINI_API_KEY="synthetic-only", GOOGLE_GENAI_USE_VERTEXAI="false",
    GEMINI_MODEL="gemini-2.5-flash", GEMINI_TIMEOUT_MS="30000", FRONTEND_ORIGINS="http://127.0.0.1:3100")
from alembic import command
from alembic.config import Config
config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
config.set_main_option("sqlalchemy.url", test_url.render_as_string(hide_password=False).replace("%", "%%"))
command.upgrade(config, "head")
import app.services.embedding_service as embedding
embedding.generate_embedding = lambda _: [1.0] + [0.0] * 767
from app.services.llm_service import llm_service

def mock_generate(contents, config=None):
    if getattr(config, "response_schema", None).__name__ == "Transcript":
        return json.dumps({"transcript": "I studied Python decorators. Closures are confusing. Next I will practice."})
    original = contents if isinstance(contents, str) else "Synthetic learning"
    return json.dumps({"subject": "Python", "topics": ["Decorators", "Closures"], "observations": [
        {"observation_type": "learned", "topic": "Decorators", "content": "Studied Python decorators", "evidence": "Python decorators" if "Python decorators" in original else original[:60]},
        {"observation_type": "difficulty", "topic": "Closures", "content": "Closures are confusing", "evidence": "Closures are confusing" if "Closures are confusing" in original else original[:60]},
        {"observation_type": "intended_next_step", "topic": "Practice", "content": "Practice decorators", "evidence": "practice" if "practice" in original else original[:60]}]})
llm_service.generate = mock_generate
llm_service.generate_response = lambda prompt: "From your saved records: " + (re.search(r"\[Observation \d+\]", prompt).group() if re.search(r"\[Observation \d+\]", prompt) else "the available evidence is limited.")
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
    uvicorn.run(app, host="127.0.0.1", port=8100, access_log=False)
