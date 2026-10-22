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
        assert connection.scalar(text("SELECT count(*) FROM pg_extension WHERE extname='vector'")) == 1
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
    with postgres_engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            table.create(connection)
    with Session(postgres_engine) as session:
        yield session


def test_empty_database_bootstrap_blocker(postgres_engine):
    # Demonstrate the historical blocker; a passing test means the failure
    # was reproduced, not that migrations are bootstrap-ready.
    from alembic import command
    from alembic.config import Config
    from sqlalchemy.exc import ProgrammingError
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_engine.url.render_as_string(hide_password=False).replace("%", "%%"))
    with pytest.raises(ProgrammingError) as failure:
        command.upgrade(config, "head")
    assert 'relation "study_logs" does not exist' in str(failure.value.orig)


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
