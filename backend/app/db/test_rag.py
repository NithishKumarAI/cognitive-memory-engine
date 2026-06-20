from app.db.database import SessionLocal
from app.services.rag_service import rag_service


db = SessionLocal()

result = rag_service.generate_answer(
    db=db,
    user_id=4,
    question="What have I studied?"
)

print("\nANSWER\n")
print(result["answer"])

print("\nSOURCES\n")

for source in result["sources"]:
    print(source)