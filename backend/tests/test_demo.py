"""Real PostgreSQL demo isolation. The storage guard is never bypassed."""
import os
from datetime import datetime, UTC, timedelta
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.main import app
from app.db.dependencies import get_db
from app.core import config
from app.models.demo_session import DemoSession, DemoBudget
from app.models.learning_capture import LearningCapture
from app.models.study_log import StudyLog
from app.models.user import User
from app.services import demo_service
from test_postgres import migrate


@pytest.fixture
def demo_engine(monkeypatch):
    value = os.environ.get("PHASE_DEMO_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set PHASE_DEMO_TEST_DATABASE_URL to the disposable cme_verification_demo database")
    url = make_url(value)
    assert url.get_backend_name() == "postgresql" and url.host in ("localhost", "127.0.0.1") and url.database == "cme_verification_demo"
    schema = "demo_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url.update_query_dict({"options": f"-csearch_path={schema},public"}))
    migrate(engine)
    monkeypatch.setattr(config, "APP_EDITION", "demo")
    monkeypatch.setattr(config, "DEMO_STORAGE_ENABLED", True)
    monkeypatch.setattr(config, "DEMO_SECRET_KEY", "synthetic-demo-signing-secret-only-32-bytes")
    monkeypatch.setattr("app.db.database.engine", engine)
    def database():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    try:
        yield engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def demo_client(demo_engine):
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def guest(client):
    response = client.post("/demo/session")
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_product_rejects_demo_bootstrap(client):
    assert client.get("/edition").json()["edition"] == "product"
    assert client.post("/demo/session").status_code == 404
    assert client.get("/learning/overview").status_code == 401


def test_storage_guard_refuses_product_database_and_missing_opt_in(monkeypatch):
    monkeypatch.setattr(config, "APP_EDITION", "demo")
    engine = create_engine("sqlite://")
    with pytest.raises(RuntimeError, match="separate PostgreSQL"):
        demo_service.require_demo_storage(engine)
    engine.dispose()


@pytest.mark.parametrize("edition,enabled,database,secret", [
    ("product", True, "synthetic_demo", "synthetic-distinct-demo-secret-32-bytes"),
    ("demo", False, "synthetic_demo", "synthetic-distinct-demo-secret-32-bytes"),
    ("demo", True, "synthetic_product", "synthetic-distinct-demo-secret-32-bytes"),
    ("demo", True, "synthetic_demo", "short"),
])
def test_storage_guard_refuses_each_unsafe_configuration(monkeypatch, edition, enabled, database, secret):
    monkeypatch.setattr(config, "APP_EDITION", edition)
    monkeypatch.setattr(config, "DEMO_STORAGE_ENABLED", enabled)
    monkeypatch.setattr(config, "DEMO_SECRET_KEY", secret)
    engine = create_engine(f"postgresql+psycopg://synthetic@127.0.0.1/{database}")
    with pytest.raises(RuntimeError):
        demo_service.require_demo_storage(engine)
    engine.dispose()


def test_seeded_statistics_sources_and_idempotent_seed(demo_client, demo_engine):
    headers = guest(demo_client)
    overview = demo_client.get("/learning/overview", headers=headers).json()
    assert overview["confirmed_captures_count"] == 15
    assert overview["total_logged_study_hours"] == 7.75
    uid = demo_client.get("/me", headers=headers).json()["id"]
    with Session(demo_engine) as db:
        assert db.query(func.sum(StudyLog.duration_minutes)).filter(StudyLog.user_id == uid).scalar() == 465
        demo_service.seed_guest(db, uid); db.commit()
        assert db.query(LearningCapture).filter_by(user_id=uid).count() == 15
    assert len(demo_client.get("/learning-tracks", headers=headers).json()) == 3
    recommendations = demo_client.get("/learning/recommendations", headers=headers).json()
    assert recommendations
    for action in recommendations:
        assert action.get("supporting_capture_id") or action.get("capture_id") or action.get("source_capture_id") or action.get("supporting_observation_ids") or action.get("supporting_study_log_ids"), action


def test_two_visitors_reset_and_cross_edition_tokens(demo_client, demo_engine, monkeypatch):
    from app.core.auth import create_access_token
    first, second = guest(demo_client), guest(demo_client)
    record = demo_client.get("/capture", headers=first).json()[0]
    assert demo_client.get(f"/capture/{record['id']}", headers=second).status_code == 404
    draft = demo_client.post("/capture/manual", headers=first, json={"text": "Private temporary reflection"})
    assert draft.status_code == 200
    reset = demo_client.post("/demo/reset", headers=first)
    assert reset.status_code == 200
    assert demo_client.get("/me", headers=first).status_code == 401
    assert len(demo_client.get("/capture", headers=second).json()) == 15
    replacement = {"Authorization": "Bearer " + reset.json()["access_token"]}
    assert len(demo_client.get("/capture", headers=replacement).json()) == 15
    product_token = create_access_token({"sub": "anything@example.com"})
    assert demo_client.get("/me", headers={"Authorization": "Bearer " + product_token}).status_code == 401
    monkeypatch.setattr(config, "APP_EDITION", "product")
    assert demo_client.get("/me", headers=replacement).status_code == 401


