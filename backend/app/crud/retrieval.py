from sqlalchemy.orm import Session
from sqlalchemy import func
from types import SimpleNamespace

from app.models.memory import Memory
from app.models.memory_embedding import MemoryEmbedding


def search_memories_by_embedding(
    db: Session,
    user_id: int,
    query_embedding: list[float],
    limit: int = 5,
    body_limit: int | None = None
):
    distance = MemoryEmbedding.embedding.cosine_distance(
        query_embedding
    )

    projection = (Memory, distance.label("distance")) if body_limit is None else (
        Memory.id, func.substr(Memory.title, 1, 200).label("title"),
        func.substr(Memory.category, 1, 80).label("category"),
        func.substr(Memory.content, 1, body_limit).label("content"), distance.label("distance"))
    results = (db.query(*projection).join(MemoryEmbedding, Memory.id == MemoryEmbedding.memory_id)
        .filter(Memory.user_id == user_id).order_by(distance, Memory.id).limit(limit).all())
    if body_limit is not None:
        return [(SimpleNamespace(id=row.id, title=row.title, category=row.category, content=row.content), row.distance)
                for row in results]
    return results
