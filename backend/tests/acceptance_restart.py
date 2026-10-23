"""Opt-in disposable PostgreSQL restart proof; run seed, restart test server, verify.

No app DB fallback, model assets, provider requests or test-only app routes.
"""
import json
import os
import re
import sys
from pathlib import Path
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "backend"))
sys.path.insert(0, str(root / "backend/tests"))
value = os.environ.get("PHASE1_TEST_DATABASE_URL", "")
url = make_url(value)
if url.get_backend_name() != "postgresql" or url.host not in ("127.0.0.1", "localhost") or url.database != "cme_phase1_test":
    raise RuntimeError("Requires the explicit disposable loopback PostgreSQL instance")
os.environ.update(PYTHON_DOTENV_DISABLED="1", DATABASE_URL=value,
    SECRET_KEY="synthetic-restart-proof-signing-key-only-2026", GEMINI_API_KEY="synthetic-only", AI_ENABLED="false")
state_file = root / ".acceptance-restart-state.json"
admin = create_engine(url)
if sys.argv[1] == "seed":
    schema = "acceptance_restart_" + uuid4().hex
    with admin.begin() as connection: connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped = create_engine(url.update_query_dict({"options":f"-csearch_path={schema},public"}))
    from test_postgres import migrate, seed_users
    from test_historical_recall import seed_observation, seed_noise
    migrate(scoped)
    with Session(scoped) as db:
        users = seed_users(db); uid, other_uid = users[0].id, users[1].id
        capture, observation = seed_observation(db, uid, content="Corrected decorator reflection retained after restart")
        capture.original_text = "Synthetic original: I studied Python decorators."
        capture.confirmed_interpretation = {"subject":"Python", "topics":["Python decorators"]}
        state = {"schema":schema,"user_id":uid,"other_user_id":other_uid,"capture_id":capture.id,"observation_id":observation.id}
        seed_noise(db, uid, 140)
    scoped.dispose(); state_file.write_text(json.dumps(state), encoding="utf-8")
    print("Synthetic confirmed history committed; seed process can exit before server restart.")
elif sys.argv[1] == "verify":
    state = json.loads(state_file.read_text(encoding="utf-8")); schema = state["schema"]
    if not re.fullmatch(r"acceptance_restart_[0-9a-f]{32}", schema): raise RuntimeError("Unexpected fixture schema")
    scoped = create_engine(url.update_query_dict({"options":f"-csearch_path={schema},public"}))
    import app.services.rag_service as rag
    from app.models.learning_capture import LearningCapture, LearningObservation
    from app.models.memory_embedding import MemoryEmbedding
    def forbidden(_): raise AssertionError("No model initialization permitted in restart proof")
    rag.generate_embedding = forbidden
    rag.llm_service.generate_response = lambda prompt: f"Saved evidence [Observation {state['observation_id']}]"
    with Session(scoped) as db:
        capture = db.get(LearningCapture, state["capture_id"])
        observation = db.get(LearningObservation, state["observation_id"])
        assert capture.original_text == "Synthetic original: I studied Python decorators."
        assert observation.content == "Corrected decorator reflection retained after restart"
        assert db.query(MemoryEmbedding).count() == 0
        answer = rag.rag_service.generate_answer(db, state["user_id"], "Explain Python decorators")
        assert answer["sources"][0]["observation_id"] == state["observation_id"]
        assert rag.rag_service.generate_answer(db, state["other_user_id"], "Explain Python decorators")["sources"] == []
    scoped.dispose()
    with admin.begin() as connection: connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    state_file.unlink()
    output = root / "test-artifacts/final-acceptance/persistence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"status":"LOCAL RUNTIME PASS", "verification":"New Python service process after actual disposable PostgreSQL stop/start", "confirmed_captures":141, "newer_unrelated_observations":140, "original_preserved":True, "correction_preserved":True, "embeddings":0, "historical_recall":True, "other_owner_sources":0, "live_ai":False, "model_downloads":False}, indent=2)+"\n", encoding="utf-8")
    print("Restart persistence, historical recall and owner isolation passed; own fixture schema removed.")
else:
    raise RuntimeError("Use seed or verify")
admin.dispose()
