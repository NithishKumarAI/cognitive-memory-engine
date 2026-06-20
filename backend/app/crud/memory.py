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


def create_memory(
    db: Session,
    memory: MemoryCreate,
    user_id: int
):
    db_memory = Memory(
        title=memory.title,
        content=memory.content,
        category=memory.category,
        study_log_id=memory.study_log_id,
        user_id=user_id
    )

    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)

    embedding_text = (
        f"{db_memory.title}\n\n"
        f"{db_memory.content}"
    )

    embedding = generate_embedding(
        embedding_text
    )

    create_memory_embedding(
        db=db,
        memory_id=db_memory.id,
        model_name=MODEL_NAME,
        embedding=embedding
    )

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
    update_data = memory_update.model_dump(
        exclude_unset=True
    )

    embedding_needs_update = False

    if (
        "title" in update_data or
        "content" in update_data
    ):
        embedding_needs_update = True

    for field, value in update_data.items():
        setattr(
            db_memory,
            field,
            value
        )

    db.commit()
    db.refresh(db_memory)

    if embedding_needs_update:

        embedding_text = (
            f"{db_memory.title}\n\n"
            f"{db_memory.content}"
        )

        embedding = generate_embedding(
            embedding_text
        )

        update_memory_embedding(
            db=db,
            memory_id=db_memory.id,
            embedding=embedding,
            model_name=MODEL_NAME
        )
        print("Regenerating embedding...")

    return db_memory


def delete_memory(
    db: Session,
    db_memory: Memory
):
    db.delete(db_memory)
    db.commit()