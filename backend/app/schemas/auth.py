"""
Pydantic v2 Validation Schemas for Authentication and RBAC.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict
from app.core.security import validate_password_complexity


class CustomerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Customer full name")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., description="Complex password")
    confirm_password: str = Field(..., description="Password confirmation")
    phone: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=255)
    billing_address: Optional[str] = Field("123 Enterprise Blvd, Suite 100", description="Initial billing address")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        valid, msg = validate_password_complexity(v)
        if not valid:
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "CustomerRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Password and confirmation password do not match.")
        return self


class StaffCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr = Field(...)
    password: str = Field(...)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        valid, msg = validate_password_complexity(v)
        if not valid:
            raise ValueError(msg)
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User registered email")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address associated with account")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Single-use reset token")
    new_password: str = Field(..., description="New complex password")
    confirm_password: str = Field(...)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        valid, msg = validate_password_complexity(v)
        if not valid:
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "PasswordResetConfirm":
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match.")
        return self


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
