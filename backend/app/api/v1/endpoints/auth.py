"""
Authentication & Authorization API Endpoints.
Covers Customer Registration, Login, Current User, Admin Staff Creation, and Password Reset.
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import (
    get_current_user,
    get_admin_user,
    RoleChecker,
)
from app.models.user import User
from app.schemas.auth import (
    CustomerRegisterRequest,
    StaffCreateRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Customer Account",
)
def register_customer(req: CustomerRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new customer account.
    - Validates email uniqueness and password complexity.
    - Automatically creates linked Customer profile.
    - Issues JWT access token upon successful registration.
    """
    return AuthService.register_customer(db, req)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password.
    Returns a signed JWT access token and user role.
    """
    return AuthService.login(db, req)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Fetch the currently authenticated user's profile and active role.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.name if current_user.role else "CUSTOMER",
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post(
    "/create-staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Staff Account (Admin Only)",
)
def create_staff(
    req: StaffCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    Administrative endpoint to provision a new Staff member.
    Enforces RBAC: Only users with the ADMIN role can execute this action.
    """
    return AuthService.create_staff(db, req)


@router.post(
    "/password-reset/request",
    summary="Request Password Reset Token",
)
def request_password_reset(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Generate a single-use, time-limited (1 hour) reset token.
    Invalidates any previous unused tokens.
    """
    return AuthService.request_password_reset(db, req)


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    summary="Confirm Password Reset",
)
def confirm_password_reset(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Validate single-use reset token and update user password.
    Rejects expired or previously consumed tokens.
    """
    result = AuthService.confirm_password_reset(db, req)
    return MessageResponse(message=result["message"])


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List All Users (Admin Only)",
)
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """
    List all users in the system and their assigned roles.
    """
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.name if u.role else "CUSTOMER",
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]
