from app.db.database import SessionLocal

from app.models.memory import Memory
from app.models.memory_embedding import MemoryEmbedding

from app.services.embedding_service import (
    generate_embedding
)


def rebuild_embeddings():
    db = SessionLocal()

    try:
        memories = db.query(Memory).all()

        for memory in memories:

            embedding_text = (
                f"{memory.title}\n\n"
                f"{memory.content}"
            )

            new_embedding = generate_embedding(
                embedding_text
            )

            db_embedding = (
                db.query(MemoryEmbedding)
                .filter(
                    MemoryEmbedding.memory_id == memory.id
                )
                .first()
            )

            if db_embedding:
                db_embedding.embedding = new_embedding

        db.commit()

        print(
            f"Updated {len(memories)} embeddings."
        )

    finally:
        db.close()


if __name__ == "__main__":
    rebuild_embeddings()