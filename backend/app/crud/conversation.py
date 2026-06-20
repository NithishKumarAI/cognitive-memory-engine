from sqlalchemy.orm import Session

from app.models.conversation import Conversation


def create_conversation(
    db: Session,
    user_id: int,
    message: str,
    response: str
):

    conversation = Conversation(
        user_id=user_id,
        message=message,
        response=response
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation