"""Opt-in real PostgreSQL/pgvector checks; SQLite never validates vector search."""
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db.database import Base
from app.crud import memory as crud
from app.crud.retrieval import search_memories_by_embedding
from app.models.user import User
from app.models.memory_embedding import MemoryEmbedding
from app.schemas.memory import MemoryCreate, MemoryUpdate
from test_history import test_track_deletion_preserves_history as check_history

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_engine():
    value = os.environ.get("PHASE1_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Set PHASE1_TEST_DATABASE_URL to an explicitly disposable local pgvector database")
    url = make_url(value)
    if (url.get_backend_name() != "postgresql" or url.host not in ("localhost", "127.0.0.1")
            or url.database != "cme_phase1_test"):
        pytest.fail("PostgreSQL tests require a loopback database named cme_phase1_test")
    # No production URL fallback; only this run's randomly named schema is removed.
    engine = create_engine(url)
    schema = "phase1_" + uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped = create_engine(url.update_query_dict({"options": f"-csearch_path={schema},public"}))
    try:
        yield scoped
    finally:
        scoped.dispose()
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


@pytest.fixture
def postgres_db(postgres_engine):
    migrate(postgres_engine)
    with Session(postgres_engine) as session:
        yield session


def migrate(engine, revision="head"):
    from alembic import command
    from alembic.config import Config
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False).replace("%", "%%"))
    command.upgrade(config, revision)


def test_empty_database_bootstrap(postgres_engine):
    from sqlalchemy import inspect
    migrate(postgres_engine)
    assert set(Base.metadata.tables) <= set(inspect(postgres_engine).get_table_names())


@pytest.mark.parametrize("revision", ["3d0e118a4fdf", "305e4c8b7844", "903ce59b718d"])
def test_earlier_revision_upgrade_preserves_data(postgres_engine, revision):
    migrate(postgres_engine, revision)
    with postgres_engine.begin() as connection:
        connection.execute(text("INSERT INTO users (username,email,hashed_password) VALUES ('existing','existing@example.com','synthetic')"))
        connection.execute(text("INSERT INTO study_logs (user_id,topic,duration_minutes" + (",notes" if revision != "3d0e118a4fdf" else "") + ") VALUES (1,'Existing topic',15" + (",'Existing notes'" if revision != "3d0e118a4fdf" else "") + ")"))
    migrate(postgres_engine)
    with postgres_engine.connect() as connection:
        assert connection.scalar(text("SELECT topic FROM study_logs WHERE id=1")) == "Existing topic"
        assert connection.scalar(text("SELECT username FROM users WHERE id=1")) == "existing"


def seed_users(db):
    users = [User(username=f"pg{i}", email=f"pg{i}@example.com", hashed_password="unused") for i in (1, 2)]
    db.add_all(users)
    db.commit()
    return users


@pytest.mark.parametrize("mode", ["orm_loaded", "orm_unloaded", "database"])
def test_postgres_history(postgres_db, mode):
    check_history(postgres_db, seed_users(postgres_db), mode)


def test_pgvector_storage_uniqueness_and_owner_search(postgres_db, monkeypatch):
    db = postgres_db
    users = seed_users(db)
    monkeypatch.setattr(crud, "generate_embedding", lambda _: [1.0] + [0.0] * 767)
    memory = crud.create_memory(db, MemoryCreate(title="Title", content="Text", category="test"), users[0].id)
    results = search_memories_by_embedding(db, users[0].id, [1.0] + [0.0] * 767)
    assert [result.id for result, _ in results] == [memory.id]
    assert results[0][1] == pytest.approx(0)
    assert search_memories_by_embedding(db, users[1].id, [1.0] + [0.0] * 767) == []
    crud.update_memory(db, memory, MemoryUpdate(content="Updated"))
    assert db.query(MemoryEmbedding).count() == 1
    assert db.scalar(text("SELECT vector_dims(embedding) FROM memory_embeddings")) == 768
    # PostgreSQL enforces the existing one-embedding-per-memory unique constraint.
    from sqlalchemy.exc import IntegrityError
    db.add(MemoryEmbedding(memory_id=memory.id, model_name="duplicate", embedding=[1.0] * 768))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.query(MemoryEmbedding).count() == 1


def test_legacy_head_with_manually_created_tables(postgres_engine):
    from app.models.conversation import Conversation
    from app.models.usage_limit import UsageLimit
    migrate(postgres_engine, "903ce59b718d")
    with postgres_engine.begin() as connection:
        Conversation.__table__.create(connection)
        UsageLimit.__table__.create(connection)
        connection.execute(text("INSERT INTO users (username,email,hashed_password) VALUES ('legacy','legacy@example.com','synthetic')"))
        connection.execute(text("INSERT INTO conversations (user_id,message,response) VALUES (1,'Synthetic message','Synthetic answer')"))
        connection.execute(text("INSERT INTO usage_limits (user_id,daily_requests,monthly_requests) VALUES (1,2,7)"))
        from app.models.memory import Memory
        connection.execute(Memory.__table__.insert().values(user_id=1, title="Existing memory", content="Preserve this", category="test"))
        connection.execute(MemoryEmbedding.__table__.insert().values(memory_id=1, model_name="synthetic-model", embedding=[1.0] + [0.0] * 767))
    migrate(postgres_engine)
    with postgres_engine.connect() as connection:
        assert connection.scalar(text("SELECT message FROM conversations")) == "Synthetic message"
        assert connection.scalar(text("SELECT monthly_requests FROM usage_limits")) == 7
        assert connection.scalar(text("SELECT content FROM memories WHERE id=1")) == "Preserve this"
        assert connection.scalar(text("SELECT model_name FROM memory_embeddings WHERE memory_id=1")) == "synthetic-model"


