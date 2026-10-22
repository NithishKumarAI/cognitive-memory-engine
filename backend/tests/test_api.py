import pytest

from app.core.auth import create_access_token
from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.models.memory import Memory


@pytest.mark.parametrize("path", ["/me", "/users", "/users/1", "/memories", "/study-logs/", "/learning-tracks"])
def test_anonymous_denied(client, path):
    assert client.get(path).status_code == 401


def test_profiles_owner_only(client, users, headers):
    for path in ("/me", f"/users/{users[0].id}"):
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == users[0].id
        assert "hashed_password" not in response.json()
    assert [user["id"] for user in client.get("/users", headers=headers).json()] == [users[0].id]
    for user_id in (users[1].id, 99999):
        response = client.get(f"/users/{user_id}", headers=headers)
        assert response.status_code == 404
        assert response.json() == {"detail": "User not found"}
    other_headers = {"Authorization": "Bearer " + create_access_token({"sub": users[1].email})}
    assert client.get(f"/users/{users[0].id}", headers=other_headers).status_code == 404


def test_auth_register_login_and_me(client):
    payload = {"username": "new", "email": "new@example.com", "password": "test-password"}
    registered = client.post("/register", json=payload)
    assert registered.status_code == 200
    login = client.post("/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    response = client.get("/me", headers={"Authorization": "Bearer " + login.json()["access_token"]})
    assert response.json()["id"] == registered.json()["id"]
    assert client.post("/login", json={"email": payload["email"], "password": "wrong"}).status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_learning_ownership_and_foreign_links(client, db, users, headers):
    track = LearningTrack(user_id=users[1].id, name="Private")
    db.add(track)
    db.flush()
    log = StudyLog(user_id=users[1].id, learning_track_id=track.id, topic="Private", duration_minutes=1, notes="")
    db.add(log)
    db.flush()
    memory = Memory(user_id=users[1].id, study_log_id=log.id, title="Private", content="Text", category="test")
    db.add(memory)
    db.commit()
    for path, record_id in (("/learning-tracks", track.id), ("/study-logs", log.id), ("/memories", memory.id)):
        for method in ("get", "put", "delete"):
            kwargs = {"json": {}} if method == "put" else {}
            assert getattr(client, method)(f"{path}/{record_id}", headers=headers, **kwargs).status_code in (403, 404)
        listing = path + "/" if path == "/study-logs" else path
        assert client.get(listing, headers=headers).json() == []
    assert client.post("/study-logs/", headers=headers, json={"topic": "Valid", "duration_minutes": 1, "notes": "", "learning_track_id": track.id}).status_code == 400
    assert client.post("/memories", headers=headers, json={"title": "Valid", "content": "Text", "category": "test", "study_log_id": log.id}).status_code == 400


@pytest.mark.parametrize("healthy", [True, False])
def test_health(client, monkeypatch, healthy):
    def probe():
        if not healthy:
            raise RuntimeError("private connection details")
    monkeypatch.setattr("app.main.test_connection", probe)
    response = client.get("/health")
    assert response.status_code == (200 if healthy else 503)
    assert response.json() == {"status": "healthy" if healthy else "unhealthy",
                               "database": "connected" if healthy else "unavailable"}


def test_unlink_and_update_link_ownership(client, db, users, headers, monkeypatch):
    monkeypatch.setattr("app.crud.memory.generate_embedding", lambda _: [0.1] * 768)
    own_track = client.post("/learning-tracks", headers=headers, json={"name": "Own"}).json()
    own_log = client.post("/study-logs/", headers=headers,
                          json={"topic": "Own", "duration_minutes": 10, "notes": "", "learning_track_id": own_track["id"]}).json()
    own_memory = client.post("/memories", headers=headers,
                             json={"title": "Own", "content": "Text", "category": "test", "study_log_id": own_log["id"]}).json()
    other_track = LearningTrack(user_id=users[1].id, name="Other")
    db.add(other_track)
    db.flush()
    other_log = StudyLog(user_id=users[1].id, topic="Other", duration_minutes=1, notes="")
    db.add(other_log)
    db.commit()
    assert client.put(f"/study-logs/{own_log['id']}", headers=headers, json={"learning_track_id": other_track.id}).status_code == 400
    assert client.put(f"/memories/{own_memory['id']}", headers=headers, json={"study_log_id": other_log.id}).status_code == 400
    unlinked_log = client.put(f"/study-logs/{own_log['id']}", headers=headers, json={"learning_track_id": None})
    assert unlinked_log.status_code == 200 and unlinked_log.json()["learning_track_id"] is None
    unlinked_memory = client.put(f"/memories/{own_memory['id']}", headers=headers, json={"study_log_id": None})
    assert unlinked_memory.status_code == 200 and unlinked_memory.json()["study_log_id"] is None
