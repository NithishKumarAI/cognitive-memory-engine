from app.db.database import SessionLocal

from app.crud.conversation import create_conversation


db = SessionLocal()

conversation = create_conversation(
    db=db,
    user_id=4,
    message="Test Question",
    response="Test Response"
)

print(conversation.id)
print(conversation.message)
print(conversation.response)