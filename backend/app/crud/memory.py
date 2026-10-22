from math import isfinite

from sqlalchemy.orm import Session

from app.services.embedding_service import (
    generate_embedding,
    MODEL_NAME
)

from app.crud.memory_embedding import (
    create_memory_embedding,
    update_memory_embedding
)

from app.models.memory import Memory
from app.schemas.memory import (
    MemoryCreate,
    MemoryUpdate
)


def validated_embedding(text: str) -> list[float]:
    embedding = [float(value) for value in generate_embedding(text)]
    if len(embedding) != 768 or not all(isfinite(value) for value in embedding):
        raise ValueError("Invalid embedding")
    return embedding


def stage_memory(db: Session, memory: MemoryCreate, user_id: int, embedding: list[float]):
    """Caller supplies a validated embedding and owns flush/commit/rollback."""
    db_memory = Memory(**memory.model_dump(), user_id=user_id)
    db.add(db_memory)
    db.flush()
    create_memory_embedding(db=db, memory_id=db_memory.id, model_name=MODEL_NAME,
                            embedding=embedding, commit=False)
    return db_memory


def create_memory(
    db: Session,
    memory: MemoryCreate,
    user_id: int
):
    try:
        embedding = validated_embedding(f"{memory.title}\n\n{memory.content}")
        db_memory = stage_memory(db, memory, user_id, embedding)
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(db_memory)
    return db_memory


def get_memory_by_id(
    db: Session,
    memory_id: int
):
    return (
        db.query(Memory)
        .filter(Memory.id == memory_id)
        .first()
    )


def get_user_memories(
    db: Session,
    user_id: int
):
    return (
        db.query(Memory)
        .filter(Memory.user_id == user_id)
        .all()
    )


def update_memory(
    db: Session,
    db_memory: Memory,
    memory_update: MemoryUpdate
):
    update_data = memory_update.model_dump(exclude_unset=True)
    try:
        text_changed = any(
            field in update_data and update_data[field] != getattr(db_memory, field)
            for field in ("title", "content")
        )
        if text_changed:
            title = update_data.get("title", db_memory.title)
            content = update_data.get("content", db_memory.content)
            embedding = validated_embedding(f"{title}\n\n{content}")
        for field, value in update_data.items():
            setattr(db_memory, field, value)
        if text_changed:
            update_memory_embedding(
                db=db, memory_id=db_memory.id, embedding=embedding,
                model_name=MODEL_NAME, commit=False,
            )
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(db_memory)
    return db_memory


def delete_memory(
    db: Session,
    db_memory: Memory
):
    db.delete(db_memory)
    db.commit()