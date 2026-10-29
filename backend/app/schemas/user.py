from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, repr=False)

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        # Keep existing bcrypt hashes; reject new passwords that bcrypt would truncate.
        try:
            size = len(value.encode("utf-8"))
        except UnicodeEncodeError:
            raise ValueError("Password contains invalid characters") from None
        if size > 72 or "\0" in value or not value.strip():
            raise ValueError("Use a non-blank password of 8 or more characters and at most 72 UTF-8 bytes, without null characters")
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    # Do not impose new signup rules on legacy users' existing credentials.
    email: EmailStr
    password: str = Field(repr=False)


class Token(BaseModel):
    access_token: str
    token_type: str
