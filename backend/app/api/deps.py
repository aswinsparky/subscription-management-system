"""
FastAPI Dependencies for Authentication, Current User Extraction, and Role-Based Access Control (RBAC).
"""
from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Extract and validate the currently authenticated user from JWT token.
    Raises 401 Unauthorized if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )
    return user


class RoleChecker:
    """
    Reusable dependency class to enforce Role-Based Access Control (RBAC).
    Usage: Depends(RoleChecker(["ADMIN", "STAFF"]))
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {', '.join(self.allowed_roles)}. Your role: {user_role}",
            )
        return current_user


# Convenience dependencies
get_admin_user = RoleChecker(["ADMIN"])
get_staff_or_admin_user = RoleChecker(["ADMIN", "STAFF"])
get_any_authenticated_user = get_current_user

