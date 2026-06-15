from sqlalchemy.orm import Session

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