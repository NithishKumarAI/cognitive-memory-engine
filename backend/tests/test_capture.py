import io
import json
import wave
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from app.models.learning_capture import LearningCapture, LearningObservation
from app.models.learning_track import LearningTrack
from app.models.memory import Memory
from app.models.memory_embedding import MemoryEmbedding
from app.models.study_log import StudyLog
from app.schemas.capture import Interpretation
from app.services import capture_service as service
from app.services.extraction_service import extract_learning
from app.services.llm_service import llm_service, LLMService, ProviderUnavailable

TEXT = "Today I studied Python decorators. Closures are confusing. Tomorrow I want to solve three problems."
PROPOSAL = {"subject": "Python", "topics": ["Decorators", "Closures"], "observations": [
    {"observation_type": "learned", "topic": "Decorators", "content": "Studied decorators", "evidence": "studied Python decorators"},
    {"observation_type": "difficulty", "topic": "Closures", "content": "Closures are confusing", "evidence": "Closures are confusing"},
    {"observation_type": "intended_next_step", "topic": "Practice", "content": "Solve three problems", "evidence": "solve three problems"}],
    "duration_minutes": None, "duration_evidence": None, "ambiguity": None}


@pytest.fixture
def ai(monkeypatch):
    mock = Mock(return_value=json.dumps(PROPOSAL))
    monkeypatch.setattr(llm_service, "generate", mock)
    monkeypatch.setattr(service, "validated_embedding", lambda _: [0.1] * 768)
    return mock


def draft(client, headers, text=TEXT, **fields):
    result = client.post("/capture/analyze", headers=headers, json={"text": text, **fields})
    assert result.status_code == 200, result.status_code
    return result.json()


def confirmation(capture, **fields):
    return {"expected_version": capture["version"], "interpretation": deepcopy(PROPOSAL),
            "learning_track_id": None, "create_memories": True, **fields}


def test_preview_and_corrected_confirmation(client, db, headers, ai):
    capture = draft(client, headers)
    assert db.query(Memory).count() == db.query(LearningObservation).count() == 0
    payload = confirmation(capture)
    payload["interpretation"]["observations"][0]["content"] = "My corrected observation"
    result = client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=payload)
    assert result.status_code == 200
    saved = result.json()
    assert saved["status"] == "confirmed" and saved["original_text"] == TEXT
    assert saved["proposed_interpretation"]["observations"][0]["content"] == "Studied decorators"
    assert saved["confirmed_interpretation"]["observations"][0]["content"] == "My corrected observation"
    assert saved["observations"][0]["provenance"] == "user_confirmed"
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == db.query(LearningObservation).count() == 3
    assert db.query(StudyLog).count() == 0
    again = client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=payload)
    assert again.status_code == 200
    assert [o["id"] for o in again.json()["observations"]] == [o["id"] for o in saved["observations"]]
    assert db.query(MemoryEmbedding).count() == 3
    payload["interpretation"]["subject"] = "Different"
    assert client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=payload).status_code == 409


@pytest.mark.parametrize("duration", [None, 20])
def test_optional_duration_and_memory_opt_in(client, db, headers, ai, duration):
    capture = draft(client, headers)
    payload = confirmation(capture, create_memories=False)
    payload["interpretation"]["duration_minutes"] = duration
    response = client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=payload)
    assert response.status_code == 200
    assert db.query(StudyLog).count() == (1 if duration else 0)
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == 0
    if duration:
        assert db.query(StudyLog).one().duration_minutes == duration


@pytest.mark.parametrize("failure", ["embedding", "flush", "commit"])
def test_confirmation_failure_is_atomic_and_retryable(client, db, headers, ai, monkeypatch, failure):
    capture = draft(client, headers)
    payload = confirmation(capture)
    payload["interpretation"]["duration_minutes"] = 10
    def fail(*args, **kwargs):
        raise RuntimeError("private prompt and credentials")
    with monkeypatch.context() as patch:
        if failure == "embedding":
            patch.setattr(service, "validated_embedding", fail)
        elif failure == "commit":
            patch.setattr(db, "commit", fail)
        else:
            event.listen(LearningObservation, "before_insert", fail)
        try:
            response = client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=payload)
        finally:
            if failure == "flush":
                event.remove(LearningObservation, "before_insert", fail)
    assert response.status_code == 503
    assert "private" not in response.text
    assert db.query(StudyLog).count() == db.query(Memory).count() == db.query(MemoryEmbedding).count() == db.query(LearningObservation).count() == 0
    assert db.get(LearningCapture, capture["id"]).status == "pending"
    assert client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=payload).status_code == 200


