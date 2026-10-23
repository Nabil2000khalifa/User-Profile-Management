from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class AdminResponse(BaseModel):
    id: int
    email: EmailStr


class LoginResponse(BaseModel):
    admin: AdminResponse
    csrf_token: str
