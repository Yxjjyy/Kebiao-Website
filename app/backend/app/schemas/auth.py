from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str = ""
    password: str = ""


class LoginResponse(BaseModel):
    token: str


class SessionOut(BaseModel):
    expires_at: str
