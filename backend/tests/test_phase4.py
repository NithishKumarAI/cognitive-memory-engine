from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.learning_track import LearningTrack
from app.models.learning_action import LearningAction
from app.models.study_log import StudyLog
from app.models.memory import Memory
from app.models.conversation import Conversation
from app.services import continuity_service as service


def seed(db, user_id, topic="Closures", track_id=None, kind="difficulty", status="confirmed"):
    capture = LearningCapture(user_id=user_id, source_type="text", original_text="Synthetic private closures note", status=status, version=2, confirmed_at=datetime.now(timezone.utc), learning_track_id=track_id)
    db.add(capture); db.flush()
    observation = LearningObservation(user_id=user_id, capture_id=capture.id, position=0, observation_type=kind, topic=topic, content="Synthetic closures question", evidence="closures", provenance="user_confirmed")
    db.add(observation); db.commit()
    return capture, observation


def test_action_reuse_rejects_changed_payload_even_after_status_update(client, headers, db):
    payload = {"idempotency_key": "same-operation", "action_type": "recommendation", "status": "completed", "topic": "Python"}
    first = client.post("/learning/actions", headers=headers, json=payload)
    assert first.status_code == 201
    action_id = first.json()["id"]
    assert client.post("/learning/actions", headers=headers, json=payload).json()["id"] == action_id
    assert client.post("/learning/actions", headers=headers, json={**payload, "status": "dismissed"}).status_code == 409
    assert client.patch(f"/learning/actions/{action_id}", headers=headers, json={"status": "dismissed"}).status_code == 200
    replay = client.post("/learning/actions", headers=headers, json=payload)
    assert replay.status_code == 201 and replay.json()["status"] == "dismissed"
    assert db.query(LearningAction).count() == 1


def test_observation_capture_identity_is_enforced(client, db, users, headers):
    first, obs = seed(db, users[0].id)
    second, _ = seed(db, users[0].id)
    result = client.post("/learning/actions", headers=headers, json={"idempotency_key": "mismatch", "action_type": "difficulty", "status": "resolved", "observation_id": obs.id, "capture_id": second.id})
    assert result.status_code == 400


def test_unassigned_topic_counts_are_not_polluted_by_assigned_tracks(db, users):
    user_id = users[0].id
    track = LearningTrack(user_id=user_id, name="Assigned")
    db.add(track); db.commit()
    seed(db, user_id, "  Shared   Topic ")
    seed(db, user_id, "shared topic", track.id)
    seed(db, user_id, "SHARED TOPIC", track.id)
    summaries = service.get_topic_continuity_summaries(db, user_id)
    unassigned = next(item for item in summaries if item.learning_track_id is None)
    assigned = next(item for item in summaries if item.learning_track_id == track.id)
    assert unassigned.confirmed_capture_count == unassigned.observations_count == 1
    assert assigned.confirmed_capture_count == assigned.observations_count == 2


def test_large_history_hydrates_bounded_evidence_and_uses_constant_queries(db, users):
    user_id = users[0].id
    now = datetime.now(timezone.utc)
    for index in range(240):
        capture = LearningCapture(user_id=user_id, source_type="text", original_text="x" * 20000, status="confirmed", version=1, confirmed_at=now - timedelta(minutes=index))
        db.add(capture); db.flush()
        db.add(LearningObservation(user_id=user_id, capture_id=capture.id, position=0, observation_type="difficulty", topic=f"Topic {index % 120}", content="question", evidence="x", provenance="user_confirmed"))
    db.commit(); db.expunge_all()
    loaded, queries = [], []
    def record_load(session, instance): loaded.append(instance.__class__.__name__)
    def record_query(*args): queries.append(1)
    event.listen(db, "loaded_as_persistent", record_load)
    event.listen(db.bind, "before_cursor_execute", record_query)
    try:
        checkpoints = service.get_resumable_checkpoints(db, user_id, limit=3)
        assert len(checkpoints) == 3
        assert loaded.count("LearningCapture") == 0
        assert loaded.count("LearningObservation") <= 6
        assert len(queries) <= 9
        queries.clear()
        summaries = service.get_topic_continuity_summaries(db, user_id, limit=20)
        assert len(summaries) == 20 and len(queries) <= 10
        overview = service.get_learning_overview(db, user_id)
        assert overview.distinct_topics_count == 120
        assert overview.unresolved_difficulties_count == 240
    finally:
        event.remove(db, "loaded_as_persistent", record_load)
        event.remove(db.bind, "before_cursor_execute", record_query)


