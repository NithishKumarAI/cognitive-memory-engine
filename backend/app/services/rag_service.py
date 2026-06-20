from sqlalchemy.orm import Session

from app.crud.retrieval import search_memories_by_embedding
from app.services.embedding_service import generate_embedding
from app.services.context_service import context_service
from app.services.llm_service import llm_service
from app.crud.conversation import create_conversation

class RAGService:

    def generate_answer(
        self,
        db: Session,
        user_id: int,
        question: str,
        top_k: int = 5
    ):

        query_embedding = generate_embedding(
            question
        )

        retrieval_results = (
            search_memories_by_embedding(
                db=db,
                user_id=user_id,
                query_embedding=query_embedding,
                limit=top_k
            )
        )

        memories = [
            memory
            for memory, _distance
            in retrieval_results
        ]

        context = (
            context_service.build_memory_context(
                memories
            )
        )

        prompt = f"""
You are a personal cognitive memory assistant.

Answer the user's question using ONLY the provided memories.

When you use information from a memory,
cite it using the format:

[Memory X]

where X is the memory number shown below.

If the memories do not contain enough information,
say that the information is not available in memory.

MEMORIES:

{context}

USER QUESTION:

{question}
"""

        answer = (
            llm_service.generate_response(
                prompt
            )
        )
        create_conversation(
            db=db,
            user_id=user_id,
            message=question,
            response=answer
        )
        sources = []

        for memory, distance in retrieval_results:
            sources.append(
                {
                    "memory_id": memory.id,
                    "title": memory.title,
                    "category": memory.category,
                    "distance": float(distance)
                }
            )

        return {
            "answer": answer,
            "sources": sources
        }

rag_service = RAGService()