from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.memory_embedding import MemoryEmbedding


def search_memories_by_embedding(
    db: Session,
    user_id: int,
    query_embedding: list[float],
    limit: int = 5
):
    distance = MemoryEmbedding.embedding.cosine_distance(
        query_embedding
    )

    results = (
        db.query(
            Memory,
            distance.label("distance")
        )
        .join(
            MemoryEmbedding,
            Memory.id == MemoryEmbedding.memory_id
        )
        .filter(
            Memory.user_id == user_id
        )
        .order_by(distance)
        .limit(limit)
        .all()
    )

    return results