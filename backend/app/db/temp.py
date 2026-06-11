from app.core.auth import (
    create_access_token,
    verify_access_token
)

token = create_access_token(
    {
        "sub": "nithish@example.com"
    }
)

email = verify_access_token(token)

print(email)