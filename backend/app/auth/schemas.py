from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserMeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    email: str
    org_id: str
    org_name: str
    roles: list[str]
    permissions: list[str]
    status: str