def test_owner_isolation_and_track_matching(client, db, users, headers, ai):
    from app.core.auth import create_access_token
    other_headers = {"Authorization": "Bearer " + create_access_token({"sub": users[1].email})}
    tracks = [LearningTrack(user_id=users[0].id, name=" PYTHON "), LearningTrack(user_id=users[0].id, name="python"), LearningTrack(user_id=users[1].id, name="Python")]
    db.add_all(tracks); db.commit()
    capture = draft(client, headers)
    assert set(capture["matching_track_ids"]) == {tracks[0].id, tracks[1].id}
    assert capture["learning_track_id"] is None
    assert len(client.get("/capture", headers=headers).json()) == 1
    assert client.get("/capture", headers=other_headers).json() == []
    for method, suffix, payload in [("get", "", None), ("post", "/confirm", confirmation(capture)), ("post", "/discard", {"expected_version": capture["version"]}), ("post", "/analyze", {"expected_version": capture["version"]})]:
        kwargs = {"json": payload} if payload else {}
        assert getattr(client, method)(f"/capture/{capture['id']}{suffix}", headers=other_headers, **kwargs).status_code == 404
    assert client.post("/capture/analyze", headers=headers, json={"text": TEXT, "learning_track_id": tracks[2].id}).status_code == 400
    assert client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=confirmation(capture, learning_track_id=tracks[2].id)).status_code == 400
    assert db.query(LearningTrack).count() == 3


@pytest.mark.parametrize("output", [TimeoutError("private"), "not json", '{"duration_minutes": 0}', json.dumps({**PROPOSAL, "invented": "not allowed"})])
def test_failed_analysis_retains_raw_input_and_can_retry(client, db, headers, ai, output):
    if isinstance(output, Exception): ai.side_effect = output
    else: ai.return_value = output
    capture = draft(client, headers)
    assert capture["status"] == "failed" and capture["proposed_interpretation"] is None
    assert db.get(LearningCapture, capture["id"]).original_text == TEXT
    ai.side_effect = None; ai.return_value = json.dumps(PROPOSAL)
    retried = client.post(f"/capture/{capture['id']}/analyze", headers=headers, json={"expected_version": capture["version"]})
    assert retried.status_code == 200 and retried.json()["status"] == "pending"


def test_failed_analysis_can_be_manually_confirmed(client, db, headers, ai):
    ai.side_effect = TimeoutError()
    capture = draft(client, headers)
    assert client.post(f"/capture/{capture['id']}/confirm", headers=headers, json=confirmation(capture)).status_code == 200
    assert db.query(LearningObservation).count() == 3


def test_no_transaction_open_during_analysis(client, db, headers, ai):
    def provider(*_):
        assert not db.in_transaction()
        return json.dumps(PROPOSAL)
    ai.side_effect = provider
    assert draft(client, headers)["status"] == "pending"


def test_discard_and_stale_updates(client, db, headers, ai):
    capture = draft(client, headers)
    url = f"/capture/{capture['id']}"
    assert client.post(url + "/confirm", headers=headers, json=confirmation(capture, expected_version=999)).status_code == 409
    response = client.post(url + "/discard", headers=headers, json={"expected_version": capture["version"]})
    assert response.status_code == 200 and response.json()["status"] == "discarded"
    assert response.json()["original_text"] == TEXT
    assert client.post(url + "/confirm", headers=headers, json=confirmation(capture)).status_code == 409
    assert client.post(url + "/analyze", headers=headers, json={"expected_version": capture["version"]}).status_code == 409
    assert db.query(LearningObservation).count() == 0


@pytest.mark.parametrize("path,method,payload", [("/capture", "get", None), ("/capture/1", "get", None), ("/capture/analyze", "post", {"text": TEXT}), ("/capture/1/confirm", "post", {}), ("/capture/1/discard", "post", {"expected_version": 1}), ("/capture/transcribe", "post", None)])
def test_capture_auth(client, path, method, payload):
    assert getattr(client, method)(path, **({"json": payload} if payload else {})).status_code == 401


@pytest.mark.parametrize("text,interpretation", [
    ("Studied Python", {"subject": "Python", "topics": ["Python", " python "], "observations": [{"observation_type": "learned", "topic": "Python", "content": "Studied Python", "evidence": "Studied Python"}]}),
    (TEXT, PROPOSAL),
    ("Something about coding", {"ambiguity": "No specific learning claim was stated"}),
    ("What are closures?", {"observations": [{"observation_type": "open_question", "topic": "Closures", "content": "What are closures?", "evidence": "What are closures?"}]}),
    ("I will practice tomorrow", {"observations": [{"observation_type": "intended_next_step", "topic": "Practice", "content": "Practice tomorrow", "evidence": "practice tomorrow"}]}),
    ("Studied for 2 hours", {"duration_minutes": 120, "duration_evidence": "2 hours"}),
])
def test_structured_extraction(ai, text, interpretation):
    ai.return_value = json.dumps(interpretation)
    result = extract_learning(text)
    assert result.duration_minutes == interpretation.get("duration_minutes")
    if text == "Studied Python":
        assert result.topics == ["Python"]
    if "?" in text: assert result.observations[0].observation_type == "open_question"


