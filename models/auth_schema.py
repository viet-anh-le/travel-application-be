from pydantic import BaseModel, EmailStr, Field


class GoogleLoginRequest(BaseModel):
    token: str


class SignUpRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResendOtpRequest(BaseModel):
    user_id: str


class VerifyOtpRequest(BaseModel):
    user_id: str
    otp: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
