"""Registration boundaries and error sanitization; only synthetic in-memory accounts."""
import pytest
from sqlalchemy.exc import OperationalError, IntegrityError
from app.models.user import User
from app.core.security import hash_password, verify_password

VALID = {"username": "synthetic-new", "email": "synthetic-new@example.com", "password": "synthetic-password"}


@pytest.mark.parametrize("field,value", [
    ("username", "ab"), ("username", "x" * 51), ("username", "    "),
    ("email", "invalid"), ("password", "short"), ("password", " " * 8),
    ("password", "x" * 73), ("password", "😀" * 19), ("password", "abc\0defgh"),
])
def test_invalid_signup_is_redacted_and_does_not_create_account(client, db, field, value):
    response = client.post("/register", json={**VALID, field: value})
    assert response.status_code == 422
    assert all(set(item) == {"loc", "msg", "type"} for item in response.json()["detail"])
    assert "input" not in response.text and VALID["password"] not in response.text
    assert db.query(User).count() == 0


def test_bcrypt_boundary_and_existing_hash_compatibility(client, db):
    password = "😀" * 18  # exactly 72 UTF-8 bytes
    response = client.post("/register", json={**VALID, "username": "  synthetic-new  ", "password": password})
    assert response.status_code == 200 and response.json()["username"] == VALID["username"]
    saved = db.query(User).one()
    assert saved.hashed_password.startswith("$2b$")
    assert verify_password(password, saved.hashed_password)
    assert client.post("/login", json={"email": VALID["email"], "password": password}).status_code == 200
    # Existing short passwords can still sign in; signup rules are not a hash migration.
    saved.hashed_password = hash_password("older"); db.commit()
    assert client.post("/login", json={"email": VALID["email"], "password": "older"}).status_code == 200


def test_duplicate_identity_and_retry_do_not_create_duplicate(client, db):
    first = client.post("/register", json=VALID)
    assert first.status_code == 200
    assert client.post("/register", json=VALID).json() == {"detail": "Email already registered"}
    assert client.post("/register", json={**VALID, "email": "another@example.com"}).json() == {"detail": "Username already exists"}
    assert db.query(User).count() == 1
    assert "password" not in first.text


@pytest.mark.parametrize("path", ["/register", "/login"])
def test_database_failure_is_sanitized(client, monkeypatch, path):
    def unavailable(*args):
        raise OperationalError("private database statement", {}, Exception("private credentials"))
    monkeypatch.setattr("app.routes.user." + ("get_user_by_email" if path == "/register" else "authenticate_user"), unavailable)
    response = client.post(path, json=VALID)
    assert response.status_code == 503
    assert response.json() == {"detail": "Account service unavailable"}
    assert "private" not in response.text and VALID["password"] not in response.text


def test_concurrent_registration_conflict_rolls_back(client, db, monkeypatch):
    from app.routes import user
    original = user.get_user_by_email
    calls = 0
    def competing_result(session, email):
        nonlocal calls
        calls += 1
        return None if calls == 1 else object()
    def conflict(*args):
        raise IntegrityError("private insert", {}, Exception("private constraint"))
    monkeypatch.setattr(user, "get_user_by_email", competing_result)
    monkeypatch.setattr(user, "create_user", conflict)
    response = client.post("/register", json=VALID)
    assert response.status_code == 400 and response.json()["detail"] == "Email already registered"
    monkeypatch.setattr(user, "get_user_by_email", original)
    assert db.query(User).count() == 0
