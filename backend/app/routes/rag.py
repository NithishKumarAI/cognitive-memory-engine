from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

from app.core.auth import get_current_user

from app.models.user import User

from app.schemas.rag import (
    RAGRequest,
    RAGResponse
)

from app.services.rag_service import rag_service


router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)


@router.post(
    "/ask",
    response_model=RAGResponse
)
def ask_question(
    request: RAGRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):

    result = rag_service.generate_answer(
        db=db,
        user_id=current_user.id,
        question=request.question,
        top_k=request.top_k
    )

    return result