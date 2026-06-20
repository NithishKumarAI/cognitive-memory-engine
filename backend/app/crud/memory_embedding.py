from sqlalchemy.orm import Session
from app.models.memory_embedding import MemoryEmbedding

from app.models.memory_embedding import MemoryEmbedding


def create_memory_embedding(
    db: Session,
    memory_id: int,
    model_name: str,
    embedding: list[float]
):
    memory_embedding = MemoryEmbedding(
        memory_id=memory_id,
        model_name=model_name,
        embedding=embedding
    )

    db.add(memory_embedding)
    db.commit()
    db.refresh(memory_embedding)

    return memory_embedding

def update_memory_embedding(
        db: Session,
        memory_id: int,
        embedding: list[float],
        model_name: str
):
    memory_embedding = (
        db.query(MemoryEmbedding)
        .filter(
            MemoryEmbedding.memory_id == memory_id
        )
        .first()
    )

    if not memory_embedding:
        return create_memory_embedding(
            db=db,
            memory_id=memory_id,
            model_name=model_name,
            embedding=embedding
        )

    memory_embedding.embedding = embedding
    memory_embedding.model_name = model_name

    db.commit()
    db.refresh(memory_embedding)

    return memory_embedding