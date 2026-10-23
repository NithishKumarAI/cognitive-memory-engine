"""Historical recall without live AI/model assets or application data."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from sqlalchemy import event
from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.learning_track import LearningTrack
from app.models.learning_action import LearningAction
from app.models.memory import Memory
from app.models.memory_embedding import MemoryEmbedding
from app.services import rag_service as rag
from app.services import continuity_service as continuity
from app.services.observation_retrieval import search_confirmed_observations, recall_terms, MAX_TERMS


def seed_observation(db, uid, topic="Python decorators", content="Closures retain state in decorated functions", *, kind="difficulty", status="confirmed", age=150, track_id=None, evidence="Synthetic source"):
    stamp = datetime.now(timezone.utc) - timedelta(days=age)
    capture = LearningCapture(user_id=uid, source_type="text", original_text=content, status=status, version=2,
        learning_track_id=track_id, created_at=stamp, confirmed_at=stamp if status == "confirmed" else None)
    db.add(capture); db.flush()
    observation = LearningObservation(user_id=uid, capture_id=capture.id, position=0, observation_type=kind,
        topic=topic, content=content, evidence=evidence, provenance="user_confirmed", created_at=stamp)
    db.add(observation); db.flush()
    return capture, observation


def seed_noise(db, uid, count=130):
    for index in range(count):
        seed_observation(db, uid, f"Gardening {index}", "Water seedlings in sunlight", kind="learned", age=0)
    db.commit()


@pytest.mark.parametrize("newer", [35, 130])
def test_general_recall_finds_old_confirmed_evidence_without_any_embeddings(db, users, client, headers, monkeypatch, newer):
    uid = users[0].id
    seed_observation(db, users[1].id, content="Private other account")
    capture, old = seed_observation(db, uid)
    oid, cid = old.id, capture.id
    seed_noise(db, uid, newer)
    assert oid not in [row.id for row in db.query(LearningObservation.id).filter_by(user_id=uid).order_by(LearningObservation.id.desc()).limit(30)]
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == 0
    embedding = Mock(side_effect=AssertionError("Observation-only recall must not initialize a model"))
    monkeypatch.setattr(rag, "generate_embedding", embedding)
    llm = Mock(return_value=f"Your saved difficulty is described in [Observation {oid}].")
    monkeypatch.setattr(rag.llm_service, "generate_response", llm)
    response = client.post("/rag/ask", headers=headers, json={"question":"Explain Python decorators from months ago"})
    assert response.status_code == 200
    from app.schemas.rag import RAGResponse
    result = RAGResponse.model_validate(response.json())
    assert result.sources[0].observation_id == oid and result.sources[0].capture_id == cid
    assert f"[Observation {oid}]" in result.answer and "retain state" in llm.call_args.args[0]
    embedding.assert_not_called()
    matches = client.get("/search?q=Python", headers=headers).json()
    assert next(row for row in matches if row["kind"] == "observation")["url"] == f"/dashboard/capture?capture={cid}#observation-{oid}"


def test_only_owned_confirmed_records_are_candidates_and_topic_relevance_precedes_recency(db, users):
    uid = users[0].id
    _, old = seed_observation(db, uid, topic="Python decorators")
    _, recent = seed_observation(db, uid, topic="Other topic", content="Python decorators mentioned in passing", age=0)
    for status in ["pending", "failed", "discarded"]:
        seed_observation(db, uid, status=status, age=0)
    seed_observation(db, users[1].id, age=0); db.commit()
    result = search_confirmed_observations(db, uid, "Explain Python decorators")
    assert [row.id for row in result] == [old.id, recent.id]
    assert len(search_confirmed_observations(db, users[1].id, "Python decorators")) == 1


def test_query_and_context_bounds_with_memory_and_observation_sources(db, users, monkeypatch):
    uid = users[0].id
    for index in range(25): seed_observation(db, uid, content="Python " + "x" * 20000, evidence="e" * 20000)
    memory = Memory(user_id=uid, title="M" * 20000, content="Python " + "m" * 50000, category="c" * 5000)
    db.add(memory); db.flush()
    db.add(MemoryEmbedding(memory_id=memory.id, model_name="synthetic", embedding=[1.0] + [0.0]*767)); db.commit()
    mid = memory.id
    fake = SimpleNamespace(id=mid, title=memory.title, content=memory.content, category=memory.category)
    retrieve = Mock(return_value=[(fake, 0.1)] * 20)
    monkeypatch.setattr(rag, "search_memories_by_embedding", retrieve)
    monkeypatch.setattr(rag, "generate_embedding", Mock(return_value=[1.0] + [0.0]*767))
    llm = Mock(return_value=f"Use [Memory {mid}] and the supplied observations.")
    monkeypatch.setattr(rag.llm_service, "generate_response", llm)
    db.expunge_all(); loaded = []
    def load(session, instance): loaded.append(type(instance).__name__)
    event.listen(db, "loaded_as_persistent", load)
    try:
        rows = search_confirmed_observations(db, uid, "Python")
        assert len(rows) == 5 and all(len(row.content) <= 2000 and len(row.evidence) <= 400 for row in rows)
        assert "LearningObservation" not in loaded
        result = rag.rag_service.generate_answer(db, uid, "Python " * 2000, top_k=20)
    finally: event.remove(db, "loaded_as_persistent", load)
    assert len(result["sources"]) <= 10
    assert len(llm.call_args.args[0]) <= rag.MAX_PROMPT_CHARS
    assert "[excerpt truncated]" in llm.call_args.args[0]
    assert retrieve.call_args.kwargs["limit"] == 5 and retrieve.call_args.kwargs["body_limit"] == 2000
    assert all(len(source["title"]) <= 213 and len(source.get("evidence") or "") <= 400 for source in result["sources"])


@pytest.mark.parametrize("question", ["Tell me what I learned", "Explain quantum entanglement", "what did I study %_ ' OR 1=1 --"])
def test_insufficient_or_unrelated_history_does_not_generate(db, users, monkeypatch, question):
    uid = users[0].id
    seed_observation(db, uid); seed_noise(db, uid, 40)
    llm = Mock(side_effect=AssertionError("No generation without relevant evidence"))
    monkeypatch.setattr(rag.llm_service, "generate_response", llm)
    result = rag.rag_service.generate_answer(db, uid, question)
    assert result == {"answer":"The information is not available in memory.","sources":[]}
    llm.assert_not_called()


def test_term_bounds_are_literal_and_deterministic():
    assert recall_terms("What did I learn about Python decorators months ago?") == ("python", "decorators")
    assert len(recall_terms("alpha beta gamma delta epsilon zeta eta theta iota kappa")) == MAX_TERMS
    assert recall_terms("%_ ' -- 123") == ()
    assert recall_terms("SQL C++ C#") == ("sql", "c++", "c#")


def test_old_continuity_and_track_identity_survive_recent_display_caps(db, users, client, headers):
    uid = users[0].id
    tracks = [LearningTrack(user_id=uid, name=name) for name in ["Python applications", "Python internals"]]
    db.add_all(tracks); db.flush()
    old_records = [seed_observation(db, uid, track_id=assigned, content=f"Old difficulty {index}") for index, assigned in enumerate([tracks[0].id, tracks[1].id, None])]
    _, completed = seed_observation(db, uid, kind="intended_next_step", content="Already completed", track_id=tracks[0].id)
    _, pending = seed_observation(db, uid, kind="intended_next_step", content="Write decorator examples", track_id=tracks[1].id)
    db.add(LearningAction(user_id=uid, idempotency_key="synthetic-completed", action_type="next_step", status="completed", observation_id=completed.id))
    seed_observation(db, users[1].id, content="Private Python difficulty")
    expected = {row.id for _, row in old_records}; pending_id = pending.id; complete_id = completed.id
    seed_noise(db, uid, 130)
    assert not expected.intersection(cp.latest_observation_id for cp in continuity.get_resumable_checkpoints(db, uid, limit=20))
    for question in ["What was I struggling with in Python decorators?", "Where did I stop learning Python decorators?"]:
        result = client.post("/rag/ask", headers=headers, json={"question":question}).json()
        assert result["sources"] and all(source["capture_id"] in {cap.id for cap, _ in old_records} | {pending.capture_id} for source in result["sources"])
        assert "Private" not in result["answer"]
    result = client.post("/rag/ask", headers=headers, json={"question":"What were my next steps for Python decorators?"}).json()
    assert "Write decorator examples" in result["answer"] and "Already completed" not in result["answer"]
    recommendations = continuity.generate_evidence_recommendations(db, uid, limit=50)
    assert expected <= {rec.source_observation_id for rec in recommendations if rec.type == "unresolved_difficulty"}
    assert pending_id in {rec.source_observation_id for rec in recommendations}
    assert complete_id not in {rec.source_observation_id for rec in recommendations if rec.type == "intended_next_step"}
    assert {rec.learning_track_id for rec in recommendations if rec.type == "unresolved_difficulty"} == {tracks[0].id, tracks[1].id, None}
    overview = continuity.get_learning_overview(db, uid)
    assert overview.unresolved_difficulties_count == 3 and overview.pending_next_actions_count == 1


def test_unknown_explicit_topic_does_not_fall_back_to_an_unrelated_checkpoint(db, users, client, headers):
    seed_observation(db, users[0].id); db.commit()
    result = client.post("/rag/ask", headers=headers, json={"question":"Where did I stop learning astrophysics?"}).json()
    assert result["sources"] == [] and "No confirmed learning checkpoint" in result["answer"]


def test_low_relevance_substrings_do_not_become_word_matches(db, users):
    seed_observation(db, users[0].id, topic="Trust management", content="Trust is important in teams")
    db.commit()
    assert search_confirmed_observations(db, users[0].id, "Explain Rust") == []


@pytest.mark.parametrize("topic", ["C++", "C#", "SQL"])
def test_short_technical_terms_are_supported(db, users, topic):
    _, observation = seed_observation(db, users[0].id, topic=topic)
    db.commit()
    assert search_confirmed_observations(db, users[0].id, f"Explain {topic}")[0].id == observation.id


@pytest.mark.parametrize("question", ["What was I struggling with in Rust?", "What open questions do I have about Rust?"])
def test_topic_filtered_empty_answer_does_not_deny_other_historical_difficulties(db, users, client, headers, question):
    seed_observation(db, users[0].id); db.commit()
    result = client.post("/rag/ask", headers=headers, json={"question":question}).json()
    assert result["sources"] == [] and "match this question" in result["answer"]
