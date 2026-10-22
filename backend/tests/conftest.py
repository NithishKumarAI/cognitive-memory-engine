import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Set before any app imports; never read a developer database or secrets.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "phase1-test-signing-key-only"
os.environ["GEMINI_API_KEY"] = "test-only"
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Fail closed if a test accidentally calls the AI boundary.
import app.services.embedding_service as embeddings
embeddings.generate_embedding = Mock(side_effect=AssertionError("Embedding must be mocked"))
import app.services.llm_service as llm
llm.llm_service.generate_response = Mock(side_effect=AssertionError("LLM must be mocked"))
from app.db.database import Base
from app.db.dependencies import get_db
from app.main import app
from app.models.user import User
from app.core.auth import create_access_token


@pytest.fixture
def db():
    engine = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    # Individual tables in a new in-memory store, never a migration workaround.
    for table in Base.metadata.sorted_tables:
        table.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture
def users(db):
    records = [User(username=f"user{i}", email=f"user{i}@example.com",
                    hashed_password="unused") for i in (1, 2)]
    db.add_all(records)
    db.commit()
    return records


@pytest.fixture
def client(db):
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def headers(users):
    return {"Authorization": "Bearer " + create_access_token({"sub": users[0].email})}
