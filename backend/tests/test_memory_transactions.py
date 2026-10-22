from unittest.mock import Mock

import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from app.crud import memory as crud
from app.models.memory import Memory
from app.models.memory_embedding import MemoryEmbedding
from app.schemas.memory import MemoryCreate, MemoryUpdate
from app.services.embedding_service import MODEL_NAME


@pytest.fixture
def generate(monkeypatch):
    mock = Mock(return_value=[0.1] * 768)
    monkeypatch.setattr(crud, "generate_embedding", mock)
    return mock


def create(db, users):
    return crud.create_memory(db, MemoryCreate(title="Before", content="Text",
                                               category="test"), users[0].id)


def test_create_and_update(db, users, generate):
    memory = create(db, users)
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == 1
    assert memory.embedding.model_name == MODEL_NAME
    assert len(memory.embedding.embedding) == 768
    generate.return_value = [0.2] * 768
    crud.update_memory(db, memory, MemoryUpdate(title="After", content="New"))
    db.expire_all()
    assert memory.title == "After" and memory.content == "New"
    assert list(memory.embedding.embedding) == pytest.approx([0.2] * 768)
    assert db.query(MemoryEmbedding).count() == 1


@pytest.mark.parametrize("bad", [RuntimeError("private failure"), [1.0], [float("nan")] * 768])
def test_failed_create_has_no_partial_rows(db, users, generate, bad):
    if isinstance(bad, Exception):
        generate.side_effect = bad
    else:
        generate.return_value = bad
    with pytest.raises((RuntimeError, ValueError)):
        create(db, users)
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == 0


def test_failed_update_preserves_previous_values(db, users, generate):
    memory = create(db, users)
    generate.side_effect = RuntimeError("private failure")
    with pytest.raises(RuntimeError):
        crud.update_memory(db, memory, MemoryUpdate(content="Changed", category="new"))
    db.expire_all()
    assert memory.content == "Text" and memory.category == "test"
    assert list(memory.embedding.embedding) == pytest.approx([0.1] * 768)


@pytest.mark.parametrize("update", [MemoryUpdate(), MemoryUpdate(title="Before", content="Text"),
                                   MemoryUpdate(category="new"), MemoryUpdate(study_log_id=None)])
def test_unchanged_text_does_not_generate(db, users, generate, update):
    memory = create(db, users)
    generate.reset_mock()
    crud.update_memory(db, memory, update)
    generate.assert_not_called()


@pytest.mark.parametrize("operation", ["create", "update"])
def test_database_failure_rolls_back(db, users, generate, operation):
    memory = create(db, users) if operation == "update" else None
    generate.return_value = [0.2] * 768
    def fail(*_):
        raise IntegrityError("test failure", None, Exception("private"))
    event_name = "before_update" if memory else "before_insert"
    event.listen(MemoryEmbedding, event_name, fail)
    try:
        with pytest.raises(IntegrityError):
            if memory:
                crud.update_memory(db, memory, MemoryUpdate(content="Changed"))
            else:
                create(db, users)
    finally:
        event.remove(MemoryEmbedding, event_name, fail)
    db.expire_all()
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == bool(memory)
    if memory:
        assert memory.content == "Text"
        assert list(memory.embedding.embedding) == pytest.approx([0.1] * 768)


def test_api_failure_is_sanitized(client, headers, generate):
    generate.side_effect = RuntimeError("private credentials")
    response = client.post("/memories", headers=headers,
                           json={"title": "Title", "content": "Text", "category": "test"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Unable to save memory"}


@pytest.mark.parametrize("operation", ["create", "update"])
def test_commit_failure_rolls_back(db, users, generate, monkeypatch, operation):
    memory = create(db, users) if operation == "update" else None
    def fail():
        raise IntegrityError("commit failed", None, Exception("private"))
    monkeypatch.setattr(db, "commit", fail)
    with pytest.raises(IntegrityError):
        if memory:
            crud.update_memory(db, memory, MemoryUpdate(title="Changed"))
        else:
            create(db, users)
    db.expire_all()
    assert db.query(Memory).count() == db.query(MemoryEmbedding).count() == bool(memory)
    if memory:
        assert memory.title == "Before"


def test_missing_embedding_recreated_once(db, users, generate):
    memory = create(db, users)
    db.delete(memory.embedding)
    db.commit()
    crud.update_memory(db, memory, MemoryUpdate(title="Changed"))
    assert db.query(MemoryEmbedding).count() == 1


def test_sentence_transformer_is_not_imported():
    import sys
    assert "sentence_transformers" not in sys.modules