def test_demo_never_calls_live_provider_and_guided_example_is_labeled(demo_client, monkeypatch):
    from unittest.mock import Mock
    from app.services import llm_service
    factory = Mock(side_effect=AssertionError("Demo must never call a provider"))
    monkeypatch.setattr(llm_service.genai, "Client", factory)
    headers = guest(demo_client)
    assert demo_client.post("/capture/analyze", headers=headers, json={"text": "SQL joins"}).status_code == 403
    assert demo_client.post("/capture/transcribe", headers=headers, content=b"fake audio").status_code == 403
    assert demo_client.put("/settings/ai", headers=headers, json={"api_key": "synthetic-never-save-this-key"}).status_code == 403
    with pytest.raises(llm_service.ProviderUnavailable):
        llm_service.LLMService().generate("synthetic note")
    draft = demo_client.post("/demo/example", headers=headers)
    assert draft.status_code == 200 and "not a live Gemini result" in draft.json()["message"]
    assert draft.json()["status"] == "pending"
    answer = demo_client.post("/rag/ask", headers=headers, json={"question": "Where did I stop?"})
    assert answer.status_code == 200 and answer.json()["sources"]
    answer = demo_client.post("/rag/ask", headers=headers, json={"question": "Explain SQL joins"})
    assert answer.status_code == 200 and "live ai is disabled" in answer.json()["answer"].lower()
    assert answer.json()["sources"]
    factory.assert_not_called()


def test_guest_issuance_global_budget_is_concurrency_safe(demo_engine):
    with Session(demo_engine) as db:
        budget = db.get(DemoBudget, 1); budget.day = datetime.now(UTC).date().isoformat(); budget.issued = 499; db.commit()
    def create(index):
        with Session(demo_engine) as db:
            try:
                demo_service.create_guest(db, f"synthetic-peer-{index}"); db.commit(); return 200
            except HTTPException as error:
                db.rollback(); return error.status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(create, range(4)))
    assert sorted(results) == [200, 429, 429, 429]
    with Session(demo_engine) as db:
        assert db.get(DemoBudget, 1).issued == 500
        assert db.query(User).count() == 1


def test_expiry_body_limits_and_atomic_mutation_budget(demo_client, demo_engine):
    headers = guest(demo_client)
    uid = demo_client.get("/me", headers=headers).json()["id"]
    response = demo_client.post("/capture/manual", headers=headers, content=iter([b"x" * 40000, b"y" * 40000]))
    assert response.status_code == 413
    with Session(demo_engine) as db:
        db.get(DemoSession, uid).mutations = 99; db.commit()
    def reserve(_):
        with Session(demo_engine) as db:
            try:
                demo_service.reserve_mutation(db, uid); return 200
            except HTTPException as error:
                return error.status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert sorted(pool.map(reserve, range(4))) == [200, 429, 429, 429]
    assert demo_client.post("/demo/example", headers=headers).status_code == 429
    with Session(demo_engine) as db:
        db.get(DemoSession, uid).expires_at = datetime.now(UTC) - timedelta(seconds=1); db.commit()
    assert demo_client.get("/me", headers=headers).status_code == 401


def test_cleanup_selects_only_expired_guest_records(demo_client, demo_engine):
    first, second = guest(demo_client), guest(demo_client)
    uid = demo_client.get("/me", headers=first).json()["id"]
    with Session(demo_engine) as db:
        db.add(User(username="unrelated-synthetic", email="unrelated@example.com", hashed_password="unused"))
        db.get(DemoSession, uid).expires_at = datetime.now(UTC) - timedelta(seconds=1); db.commit()
        assert demo_service.purge_expired(db) == 1
        assert db.query(User).filter_by(username="unrelated-synthetic").one()
        assert db.query(LearningCapture).filter_by(user_id=uid).count() == 0
    assert demo_client.get("/me", headers=first).status_code == 401
    assert demo_client.get("/learning/overview", headers=second).json()["confirmed_captures_count"] == 15


def test_explicit_local_helper_uses_only_demo_configuration(demo_engine, tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    environment = tmp_path / "synthetic-demo.env"
    url = demo_engine.url.render_as_string(hide_password=False)
    environment.write_text("\n".join([
        "APP_EDITION=demo", "DEMO_STORAGE_ENABLED=true", f"DATABASE_URL={url}", f"ALEMBIC_DATABASE_URL={url}",
        "DEMO_SECRET_KEY=synthetic-only-local-helper-demo-secret", "SECRET_KEY=synthetic-unused-product-secret", "AI_ENABLED=false"
    ]), encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "scripts/demo_local.py"
    for command in ["check", "migrate"]:
        result = subprocess.run([sys.executable, str(script), command, "--env-file", str(environment)], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, "Local demo helper failed; private subprocess output suppressed"
        assert "synthetic-only-local-helper-demo-secret" not in result.stdout + result.stderr
