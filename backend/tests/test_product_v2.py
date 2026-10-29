"""Fresh-account and manual capture regressions. No paid provider calls."""
import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.dependencies import get_db
from test_postgres import postgres_db, postgres_engine  # noqa: F401


def test_manual_capture_never_calls_provider(client, headers, monkeypatch):
    from app.services.llm_service import llm_service
    provider = Mock(side_effect=AssertionError("Manual capture must not call AI"))
    monkeypatch.setattr(llm_service, "generate", provider)
    draft = client.post("/capture/manual", headers=headers, json={"text": "I studied SQL joins."})
    assert draft.status_code == 200
    data = draft.json()
    assert data["proposed_interpretation"] is None and data["original_text"] == "I studied SQL joins."
    saved = client.post(f"/capture/{data['id']}/confirm", headers=headers, json={"expected_version": data["version"], "interpretation": {"topics": ["SQL joins"], "observations": [{"observation_type": "difficulty", "topic": "SQL joins", "content": "Need more practice", "evidence": "SQL joins"}]}})
    assert saved.status_code == 200 and saved.json()["status"] == "confirmed"
    assert len(client.get("/learning/recommendations", headers=headers).json()) > 0
    provider.assert_not_called()


def test_personal_key_lifecycle_is_encrypted_and_owner_scoped(client, db, headers, users, monkeypatch):
    import base64
    from app.core import config
    from app.core.auth import create_access_token
    from app.models.ai_credential import AICredential
    from app.services.ai_credentials import provider_owner, personal_key
    monkeypatch.setattr(config, "AI_KEY_ENCRYPTION_KEYS", base64.urlsafe_b64encode(b"0" * 32).decode())
    first, second = "synthetic-personal-key-one", "synthetic-personal-key-two"
    other_headers = {"Authorization": "Bearer " + create_access_token({"sub": users[1].email})}
    for secret in (first, second):
        result = client.put("/settings/ai", headers=headers, json={"api_key": secret})
        assert result.status_code == 200 and secret not in result.text
        record = db.get(AICredential, users[0].id)
        assert secret not in record.encrypted_key
        context = provider_owner.set((users[0].id, db.get_bind()))
        try:
            assert personal_key() == secret
        finally:
            provider_owner.reset(context)
        assert client.get("/settings/ai", headers=other_headers).json()["configured"] is False
    assert client.delete("/settings/ai", headers=other_headers).status_code == 200
    assert client.get("/settings/ai", headers=headers).json()["configured"] is True
    assert client.delete("/settings/ai", headers=headers).status_code == 200
    assert client.get("/settings/ai", headers=headers).json()["configured"] is False


def test_no_global_key_fallback_or_secret_validation_echo(client, headers, monkeypatch):
    from app.services import llm_service
    from unittest.mock import Mock
    secret = "synthetic-secret-never-return"
    response = client.put("/settings/ai", headers=headers, json={"api_key": secret, "unexpected": secret})
    assert response.status_code == 422 and secret not in response.text
    constructor = Mock(side_effect=AssertionError("Global key must not be used"))
    monkeypatch.setattr(llm_service.genai, "Client", constructor)
    monkeypatch.setattr(llm_service, "GEMINI_API_KEY", secret)
    with pytest.raises(llm_service.ProviderUnavailable):
        llm_service.LLMService().generate("synthetic text")
    constructor.assert_not_called()


def test_authenticated_provider_uses_only_current_users_key(client, headers, users, monkeypatch):
    import base64
    from types import SimpleNamespace
    from unittest.mock import Mock
    from app.core import config
    from app.core.auth import create_access_token
    from app.services import llm_service as provider
    monkeypatch.setattr(config, "AI_KEY_ENCRYPTION_KEYS", base64.urlsafe_b64encode(b"1" * 32).decode())
    other = {"Authorization": "Bearer " + create_access_token({"sub": users[1].email})}
    first_key, second_key = "synthetic-owner-first-key", "synthetic-owner-second-key"
    for authentication, key in [(headers, first_key), (other, second_key)]:
        assert client.put("/settings/ai", headers=authentication, json={"api_key": key}).status_code == 200
    fake = Mock()
    fake.__enter__ = Mock(return_value=fake)
    fake.__exit__ = Mock(return_value=False)
    fake.models.generate_content.return_value = SimpleNamespace(text='{"topics":[],"observations":[]}')
    constructor = Mock(return_value=fake)
    monkeypatch.setattr(provider.genai, "Client", constructor)
    monkeypatch.setattr(provider.llm_service, "generate", provider.LLMService().generate)
    for authentication, key in [(headers, first_key), (other, second_key), (headers, first_key)]:
        response = client.post("/capture/analyze", headers=authentication, json={"text": "A synthetic learning note"})
        assert response.status_code == 200 and response.json()["status"] == "pending"
        assert constructor.call_args.kwargs["api_key"] == key
    assert constructor.call_count == 3


