from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import pytest
from sqlalchemy import text

from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.learning_track import LearningTrack
from app.models.study_log import StudyLog
from app.models.learning_action import LearningAction
from app.models.memory import Memory
from app.schemas.continuity import LearningActionCreate, LearningActionUpdate
from app.services import continuity_service as continuity
from app.services.recommendation_service import RecommendationService
from app.services import rag_service as rag_module
from app.core.auth import create_access_token


def test_empty_history(client, headers):
    # New user with no data should get empty structures and zero metrics without errors
    res = client.get("/learning/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["confirmed_captures_count"] == 0
    assert data["distinct_topics_count"] == 0
    assert data["total_observations_count"] == 0
    assert data["total_logged_study_hours"] == 0.0
    assert data["current_streak"] == 0
    assert data["checkpoints_count"] == 0

    res_cp = client.get("/learning/checkpoints", headers=headers)
    assert res_cp.status_code == 200
    assert res_cp.json() == []

    res_rec = client.get("/learning/recommendations", headers=headers)
    assert res_rec.status_code == 200
    assert res_rec.json() == []

    res_top = client.get("/learning/topics", headers=headers)
    assert res_top.status_code == 200
    assert res_top.json() == []


def test_confirmed_vs_unconfirmed_filtering(db, client, headers, users):
    u1 = users[0]
    # Create captures in pending, failed, discarded, and confirmed states
    cap_pending = LearningCapture(user_id=u1.id, source_type="text", original_text="Pending text", status="pending", version=1)
    cap_failed = LearningCapture(user_id=u1.id, source_type="text", original_text="Failed text", status="failed", version=1)
    cap_discarded = LearningCapture(user_id=u1.id, source_type="text", original_text="Discarded text", status="discarded", version=2)
    cap_confirmed = LearningCapture(
        user_id=u1.id, source_type="text", original_text="Confirmed text", status="confirmed", version=2,
        confirmed_at=datetime.now(timezone.utc)
    )
    db.add_all([cap_pending, cap_failed, cap_discarded, cap_confirmed])
    db.commit()

    # Add observations to confirmed capture
    obs1 = LearningObservation(
        user_id=u1.id, capture_id=cap_confirmed.id, position=0, observation_type="learned",
        topic="FastAPI", content="Understood routing", evidence="routing evidence", provenance="user_confirmed"
    )
    obs2 = LearningObservation(
        user_id=u1.id, capture_id=cap_confirmed.id, position=1, observation_type="difficulty",
        topic="FastAPI", content="Dependency injection nuance", evidence="dependency evidence", provenance="user_confirmed"
    )
    db.add_all([obs1, obs2])
    db.commit()

    res = client.get("/learning/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["confirmed_captures_count"] == 1
    assert data["total_observations_count"] == 2
    assert data["learned_count"] == 1
    assert data["difficulties_count"] == 1

    cps = client.get("/learning/checkpoints", headers=headers).json()
    assert len(cps) == 1
    assert cps[0]["topic"] == "FastAPI"
    assert cps[0]["state"] == "needs_attention"
    assert len(cps[0]["unresolved_difficulties"]) == 1


def test_missing_duration_and_no_double_counted_time(db, client, headers, users):
    u1 = users[0]
    # Confirmed capture WITHOUT duration (study_log_id is None)
    cap_no_dur = LearningCapture(
        user_id=u1.id, source_type="text", original_text="No duration capture", status="confirmed", version=2,
        confirmed_at=datetime.now(timezone.utc), study_log_id=None
    )
    db.add(cap_no_dur)
    db.commit()
    obs = LearningObservation(
        user_id=u1.id, capture_id=cap_no_dur.id, position=0, observation_type="learned",
        topic="SQLAlchemy", content="ORM basics", evidence="orm", provenance="user_confirmed"
    )
    db.add(obs)
    db.commit()

    # Log duration should still be 0.0
    overview = client.get("/learning/overview", headers=headers).json()
    assert overview["total_logged_study_hours"] == 0.0

    # Add a study log associated with a confirmed capture
    log1 = StudyLog(user_id=u1.id, topic="SQLAlchemy", duration_minutes=60, notes="Session 1")
    db.add(log1)
    db.commit()
    cap_with_dur = LearningCapture(
        user_id=u1.id, source_type="text", original_text="With duration capture", status="confirmed", version=2,
        confirmed_at=datetime.now(timezone.utc), study_log_id=log1.id
    )
    db.add(cap_with_dur)
    db.commit()

    overview = client.get("/learning/overview", headers=headers).json()
    # 60 minutes = 1.0 hour, NOT double-counted as 120 minutes!
    assert overview["total_logged_study_hours"] == 1.0


def test_legacy_study_log_only_history(db, client, headers, users):
    u1 = users[0]
    # Legacy study log before Phase 2 capture existed
    legacy_log = StudyLog(user_id=u1.id, topic="Legacy Python", duration_minutes=45, notes="Old manual note")
    db.add(legacy_log)
    db.commit()

    overview = client.get("/learning/overview", headers=headers).json()
    assert overview["confirmed_captures_count"] == 0
    assert overview["total_observations_count"] == 0
    assert overview["distinct_topics_count"] == 1
    assert overview["total_logged_study_hours"] == 0.75

    checkpoints = client.get("/learning/checkpoints", headers=headers).json()
    assert len(checkpoints) == 1
    cp = checkpoints[0]
    assert cp["topic"] == "Legacy Python"
    assert cp["state"] == "recorded"
    # Never invent confirmed observations from legacy notes!
    assert cp["understood_self_reports"] == []
    assert cp["unresolved_difficulties"] == []
    assert cp["last_capture_id"] is None


def test_multi_topic_and_multi_track_isolation(db, client, headers, users):
    u1 = users[0]
    track_py = LearningTrack(user_id=u1.id, name="Python Track")
    track_js = LearningTrack(user_id=u1.id, name="JavaScript Track")
    db.add_all([track_py, track_js])
    db.commit()

    now = datetime.now(timezone.utc)
    # Python track capture with multiple topics
    cap_py = LearningCapture(
        user_id=u1.id, learning_track_id=track_py.id, source_type="text",
        original_text="Decorators and closures", status="confirmed", version=2, confirmed_at=now
    )
    db.add(cap_py)
    db.commit()
    db.add_all([
        LearningObservation(user_id=u1.id, capture_id=cap_py.id, position=0, observation_type="understood_self_report",
                            topic="Decorators", content="I understand @wraps", evidence="@wraps", provenance="user_confirmed"),
        LearningObservation(user_id=u1.id, capture_id=cap_py.id, position=1, observation_type="difficulty",
                            topic="Closures", content="Scope is confusing", evidence="confusing", provenance="user_confirmed"),
    ])

    # JavaScript track has similarly named topic "Decorators" (JS proposal)
    cap_js = LearningCapture(
        user_id=u1.id, learning_track_id=track_js.id, source_type="text",
        original_text="JS Decorators", status="confirmed", version=2, confirmed_at=now - timedelta(days=1)
    )
    db.add(cap_js)
    db.commit()
    db.add(LearningObservation(user_id=u1.id, capture_id=cap_js.id, position=0, observation_type="learned",
                               topic="Decorators", content="Stage 3 decorators", evidence="stage 3", provenance="user_confirmed"))
    db.commit()

    checkpoints = client.get("/learning/checkpoints", headers=headers).json()
    # Distinct tracks should NOT merge similarly named topics silently
    py_decs = [c for c in checkpoints if c["topic"] == "Decorators" and c["learning_track_id"] == track_py.id]
    js_decs = [c for c in checkpoints if c["topic"] == "Decorators" and c["learning_track_id"] == track_js.id]
    closures = [c for c in checkpoints if c["topic"] == "Closures"]

    assert len(py_decs) == 1
    assert len(js_decs) == 1
    assert len(closures) == 1
    assert py_decs[0]["state"] == "self_reported_understood"
    assert closures[0]["state"] == "needs_attention"

    # Filter checkpoints by track
    py_only = client.get(f"/learning/checkpoints?track_id={track_py.id}", headers=headers).json()
    assert all(c["learning_track_id"] == track_py.id for c in py_only)
    assert len(py_only) == 2


def test_cross_user_isolation(db, client, headers, users):
    u1, u2 = users[0], users[1]
    headers_u2 = {"Authorization": "Bearer " + create_access_token({"sub": u2.email})}

    # User 1 confirmed capture
    cap1 = LearningCapture(user_id=u1.id, source_type="text", original_text="User 1 note", status="confirmed", version=2)
    db.add(cap1); db.commit()
    obs1 = LearningObservation(user_id=u1.id, capture_id=cap1.id, position=0, observation_type="difficulty",
                               topic="Security", content="User 1 difficulty", evidence="sec", provenance="user_confirmed")
    db.add(obs1); db.commit()

    # User 2 should NOT see User 1's difficulty, checkpoint or overview
    u2_overview = client.get("/learning/overview", headers=headers_u2).json()
    assert u2_overview["confirmed_captures_count"] == 0
    assert u2_overview["difficulties_count"] == 0

    u2_checkpoints = client.get("/learning/checkpoints", headers=headers_u2).json()
    assert u2_checkpoints == []

    u2_recs = client.get("/learning/recommendations", headers=headers_u2).json()
    assert u2_recs == []

    # User 2 cannot resolve User 1's observation
    res_bad = client.post("/learning/actions", headers=headers_u2, json={
        "idempotency_key": "u2-hack-key",
        "action_type": "difficulty",
        "status": "resolved",
        "observation_id": obs1.id,
    })
    assert res_bad.status_code == 404


def test_action_completion_idempotency_and_difficulty_resolution(db, client, headers, users):
    u1 = users[0]
    cap = LearningCapture(user_id=u1.id, source_type="text", original_text="Study note", status="confirmed", version=2)
    db.add(cap); db.commit()
    obs_diff = LearningObservation(
        user_id=u1.id, capture_id=cap.id, position=0, observation_type="difficulty",
        topic="AsyncIO", content="Event loop blocking", evidence="event loop", provenance="user_confirmed"
    )
    obs_next = LearningObservation(
        user_id=u1.id, capture_id=cap.id, position=1, observation_type="intended_next_step",
        topic="AsyncIO", content="Build small scraper", evidence="scraper", provenance="user_confirmed"
    )
    db.add_all([obs_diff, obs_next]); db.commit()

    # Check initially needs_attention
    cps = client.get("/learning/checkpoints", headers=headers).json()
    assert cps[0]["state"] == "needs_attention"
    assert len(cps[0]["unresolved_difficulties"]) == 1
    assert len(cps[0]["pending_next_steps"]) == 1

    # Mark difficulty resolved with idempotency key
    action_payload = {
        "idempotency_key": "idemp-diff-1",
        "action_type": "difficulty",
        "status": "resolved",
        "observation_id": obs_diff.id,
        "notes": "Read the official asyncio docs and understood tasks vs coroutines"
    }
    res_action = client.post("/learning/actions", headers=headers, json=action_payload)
    assert res_action.status_code in (200, 201)
    act_data = res_action.json()
    assert act_data["status"] == "resolved"
    action_id = act_data["id"]

    # Retry identical request: must return existing record idempotently
    res_retry = client.post("/learning/actions", headers=headers, json=action_payload)
    assert res_retry.status_code in (200, 201)
    assert res_retry.json()["id"] == action_id

    # Check that difficulty is now resolved!
    cps_after = client.get("/learning/checkpoints", headers=headers).json()
    assert len(cps_after[0]["unresolved_difficulties"]) == 0

    # Complete the next step
    client.post("/learning/actions", headers=headers, json={
        "idempotency_key": "idemp-next-1",
        "action_type": "next_step",
        "status": "completed",
        "observation_id": obs_next.id,
    })
    cps_final = client.get("/learning/checkpoints", headers=headers).json()
    assert len(cps_final[0]["pending_next_steps"]) == 0

    # Update action status
    res_update = client.post(f"/learning/actions/{action_id}/update", headers=headers, json={
        "status": "dismissed",
        "notes": "Updated note"
    })
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "dismissed"


def test_deterministic_recommendation_ranking_and_provenance(db, client, headers, users):
    u1 = users[0]
    now = datetime.now(timezone.utc)

    # 1. Capture with intended next step
    cap1 = LearningCapture(user_id=u1.id, source_type="text", original_text="Plan step", status="confirmed", version=2, confirmed_at=now)
    db.add(cap1); db.commit()
    obs_step = LearningObservation(
        user_id=u1.id, capture_id=cap1.id, position=0, observation_type="intended_next_step",
        topic="Testing", content="Write integration tests", evidence="tests", provenance="user_confirmed"
    )
    # 2. Capture with difficulty
    cap2 = LearningCapture(user_id=u1.id, source_type="text", original_text="Struggled", status="confirmed", version=2, confirmed_at=now - timedelta(days=1))
    db.add(cap2); db.commit()
    obs_diff = LearningObservation(
        user_id=u1.id, capture_id=cap2.id, position=0, observation_type="difficulty",
        topic="Algorithms", content="Dynamic programming memoization", evidence="dp", provenance="user_confirmed"
    )
    # 3. Capture with open question
    cap3 = LearningCapture(user_id=u1.id, source_type="text", original_text="Question", status="confirmed", version=2, confirmed_at=now - timedelta(days=2))
    db.add(cap3); db.commit()
    obs_q = LearningObservation(
        user_id=u1.id, capture_id=cap3.id, position=0, observation_type="open_question",
        topic="Architecture", content="Microservices vs modular monolith?", evidence="arch", provenance="user_confirmed"
    )
    # 4. Old topic eligible for review (studied 5 days ago)
    cap4 = LearningCapture(user_id=u1.id, source_type="text", original_text="Old study", status="confirmed", version=2, confirmed_at=now - timedelta(days=5))
    db.add(cap4); db.commit()
    obs_old = LearningObservation(
        user_id=u1.id, capture_id=cap4.id, position=0, observation_type="learned",
        topic="Database Indexing", content="B-tree basics", evidence="b-tree", provenance="user_confirmed"
    )
    # 5. Untouched track
    track_empty = LearningTrack(user_id=u1.id, name="Untouched Rust Track")
    db.add(track_empty)
    db.add_all([obs_step, obs_diff, obs_q, obs_old])
    db.commit()

    recs = client.get("/learning/recommendations", headers=headers).json()
    assert len(recs) >= 5

    # Check ordering:
    # 1. intended_next_step (priority high, category rank 1)
    # 2. unresolved_difficulty (priority high, category rank 2)
    # 3. open_question (priority medium, category rank 3)
    # 4. review_suggestion (priority medium/high, category rank 4)
    # 5. start_track (priority low, category rank 6)
    types = [r["type"] for r in recs]
    assert types[0] == "intended_next_step"
    assert types[1] == "unresolved_difficulty"
    assert types[2] == "open_question"
    assert "review_suggestion" in types
    assert "start_track" in types

    # Check provenance accuracy
    next_step_rec = recs[0]
    assert next_step_rec["source_capture_id"] == cap1.id
    assert next_step_rec["source_observation_id"] == obs_step.id
    assert "Write integration tests" in next_step_rec["action"]

    diff_rec = recs[1]
    assert diff_rec["source_capture_id"] == cap2.id
    assert diff_rec["source_observation_id"] == obs_diff.id


def test_existing_recommendation_endpoints_compatibility(db, client, headers, users):
    u1 = users[0]
    cap = LearningCapture(user_id=u1.id, source_type="text", original_text="Study update", status="confirmed", version=2)
    db.add(cap); db.commit()
    obs = LearningObservation(
        user_id=u1.id, capture_id=cap.id, position=0, observation_type="difficulty",
        topic="Concurrency", content="Race conditions", evidence="race", provenance="user_confirmed"
    )
    db.add(obs); db.commit()

    # /recommendations/daily
    daily_res = client.get("/recommendations/daily", headers=headers)
    assert daily_res.status_code == 200
    daily_data = daily_res.json()
    assert "generated_at" in daily_data
    assert "recommendations" in daily_data
    assert len(daily_data["recommendations"]) >= 1
    first_rec = daily_data["recommendations"][0]
    assert "type" in first_rec
    assert "priority" in first_rec
    assert "message" in first_rec

    # /recommendations/weak-areas
    weak_res = client.get("/recommendations/weak-areas", headers=headers)
    assert weak_res.status_code == 200
    assert "recommendations" in weak_res.json()

    # /recommendations/continue-learning
    cont_res = client.get("/recommendations/continue-learning", headers=headers)
    assert cont_res.status_code == 200

    # /recommendations/neglected
    negl_res = client.get("/recommendations/neglected", headers=headers)
    assert negl_res.status_code == 200


def test_review_scheduling_interval_and_recent_acknowledgment(db, client, headers, users):
    u1 = users[0]
    now = datetime.now(timezone.utc)

    # Topic studied 4 days ago -> review due
    cap = LearningCapture(user_id=u1.id, source_type="text", original_text="Docker study", status="confirmed", version=2, confirmed_at=now - timedelta(days=4))
    db.add(cap); db.commit()
    obs = LearningObservation(user_id=u1.id, capture_id=cap.id, position=0, observation_type="learned",
                               topic="Docker", content="Container layers", evidence="layers", provenance="user_confirmed")
    db.add(obs); db.commit()

    checkpoints = client.get("/learning/checkpoints", headers=headers).json()
    docker_cp = [c for c in checkpoints if c["topic"] == "Docker"][0]
    assert docker_cp["review_suggested"] is True
    assert docker_cp["state"] == "review_suggested"

    # User completes a review action for Docker
    client.post("/learning/actions", headers=headers, json={
        "idempotency_key": "review-docker-1",
        "action_type": "review",
        "status": "completed",
        "topic": "Docker",
        "notes": "Reviewed container layer caching"
    })

    # After recent review completion, review is no longer due!
    checkpoints_after = client.get("/learning/checkpoints", headers=headers).json()
    docker_cp_after = [c for c in checkpoints_after if c["topic"] == "Docker"][0]
    assert docker_cp_after["review_suggested"] is False


def test_timezone_streak_dst_and_midnight_boundaries(db, client, headers, users):
    u1 = users[0]
    # Set up study logs near UTC midnight:
    # Day 1: 2026-10-21 23:55:00 UTC
    # In Asia/Kolkata (+5:30), 23:55 UTC is 05:25 on 2026-10-22!
    # In US/Eastern (-4:00 EDT), 23:55 UTC is 19:55 on 2026-10-21!
    log1 = StudyLog(
        user_id=u1.id, topic="Timezone Study", duration_minutes=30, notes="Midnight test",
        created_at=datetime(2026, 10, 21, 23, 55, 0, tzinfo=timezone.utc)
    )
    db.add(log1); db.commit()

    # Query daily activity with different timezones
    res_utc = client.get("/analytics/daily-activity?timezone=UTC", headers=headers).json()
    assert len(res_utc) == 1
    assert res_utc[0]["date"] == "2026-10-21"

    res_kolkata = client.get("/analytics/daily-activity?timezone=Asia/Kolkata", headers=headers).json()
    assert len(res_kolkata) == 1
    assert res_kolkata[0]["date"] == "2026-10-22"

    res_ny = client.get("/analytics/daily-activity?timezone=America/New_York", headers=headers).json()
    assert len(res_ny) == 1
    assert res_ny[0]["date"] == "2026-10-21"

    # Invalid timezone returns 400
    res_invalid = client.get("/analytics/daily-activity?timezone=Mars/Olympus_Mons", headers=headers)
    assert res_invalid.status_code == 400


def test_learning_assistant_deterministic_continuity(db, client, headers, users):
    u1 = users[0]
    now = datetime.now(timezone.utc)
    cap = LearningCapture(user_id=u1.id, source_type="text", original_text="Python study session", status="confirmed", version=2, confirmed_at=now)
    db.add(cap); db.commit()
    db.add_all([
        LearningObservation(user_id=u1.id, capture_id=cap.id, position=0, observation_type="learned",
                            topic="Python", content="List comprehensions syntax", evidence="syntax", provenance="user_confirmed"),
        LearningObservation(user_id=u1.id, capture_id=cap.id, position=1, observation_type="difficulty",
                            topic="Python", content="Generator memory consumption nuance", evidence="generators", provenance="user_confirmed"),
        LearningObservation(user_id=u1.id, capture_id=cap.id, position=2, observation_type="open_question",
                            topic="Python", content="When to use async generators?", evidence="async gen", provenance="user_confirmed"),
        LearningObservation(user_id=u1.id, capture_id=cap.id, position=3, observation_type="intended_next_step",
                            topic="Python", content="Implement streaming file reader", evidence="streaming", provenance="user_confirmed"),
    ])
    db.commit()

    # Deterministic query: "Where did I stop learning Python?"
    res_stop = client.post("/rag/ask", headers=headers, json={"question": "Where did I stop learning Python?"})
    assert res_stop.status_code == 200
    data_stop = res_stop.json()
    assert "last recorded learning about 'Python'" in data_stop["answer"]
    assert len(data_stop["sources"]) >= 1
    assert data_stop["sources"][0]["observation_id"] is not None

    # Deterministic query: "What was I struggling with?"
    res_diff = client.post("/rag/ask", headers=headers, json={"question": "What was I struggling with last time?"})
    assert res_diff.status_code == 200
    assert "Generator memory consumption nuance" in res_diff.json()["answer"]

    # Deterministic query: "What should I practice next?"
    res_next = client.post("/rag/ask", headers=headers, json={"question": "What should I practice next?"})
    assert res_next.status_code == 200
    assert "Implement streaming file reader" in res_next.json()["answer"]

    # Deterministic query: "What questions did I leave unanswered?"
    res_q = client.post("/rag/ask", headers=headers, json={"question": "What open questions do I have?"})
    assert res_q.status_code == 200
    assert "When to use async generators?" in res_q.json()["answer"]


def test_learning_assistant_without_memory_embeddings(db, client, headers, users, monkeypatch):
    u1 = users[0]
    # Confirmed capture with create_memories=False (no Memory or MemoryEmbedding rows)
    cap = LearningCapture(user_id=u1.id, source_type="text", original_text="FastAPI routers", status="confirmed", version=2)
    db.add(cap); db.commit()
    obs = LearningObservation(
        user_id=u1.id, capture_id=cap.id, position=0, observation_type="learned",
        topic="APIRouter", content="APIRouter helps structure large applications", evidence="APIRouter", provenance="user_confirmed"
    )
    db.add(obs); db.commit()
    assert db.query(Memory).count() == 0

    # Mock LLM generation and embedding
    mock_llm = Mock(return_value="APIRouter is used for structuring according to [Observation 1].")
    monkeypatch.setattr(rag_module.llm_service, "generate_response", mock_llm)
    monkeypatch.setattr(rag_module, "generate_embedding", Mock(return_value=[0.1] * 768))

    res = client.post("/rag/ask", headers=headers, json={"question": "Tell me about APIRouter structure"})
    assert res.status_code == 200
    data = res.json()
    assert "APIRouter" in data["answer"]
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["source_type"] == "observation"