@pytest.mark.parametrize("mode", ["duplicate_confirm", "discard_during_preparation"])
def test_capture_concurrency(postgres_db, monkeypatch, mode):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Event
    from fastapi import HTTPException
    from app.models.learning_capture import LearningCapture, LearningObservation
    from app.models.memory import Memory
    from app.schemas.capture import ConfirmInput
    from app.services import capture_service as service
    from app.routes.capture import safe_write
    db = postgres_db
    user_id = seed_users(db)[0].id
    capture = LearningCapture(user_id=user_id, original_text="Synthetic input", source_type="text", status="pending", version=1)
    db.add(capture); db.commit()
    capture_id = capture.id
    payload = ConfirmInput(expected_version=1, create_memories=True, interpretation={"subject": "Python", "duration_minutes": 10,
        "observations": [{"observation_type": "learned", "topic": "Python", "content": "Synthetic learning"}]})
    barrier = Barrier(2)
    prepared, discarded = Event(), Event()
    def vector(_):
        if mode == "duplicate_confirm": barrier.wait(timeout=10)
        else:
            prepared.set()
            assert discarded.wait(timeout=10)
        return [1.0] + [0.0] * 767
    monkeypatch.setattr(service, "validated_embedding", vector)
    def confirm():
        with Session(db.bind) as session:
            with safe_write(session):
                try:
                    return service.confirm(session, capture_id, user_id, payload).status
                except HTTPException as error:
                    return error.status_code
    def discard():
        assert prepared.wait(timeout=10)
        with Session(db.bind) as session:
            item = service.owned(session, capture_id, user_id, lock=True)
            item.status = "discarded"; item.version += 1; session.commit()
        discarded.set()
        return "discarded"
    db.rollback()
    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(confirm)
        two = pool.submit(confirm if mode == "duplicate_confirm" else discard)
        results = [one.result(timeout=20), two.result(timeout=20)]
    db.expire_all()
    if mode == "duplicate_confirm":
        assert results == ["confirmed", "confirmed"]
        assert db.query(LearningObservation).count() == db.query(Memory).count() == db.query(MemoryEmbedding).count() == 1
        assert db.scalar(text("SELECT count(*) FROM study_logs")) == 1
    else:
        assert results == [409, "discarded"]
        assert db.query(LearningObservation).count() == db.query(Memory).count() == db.query(MemoryEmbedding).count() == 0
        assert db.scalar(text("SELECT count(*) FROM study_logs")) == 0


def test_capture_database_constraints(postgres_db):
    from app.models.learning_capture import LearningCapture, LearningObservation
    from sqlalchemy.exc import IntegrityError
    db = postgres_db
    users = seed_users(db)
    ids = [user.id for user in users]
    capture = LearningCapture(user_id=ids[0], source_type="text", original_text="Synthetic", status="pending", version=1)
    db.add(capture); db.commit(); capture_id = capture.id
    for values in [{"user_id": ids[1], "provenance": "user_confirmed", "observation_type": "learned"},
                   {"user_id": ids[0], "provenance": "llm_confirmed", "observation_type": "learned"},
                   {"user_id": ids[0], "provenance": "user_confirmed", "observation_type": "mastered"}]:
        db.add(LearningObservation(capture_id=capture_id, position=0, topic="Topic", content="Text", evidence="", **values))
        with pytest.raises(IntegrityError): db.commit()
        db.rollback()
    for _ in range(2):
        db.add(LearningObservation(capture_id=capture_id, user_id=ids[0], position=0, observation_type="learned", topic="Topic", content="Text", evidence="", provenance="user_confirmed"))
    with pytest.raises(IntegrityError): db.commit()
    db.rollback()


def test_unversioned_legacy_baseline_preserved(postgres_engine):
    with postgres_engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, email VARCHAR(255) NOT NULL UNIQUE, hashed_password VARCHAR(255) NOT NULL, created_at TIMESTAMPTZ DEFAULT now())"))
        connection.execute(text("CREATE TABLE study_logs (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), topic VARCHAR(255) NOT NULL, duration_minutes INTEGER NOT NULL, created_at TIMESTAMPTZ DEFAULT now())"))
        connection.execute(text("INSERT INTO users (username,email,hashed_password) VALUES ('legacy','legacy@example.com','synthetic')"))
        connection.execute(text("INSERT INTO study_logs (user_id,topic,duration_minutes) VALUES (1,'Legacy',12)"))
    migrate(postgres_engine)
    with postgres_engine.connect() as connection:
        assert connection.scalar(text("SELECT duration_minutes FROM study_logs WHERE id=1")) == 12


def test_explicit_migration_environment_url(postgres_engine, monkeypatch):
    from alembic import command
    from alembic.config import Config
    monkeypatch.setenv("ALEMBIC_DATABASE_URL", postgres_engine.url.render_as_string(hide_password=False))
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", "")
    command.upgrade(config, "head")
    with postgres_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "f20200000002"


def test_migration_needs_no_application_database_setting(postgres_engine):
    import subprocess
    import sys
    env = {key: value for key, value in os.environ.items() if key not in ("DATABASE_URL", "SECRET_KEY", "GEMINI_API_KEY")}
    env["PYTHON_DOTENV_DISABLED"] = "1"
    env["ALEMBIC_DATABASE_URL"] = postgres_engine.url.render_as_string(hide_password=False)
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, capture_output=True, timeout=30)
    assert result.returncode == 0, "Isolated Alembic bootstrap failed without app settings"
    with postgres_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "f20200000002"