def test_ciphertext_cannot_be_reassigned_to_another_owner_and_rotation_reads_old_keys(db, users, monkeypatch):
    import base64
    from app.core import config
    from app.models.ai_credential import AICredential
    from app.services.ai_credentials import encrypt, personal_key, provider_owner
    old, new = [base64.urlsafe_b64encode(value * 32).decode() for value in [b"2", b"3"]]
    monkeypatch.setattr(config, "AI_KEY_ENCRYPTION_KEYS", old)
    encrypted = encrypt(users[0].id, "synthetic-owner-key-for-rotation")
    db.add(AICredential(user_id=users[0].id, encrypted_key=encrypted))
    db.add(AICredential(user_id=users[1].id, encrypted_key=encrypted)); db.commit()
    monkeypatch.setattr(config, "AI_KEY_ENCRYPTION_KEYS", new + "," + old)
    owner = provider_owner.set((users[0].id, db.get_bind()))
    try:
        assert personal_key() == "synthetic-owner-key-for-rotation"
    finally:
        provider_owner.reset(owner)
    other = provider_owner.set((users[1].id, db.get_bind()))
    try:
        with pytest.raises(ValueError, match="owner mismatch"):
            personal_key()
    finally:
        provider_owner.reset(other)


def test_storage_outage_is_sanitized_and_recovers(client, headers, monkeypatch):
    from app.services import continuity_service
    from sqlalchemy.exc import OperationalError
    original = continuity_service.get_learning_overview
    def unavailable(*args, **kwargs):
        raise OperationalError("private query", {}, Exception("private connection credential"))
    monkeypatch.setattr(continuity_service, "get_learning_overview", unavailable)
    result = client.get("/learning/overview", headers=headers)
    assert result.status_code == 503 and "private" not in result.text
    assert client.get("/learning-tracks", headers=headers).status_code == 200
    monkeypatch.setattr(continuity_service, "get_learning_overview", original)
    assert client.get("/learning/overview", headers=headers).status_code == 200


@pytest.mark.postgres
def test_confirmed_learning_survives_application_process_restarts(postgres_db):
    import os
    import sys
    import subprocess
    import json
    from pathlib import Path
    from app.models.user import User
    from app.models.learning_capture import LearningCapture
    from app.schemas.capture import ConfirmInput
    from app.services.capture_service import confirm
    user = User(username="restart-v2", email="restart-v2@example.com", hashed_password="synthetic-unused")
    postgres_db.add(user); postgres_db.flush()
    capture = LearningCapture(user_id=user.id, original_text="A durable manual learning update", source_type="text", status="pending", version=1)
    postgres_db.add(capture); postgres_db.commit()
    result = confirm(postgres_db, capture.id, user.id, ConfirmInput(expected_version=1,
        interpretation={"topics": ["Persistence"], "observations": [{"observation_type": "learned", "topic": "Persistence", "content": "Saved through a restart"}]}))
    capture_id = result.id
    environment = {**os.environ, "DATABASE_URL": postgres_db.bind.url.render_as_string(hide_password=False),
                   "AI_ENABLED": "false", "APP_EDITION": "product", "PYTHON_DOTENV_DISABLED": "1"}
    script = '''import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import create_access_token
with TestClient(app) as client:
    headers = {"Authorization": "Bearer " + create_access_token({"sub": "restart-v2@example.com"})}
    response = client.get("/capture/CAPTURE_ID", headers=headers)
    assert response.status_code == 200
    print(json.dumps(response.json()))
'''.replace("CAPTURE_ID", str(capture_id))
    for _ in range(2):
        child = subprocess.run([sys.executable, "-c", script], env=environment,
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        assert child.returncode == 0, "Isolated restart verification failed; private subprocess output suppressed"
        saved = json.loads(child.stdout)
        assert saved["status"] == "confirmed" and saved["original_text"] == "A durable manual learning update"
        assert saved["observations"][0]["content"] == "Saved through a restart"


@pytest.mark.postgres
@pytest.mark.parametrize("ai_enabled", [False, True])
def test_fresh_migrated_account_endpoint_matrix(postgres_db, monkeypatch, ai_enabled):
    from app.services import llm_service
    monkeypatch.setattr(llm_service, "AI_ENABLED", ai_enabled)
    def database():
        yield postgres_db
    def health():
        postgres_db.execute(text("SELECT 1"))
    monkeypatch.setattr("app.main.test_connection", health)
    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            account = {"username": "fresh-v2", "email": "fresh-v2@example.com", "password": "synthetic-password"}
            assert client.post("/register", json=account).status_code == 200
            login = client.post("/login", json=account)
            assert login.status_code == 200
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            for path in ["/me", "/learning/overview?timezone=Asia/Calcutta", "/learning/checkpoints", "/learning/recommendations", "/learning-tracks", "/capture", "/health"]:
                response = client.get(path, headers=headers)
                print(f"AI={ai_enabled} {path}: {response.status_code}")
                assert response.status_code == 200, path
                if path in ["/learning/checkpoints", "/learning/recommendations", "/learning-tracks", "/capture"]:
                    assert response.json() == []
    finally:
        app.dependency_overrides.clear()
