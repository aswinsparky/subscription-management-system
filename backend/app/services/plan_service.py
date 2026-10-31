"""
Subscription Plan Domain Service (Module 4).
Handles Plan CRUD, Availability Period Validation, and Lifecycle Policy Enforcement.
"""
from datetime import datetime, timezone
import math
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from fastapi import HTTPException, status
from app.models.plan import Plan
from app.models.quotation import Quotation
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.plan import (
    PlanCreate,
    PlanUpdate,
    PlanResponse,
    PlanListResponse,
)


class PlanService:
    @staticmethod
    def _generate_plan_code(db: Session, interval: str) -> str:
        """Generate plan code: PLAN-{INTERVAL_PREFIX}-XXXX."""
        prefix = interval[:3].upper()
        count = db.scalar(select(func.count(Plan.id))) or 0
        return f"PLAN-{prefix}-{(count + 1):04d}"

    @staticmethod
    def create_plan(db: Session, req: PlanCreate, current_user: User) -> PlanResponse:
        """Create a new subscription plan."""
        code = req.plan_code.strip() if req.plan_code else PlanService._generate_plan_code(db, req.billing_interval)
        existing = db.scalar(select(Plan).where(Plan.plan_code == code))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Plan with code '{code}' already exists.",
            )

        plan = Plan(
            plan_code=code,
            name=req.name.strip(),
            description=req.description.strip() if req.description else None,
            billing_interval=req.billing_interval.upper(),
            plan_price=req.plan_price,
            minimum_quantity=req.minimum_quantity,
            available_from=req.available_from,
            available_until=req.available_until,
            auto_close_enabled=req.auto_close_enabled,
            early_cancellation_allowed=req.early_cancellation_allowed,
            pause_allowed=req.pause_allowed,
            renewal_allowed=req.renewal_allowed,
            status=req.status.upper(),
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return PlanResponse.model_validate(plan)

    @staticmethod
    def get_plans(
        db: Session,
        query: Optional[str] = None,
        billing_interval: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PlanListResponse:
        """List plans with search, interval filter, status filter, and pagination."""
        stmt = select(Plan)

        if query and query.strip():
            search = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Plan.name.ilike(search),
                    Plan.plan_code.ilike(search),
                    Plan.description.ilike(search),
                )
            )

        if billing_interval and billing_interval.upper() != "ALL":
            stmt = stmt.where(Plan.billing_interval == billing_interval.upper())

        if status_filter and status_filter.upper() != "ALL":
            stmt = stmt.where(Plan.status == status_filter.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.order_by(Plan.created_at.desc()).offset(offset).limit(page_size)
        items = db.scalars(stmt).all()

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return PlanListResponse(
            items=[PlanResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_plan_by_id(db: Session, plan_id: int) -> PlanResponse:
        """Fetch plan by ID."""
        plan = db.scalar(select(Plan).where(Plan.id == plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription Plan #{plan_id} not found.",
            )
        return PlanResponse.model_validate(plan)

    @staticmethod
    def update_plan(
        db: Session, plan_id: int, req: PlanUpdate, current_user: User
    ) -> PlanResponse:
        """Update subscription plan settings and lifecycle permissions."""
        plan = db.scalar(select(Plan).where(Plan.id == plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription Plan #{plan_id} not found.",
            )

        if req.name is not None:
            plan.name = req.name.strip()
        if req.description is not None:
            plan.description = req.description.strip()
        if req.billing_interval is not None:
            plan.billing_interval = req.billing_interval.upper()
        if req.plan_price is not None:
            plan.plan_price = req.plan_price
        if req.minimum_quantity is not None:
            plan.minimum_quantity = req.minimum_quantity
        if req.available_from is not None:
            plan.available_from = req.available_from
        if req.available_until is not None:
            plan.available_until = req.available_until
        if req.auto_close_enabled is not None:
            plan.auto_close_enabled = req.auto_close_enabled
        if req.early_cancellation_allowed is not None:
            plan.early_cancellation_allowed = req.early_cancellation_allowed
        if req.pause_allowed is not None:
            plan.pause_allowed = req.pause_allowed
        if req.renewal_allowed is not None:
            plan.renewal_allowed = req.renewal_allowed
        if req.status is not None:
            plan.status = req.status.upper()

        # Validate date consistency if updated
        if plan.available_from and plan.available_until:
            if plan.available_until < plan.available_from:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="available_until date must be greater than or equal to available_from date.",
                )

        plan.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(plan)
        return PlanResponse.model_validate(plan)

    @staticmethod
    def archive_or_delete_plan(db: Session, plan_id: int, current_user: User) -> dict:
        """
        Safely deletes or archives a plan.
        If referenced in existing quotations or subscriptions, archives the plan rather than hard deleting.
        """
        plan = db.scalar(select(Plan).where(Plan.id == plan_id))
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription Plan #{plan_id} not found.",
            )

        quote_refs = db.scalar(
            select(func.count(Quotation.id)).where(Quotation.plan_id == plan_id)
        ) or 0
        sub_refs = db.scalar(
            select(func.count(Subscription.id)).where(Subscription.plan_id == plan_id)
        ) or 0

        if quote_refs > 0 or sub_refs > 0:
            plan.status = "ARCHIVED"
            db.commit()
            return {
                "message": (
                    f"Plan #{plan_id} ('{plan.name}') is actively referenced in {quote_refs} quotations and "
                    f"{sub_refs} subscriptions, and was safely archived rather than deleted."
                ),
                "action": "archived",
                "plan_id": plan_id,
                "status": "ARCHIVED",
            }

        db.delete(plan)
        db.commit()
        return {
            "message": f"Plan #{plan_id} ('{plan.name}') had no dependencies and was permanently deleted.",
            "action": "deleted",
            "plan_id": plan_id,
        }

    @staticmethod
    def is_plan_available(plan: Plan, requested_date: Optional[datetime] = None) -> bool:
        """Check if plan is currently active and within its availability window."""
        if plan.status != "ACTIVE":
            return False
        now = requested_date or datetime.now(timezone.utc)
        if plan.available_from and now < plan.available_from:
            return False
        if plan.available_until and now > plan.available_until:
            return False
        return True
