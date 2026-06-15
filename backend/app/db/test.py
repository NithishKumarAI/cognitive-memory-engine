from app.services.embedding_service import generate_embedding

embedding = generate_embedding(
    "I studied machine learning today"
)

print(len(embedding))