from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema para login"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema de respuesta de tokens"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema para refresh token"""

    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Schema de respuesta de access token"""

    access_token: str
    token_type: str = "bearer"