@pytest.mark.parametrize("change", [{"duration_minutes": 30, "duration_evidence": "studied Python decorators"}, {"observations": [{"observation_type": "learned", "topic": "Fake", "content": "Fake", "evidence": "not in input"}]}])
def test_unsupported_extraction_rejected(ai, change):
    ai.return_value = json.dumps({**PROPOSAL, **change})
    with pytest.raises(ValueError): extract_learning(TEXT)


def test_supported_sdk_boundary(monkeypatch):
    import app.services.llm_service as module
    monkeypatch.setattr(module, "personal_key", lambda: "synthetic-personal-test-key")
    client = Mock(); client.__enter__ = Mock(return_value=client); client.__exit__ = Mock(return_value=False)
    client.models.generate_content.return_value = SimpleNamespace(text=" Answer ")
    factory = Mock(return_value=client)
    monkeypatch.setattr(module.genai, "Client", factory)
    assert LLMService().generate_response("Synthetic prompt") == "Answer"
    assert client.models.generate_content.call_args.kwargs["model"] == "gemini-2.5-flash"
    assert factory.call_args.kwargs["http_options"].timeout == 30000
    client.models.generate_content.side_effect = TimeoutError("private")
    with pytest.raises(ProviderUnavailable, match="AI service unavailable"):
        LLMService().generate_response("Synthetic prompt")


def wav(seconds=0.1):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as recording:
        recording.setnchannels(1); recording.setsampwidth(2); recording.setframerate(16000)
        recording.writeframes(b"\x00\x00" * int(seconds * 16000))
    return buffer.getvalue()


def test_voice_consent_and_success(client, headers, ai, db):
    audio_headers = {**headers, "Content-Type": "audio/wav"}
    assert client.post("/capture/transcribe", headers=audio_headers, content=wav()).status_code == 400
    ai.assert_not_called()
    ai.return_value = '{"transcript":"A synthetic learning note"}'
    result = client.post("/capture/transcribe", headers={**audio_headers, "X-Audio-Consent": "true"}, content=wav())
    assert result.status_code == 200 and result.json()["transcript"] == "A synthetic learning note"
    assert db.query(LearningCapture).count() == db.query(Memory).count() == 0
    part = ai.call_args.args[0][0]
    assert part.inline_data.mime_type == "audio/wav"


@pytest.mark.parametrize("data,mime,status", [(b"", "audio/wav", 422), (b"not audio", "audio/wav", 422), (b"fake", "audio/mpeg", 422), (b"fake", "audio/webm", 415), (b"a" * (4*1024*1024+1), "audio/wav", 413), (wav(120.1), "audio/wav", 422), (wav()[:-10], "audio/wav", 422)], ids=["empty", "spoofed-wav", "spoofed-mp3", "unsupported-webm", "oversized", "overlong", "truncated"])
def test_audio_validation(client, headers, ai, data, mime, status):
    result = client.post("/capture/transcribe", headers={**headers, "Content-Type": mime, "X-Audio-Consent": "true"}, content=data)
    assert result.status_code == status
    ai.assert_not_called()


@pytest.mark.parametrize("output,status", [(TimeoutError("private"), 503), ("invalid json", 503), ('{"transcript":""}', 422)])
def test_transcription_failure(client, headers, ai, output, status):
    if isinstance(output, Exception): ai.side_effect = output
    else: ai.return_value = output
    result = client.post("/capture/transcribe", headers={**headers, "Content-Type": "audio/wav", "X-Audio-Consent": "true"}, content=wav())
    assert result.status_code == status and "private" not in result.text


@pytest.mark.parametrize("mode", ["extraction", "transcription"])
def test_real_sdk_structured_serialization_without_network(monkeypatch, mode):
    import httpx
    import app.services.llm_service as module
    monkeypatch.setattr(module, "personal_key", lambda: "synthetic-personal-test-key")
    from google.genai import types
    original_client = module.genai.Client
    requests = []
    def handle(request):
        requests.append(json.loads(request.content))
        output = PROPOSAL if mode == "extraction" else {"transcript": "Synthetic transcript"}
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps(output)}]}, "finishReason": "STOP"}]})
    def client(**kwargs):
        return original_client(api_key="synthetic-only", http_options=types.HttpOptions(
            timeout=30000, client_args={"transport": httpx.MockTransport(handle)}))
    monkeypatch.setattr(module.genai, "Client", client)
    monkeypatch.setattr(llm_service, "generate", LLMService().generate)
    if mode == "extraction":
        result = extract_learning(TEXT)
        assert result.subject == "Python"
        assert requests[0]["contents"][0]["parts"][0]["text"] == TEXT
        assert "untrusted data" in requests[0]["systemInstruction"]["parts"][0]["text"]
    else:
        from app.services.audio_service import transcribe
        assert transcribe(wav(), "audio/wav") == "Synthetic transcript"
        inline = requests[0]["contents"][0]["parts"][0]["inlineData"]
        assert inline.get("mimeType", inline.get("mime_type")) == "audio/wav"
    assert requests[0]["generationConfig"]["responseMimeType"] == "application/json"
