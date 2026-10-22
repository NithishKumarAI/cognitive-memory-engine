"""Narrow release regressions; no provider calls or application data."""
import base64
import hashlib
import hmac
import json
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime, UTC
import pytest
import jwt
from app.core import auth

LEGACY = json.loads(Path(__file__).with_name("legacy_hs256.json").read_text())


def test_baseline_jose_token_decodes_and_authenticates_without_session_rotation(monkeypatch, client, users):
    monkeypatch.setattr(auth, "SECRET_KEY", LEGACY["key"])
    assert auth.verify_access_token(LEGACY["token"]) == users[0].email
    response = client.get("/me", headers={"Authorization": "Bearer " + LEGACY["token"]})
    assert response.status_code == 200 and response.json()["id"] == users[0].id


def test_new_token_preserves_hs256_wire_format_and_expiry(monkeypatch):
    monkeypatch.setattr(auth, "SECRET_KEY", LEGACY["key"])
    before = datetime.now(UTC).timestamp()
    token = auth.create_access_token({"sub": "user1@example.com"})
    header, body, signature = token.split(".")
    assert json.loads(base64.urlsafe_b64decode(header + "=="))["alg"] == "HS256"
    assert base64.urlsafe_b64decode(signature + "==") == hmac.new(LEGACY["key"].encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    claims = json.loads(base64.urlsafe_b64decode(body + "=="))
    assert before + auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60 - 1 <= claims["exp"] <= datetime.now(UTC).timestamp() + auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert auth.verify_access_token(token) == "user1@example.com"


@pytest.mark.parametrize("claims,algorithm", [({"sub":"user1@example.com","exp":1},"HS256"), ({"sub":"user1@example.com","exp":4102444800},"HS384"), ({"exp":4102444800},"HS256"), ({"sub":"user1@example.com"},"HS256"), ({"sub":123,"exp":4102444800},"HS256")])
def test_invalid_expired_or_wrong_algorithm_token_is_rejected(monkeypatch, claims, algorithm):
    monkeypatch.setattr(auth, "SECRET_KEY", LEGACY["key"])
    assert auth.verify_access_token(jwt.encode(claims, LEGACY["key"] if algorithm == "HS256" else "wrong-algorithm-synthetic-key-at-least-48-bytes-long", algorithm=algorithm)) is None


def test_tampered_legacy_token_is_rejected(monkeypatch):
    monkeypatch.setattr(auth, "SECRET_KEY", "different-synthetic-key-with-sufficient-length")
    assert auth.verify_access_token(LEGACY["token"]) is None


def test_container_backend_port_contract(monkeypatch):
    from app import runtime
    import uvicorn
    monkeypatch.delenv("PORT", raising=False)
    assert runtime.configured_port() == 8000
    monkeypatch.setenv("PORT", "8089")
    run = Mock(); monkeypatch.setattr(uvicorn, "run", run)
    runtime.main(); run.assert_called_once_with("app.main:app", host="0.0.0.0", port=8089)
    for value in ["", "0", "65536", "8080 --reload", "1.5", "-1"]:
        with pytest.raises(ValueError): runtime.configured_port(value)


def test_registration_can_close_without_changing_existing_login(monkeypatch, client, db):
    from app.routes import user
    from app.models.user import User
    monkeypatch.setattr(user, "REGISTRATION_ENABLED", False)
    response = client.post("/register", json={"username":"closed-user", "email":"closed@example.com", "password":"synthetic-pass"})
    assert response.status_code == 403
    assert db.query(User).count() == 0
    assert client.post("/login", json={"email":"closed@example.com", "password":"synthetic-pass"}).status_code == 401


def test_ai_disabled_never_constructs_provider_client(monkeypatch):
    from app.services import llm_service as service
    monkeypatch.setattr(service, "AI_ENABLED", False)
    provider = Mock(side_effect=AssertionError("No provider client when AI disabled"))
    monkeypatch.setattr(service.genai, "Client", provider)
    with pytest.raises(service.ProviderUnavailable, match="AI service unavailable"):
        service.LLMService().generate("synthetic note")
    provider.assert_not_called()


def test_fixed_fsspec_local_io_contract(tmp_path):
    import fsspec
    target = tmp_path / "synthetic.txt"
    with fsspec.open(str(target), "w") as output: output.write("synthetic model cache metadata")
    with fsspec.open(str(target), "r") as source: assert source.read() == "synthetic model cache metadata"


def test_concurrent_embedding_initialization_loads_once(monkeypatch):
    import sys
    import time
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace
    from app.services import embedding_service as service
    start = Barrier(2); model = object()
    def construct(name):
        assert name == service.MODEL_NAME
        time.sleep(0.03)
        return model
    constructor = Mock(side_effect=construct)
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=constructor))
    monkeypatch.setattr(service, "_embedding_model", None)
    def load():
        start.wait(timeout=5)
        return service.get_embedding_model()
    with ThreadPoolExecutor(max_workers=2) as workers:
        first, second = workers.submit(load), workers.submit(load)
        assert first.result(timeout=5) is model and second.result(timeout=5) is model
    constructor.assert_called_once()


def test_rag_provider_output_is_bounded_without_changing_capture_limits(monkeypatch):
    from app.services.llm_service import LLMService
    service = LLMService(); generate = Mock(return_value="synthetic answer")
    monkeypatch.setattr(service, "generate", generate)
    assert service.generate_response("synthetic question") == "synthetic answer"
    assert generate.call_args.args[0] == "synthetic question"
    assert generate.call_args.args[1].max_output_tokens == 2048