def test_old_unresolved_evidence_is_preserved_with_bounded_briefs(db, users):
    user_id = users[0].id
    for index in range(25): seed(db, user_id)
    checkpoints = service.get_resumable_checkpoints(db, user_id, limit=1)
    assert len(checkpoints[0].unresolved_difficulties) == 10
    assert checkpoints[0].unresolved_difficulties_count == 25
    assert service.get_learning_overview(db, user_id).unresolved_difficulties_count == 25


def test_search_and_chat_history_are_owned_bounded_and_literal(client, db, users, headers):
    from app.core.auth import create_access_token
    uid, other_id = users[0].id, users[1].id
    own, own_obs = seed(db, uid)
    seed(db, uid, status="pending")
    seed(db, other_id)
    db.add_all([Memory(user_id=uid, title="Closures", content="100% literal", category="test"), LearningTrack(user_id=uid, name="Closures")])
    for number in range(25): db.add(Conversation(user_id=uid, message=f"question {number}", response="answer"))
    db.add(Conversation(user_id=other_id, message="private other user", response="private answer")); db.commit()
    result = client.get("/search?q=closures&limit=3", headers=headers)
    assert result.status_code == 200 and len(result.json()) == 3
    results = client.get("/search?q=closures&limit=30", headers=headers).json()
    capture_ids = [item["id"] for item in results if item["kind"] == "capture"]
    assert capture_ids == [own.id]
    observation = next(item for item in results if item["kind"] == "observation")
    assert observation["url"] == f"/dashboard/capture?capture={own.id}#observation-{own_obs.id}"
    assert len(client.get("/search?q=100%25", headers=headers).json()) == 1
    assert client.get("/search?q=%27%20OR%201%3D1--", headers=headers).json() == []
    history = client.get("/rag/history?limit=20", headers=headers).json()
    assert len(history) == 20 and "sources" not in history[0]
    older = client.get(f"/rag/history?before_id={history[-1]['id']}", headers=headers).json()
    assert len(older) == 5
    other = {"Authorization": "Bearer " + create_access_token({"sub": users[1].email})}
    assert len(client.get("/rag/history", headers=other).json()) == 1
    assert client.get("/search?q=closures", headers=other).status_code == 200
    assert result.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("path", ["/search?q=closures", "/rag/history", "/capture?offset=0"])
def test_new_reads_require_auth(client, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", ["/search?q=x", "/search?q=%20%20", "/search?q=word&limit=31", "/rag/history?limit=51", "/rag/history?before_id=-1", "/capture?limit=51", "/capture?offset=-1"])
def test_read_bounds(client, headers, path):
    assert client.get(path, headers=headers).status_code == 422


def test_distant_retrieval_cannot_trigger_unsupported_generation(monkeypatch):
    from app.services import rag_service as rag
    memory = SimpleNamespace(id=13, title="Unrelated", content="unrelated", category="test")
    monkeypatch.setattr(rag, "generate_embedding", Mock(return_value=[0.1] * 768))
    monkeypatch.setattr(rag, "search_memories_by_embedding", Mock(return_value=[(memory, 1.5)]))
    llm = Mock(side_effect=AssertionError("Do not generate without relevant evidence"))
    monkeypatch.setattr(rag.llm_service, "generate_response", llm)
    monkeypatch.setattr(rag, "create_conversation", Mock())
    result = rag.rag_service.generate_answer(Mock(), 1, "Unrelated subject query")
    assert result == {"answer": "The information is not available in memory.", "sources": []}
    llm.assert_not_called()


def test_study_frequency_has_seven_and_thirty_day_windows(db, users):
    from app.services.analytics_service import get_study_frequency
    user_id = users[0].id
    now = datetime.now(timezone.utc).replace(hour=12)
    for day in range(35): db.add(StudyLog(user_id=user_id, topic="Python", duration_minutes=5, notes="", created_at=now - timedelta(days=day)))
    db.add(StudyLog(user_id=user_id, topic="future", duration_minutes=5, notes="", created_at=now + timedelta(days=1)))
    db.commit()
    assert get_study_frequency(db, user_id) == {"study_days_last_7_days": 7, "study_days_last_30_days": 30}
