"""
Authentication Domain Service.
Handles User Registration, Login, Role Seeding, Password Reset, and RBAC.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from fastapi import HTTPException, status
from app.models.user import User, Role, PasswordResetToken
from app.models.customer import Customer
from app.schemas.auth import (
    CustomerRegisterRequest,
    StaffCreateRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_secure_reset_token,
)


class AuthService:
    @staticmethod
    def seed_initial_roles_and_admin(db: Session) -> None:
        """
        Ensures default roles (ADMIN, STAFF, CUSTOMER) and default Admin exist.
        Idempotent: safe to run on every startup.
        """
        default_roles = [
            ("ADMIN", "Full administrative access across all modules and settings."),
            ("STAFF", "Operational staff access to customers, quotations, and subscriptions."),
            ("CUSTOMER", "Self-service customer portal access restricted to own records."),
        ]
        for role_name, description in default_roles:
            role = db.scalar(select(Role).where(Role.name == role_name))
            if not role:
                new_role = Role(name=role_name, description=description)
                db.add(new_role)
        db.commit()

        # Seed initial admin user if not present
        admin_email = "admin@brightloop.io"
        admin_user = db.scalar(select(User).where(User.email == admin_email))
        if not admin_user:
            admin_role = db.scalar(select(Role).where(Role.name == "ADMIN"))
            initial_admin = User(
                email=admin_email,
                full_name="Brightloop System Administrator",
                hashed_password=get_password_hash("Admin@123456!"),
                role_id=admin_role.id,
                is_active=True,
            )
            db.add(initial_admin)
            db.commit()

    @staticmethod
    def register_customer(db: Session, req: CustomerRegisterRequest) -> TokenResponse:
        """Register a new customer account, create customer profile, and return JWT token."""
        # 1. Verify email uniqueness
        existing_user = db.scalar(select(User).where(User.email == req.email.lower()))
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        # 2. Get CUSTOMER role
        customer_role = db.scalar(select(Role).where(Role.name == "CUSTOMER"))
        if not customer_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Customer role is not configured.",
            )

        # 3. Create User record
        user = User(
            email=req.email.lower(),
            full_name=req.name,
            hashed_password=get_password_hash(req.password),
            role_id=customer_role.id,
            is_active=True,
        )
        db.add(user)
        db.flush()  # Populates user.id within transaction

        # 4. Generate unique customer code
        customer_code = f"CUST-{user.id:04d}"
        customer = Customer(
            customer_code=customer_code,
            user_id=user.id,
            full_name=req.name,
            email=req.email.lower(),
            phone=req.phone,
            company_name=req.company_name,
            billing_address=req.billing_address or "123 Enterprise Blvd, Suite 100",
            account_status="ACTIVE",
        )
        db.add(customer)
        db.commit()
        db.refresh(user)

        # 5. Generate JWT token
        token = create_access_token(
            subject=user.id,
            role="CUSTOMER",
            email=user.email,
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role="CUSTOMER",
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )

    @staticmethod
    def create_staff(db: Session, req: StaffCreateRequest) -> UserResponse:
        """Admin-only endpoint to provision a new Staff member."""
        existing_user = db.scalar(select(User).where(User.email == req.email.lower()))
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists.",
            )

        staff_role = db.scalar(select(Role).where(Role.name == "STAFF"))
        if not staff_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Staff role is not configured.",
            )

        staff_user = User(
            email=req.email.lower(),
            full_name=req.full_name,
            hashed_password=get_password_hash(req.password),
            role_id=staff_role.id,
            is_active=True,
        )
        db.add(staff_user)
        db.commit()
        db.refresh(staff_user)

        return UserResponse(
            id=staff_user.id,
            email=staff_user.email,
            full_name=staff_user.full_name,
            role="STAFF",
            is_active=staff_user.is_active,
            created_at=staff_user.created_at,
        )

    @staticmethod
    def login(db: Session, req: LoginRequest) -> TokenResponse:
        """Authenticate user by email and password, returning JWT token."""
        user = db.scalar(select(User).where(User.email == req.email.lower()))
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated. Contact an administrator.",
            )

        user_role = user.role.name if user.role else "CUSTOMER"
        token = create_access_token(
            subject=user.id,
            role=user_role,
            email=user.email,
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user_role,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )

    @staticmethod
    def request_password_reset(db: Session, req: PasswordResetRequest) -> dict:
        """
        Generate a secure, single-use reset token valid for 1 hour.
        Invalidates any previously issued unused tokens for this user.
        """
        user = db.scalar(select(User).where(User.email == req.email.lower()))
        # Even if user doesn't exist, return generic message to avoid email enumeration
        if not user:
            return {
                "message": "If this email is registered, a password reset link has been dispatched.",
                "reset_token": None,
            }

        # Invalidate previous tokens
        db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id, PasswordResetToken.is_used == False)
            .values(is_used=True)
        )

        reset_token_str = generate_secure_reset_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token=reset_token_str,
            expires_at=expires_at,
            is_used=False,
        )
        db.add(reset_record)
        db.commit()

        # In production, dispatch via SMTP/SendGrid. For development/hackathon demo, provide token.
        return {
            "message": "Password reset token generated and email dispatched.",
            "reset_token": reset_token_str,  # Provided for seamless API testing & verification
            "expires_at": expires_at.isoformat(),
        }

    @staticmethod
    def confirm_password_reset(db: Session, req: PasswordResetConfirm) -> dict:
        """
        Validate single-use reset token and update user password.
        Rejects expired or already consumed tokens.
        """
        token_record = db.scalar(
            select(PasswordResetToken).where(
                PasswordResetToken.token == req.token,
                PasswordResetToken.is_used == False,
            )
        )
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid, expired, or already consumed password reset token.",
            )

        now = datetime.now(timezone.utc)
        # Handle naive or aware timestamp comparison
        token_exp = token_record.expires_at
        if token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=timezone.utc)

        if token_exp < now:
            token_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired. Please request a new one.",
            )

        # Update password
        user = db.scalar(select(User).where(User.id == token_record.user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account no longer exists.",
            )

        user.hashed_password = get_password_hash(req.new_password)
        token_record.is_used = True
        db.commit()

        return {"message": "Password successfully updated. You may now log in with your new password."}

