from app.schemas.user import UserCreate

user = UserCreate(
    username="nithish",
    email="test@example.com",
    password="secret123"
)

print(user)