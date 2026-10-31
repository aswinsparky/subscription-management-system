"""
Discount Domain Service for Brightloop Nexus.
Enforces business rules, minimum spend, expiration dates, and per-customer usage tracking.
"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.discount import Discount, DiscountUsage
from app.schemas.discount import DiscountCreate, DiscountUpdate, DiscountValidateResponse


class DiscountService:
    @staticmethod
    def get_discounts(db: Session, active_only: bool = False) -> List[Discount]:
        stmt = select(Discount)
        if active_only:
            stmt = stmt.where(Discount.is_active == True)
        stmt = stmt.order_by(Discount.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_discount_by_id(db: Session, discount_id: int) -> Discount:
        discount = db.scalar(select(Discount).where(Discount.id == discount_id))
        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Discount with ID {discount_id} not found.",
            )
        return discount

    @staticmethod
    def get_discount_by_code(db: Session, coupon_code: str) -> Optional[Discount]:
        return db.scalar(
            select(Discount).where(
                func.upper(Discount.coupon_code) == coupon_code.strip().upper()
            )
        )

    @staticmethod
    def create_discount(db: Session, data: DiscountCreate) -> Discount:
        clean_code = data.coupon_code.strip().upper()
        existing = DiscountService.get_discount_by_code(db, clean_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Coupon code '{clean_code}' already exists.",
            )

        discount = Discount(
            name=data.name.strip(),
            coupon_code=clean_code,
            discount_type=data.discount_type.upper(),
            discount_value=data.discount_value,
            min_purchase_amount=data.min_purchase_amount,
            min_quantity=data.min_quantity,
            max_usage_limit=data.max_usage_limit,
            usage_per_customer_limit=data.usage_per_customer_limit,
            applicable_product_ids=data.applicable_product_ids,
            applicable_plan_ids=data.applicable_plan_ids,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active,
        )
        db.add(discount)
        db.commit()
        db.refresh(discount)
        return discount

    @staticmethod
    def update_discount(db: Session, discount_id: int, data: DiscountUpdate) -> Discount:
        discount = DiscountService.get_discount_by_id(db, discount_id)
        if data.name is not None:
            discount.name = data.name.strip()
        if data.discount_type is not None:
            discount.discount_type = data.discount_type.upper()
        if data.discount_value is not None:
            discount.discount_value = data.discount_value
        if data.min_purchase_amount is not None:
            discount.min_purchase_amount = data.min_purchase_amount
        if data.min_quantity is not None:
            discount.min_quantity = data.min_quantity
        if data.max_usage_limit is not None:
            discount.max_usage_limit = data.max_usage_limit
        if data.usage_per_customer_limit is not None:
            discount.usage_per_customer_limit = data.usage_per_customer_limit
        if data.applicable_product_ids is not None:
            discount.applicable_product_ids = data.applicable_product_ids
        if data.applicable_plan_ids is not None:
            discount.applicable_plan_ids = data.applicable_plan_ids
        if data.start_date is not None:
            discount.start_date = data.start_date
        if data.end_date is not None:
            discount.end_date = data.end_date
        if data.is_active is not None:
            discount.is_active = data.is_active

        db.commit()
        db.refresh(discount)
        return discount

    @staticmethod
    def validate_coupon(
        db: Session,
        coupon_code: str,
        customer_id: int,
        subtotal: Decimal,
        quantity: int = 1,
        product_ids: Optional[List[int]] = None,
        plan_id: Optional[int] = None,
    ) -> DiscountValidateResponse:
        """Validate coupon eligibility against customer, purchase amount, limits, and scope."""
        clean_code = coupon_code.strip().upper()
        discount = DiscountService.get_discount_by_code(db, clean_code)

        if not discount:
            return DiscountValidateResponse(
                is_valid=False,
                coupon_code=clean_code,
                message=f"Coupon code '{clean_code}' is invalid.",
            )

        # Count customer usages
        customer_usage_count = db.scalar(
            select(func.count(DiscountUsage.id)).where(
                DiscountUsage.discount_id == discount.id,
                DiscountUsage.customer_id == customer_id,
            )
        ) or 0

        is_valid, reason = discount.is_eligible(
            subtotal=subtotal,
            quantity=quantity,
            customer_usage_count=customer_usage_count,
            product_ids=product_ids,
            plan_id=plan_id,
        )

        if not is_valid:
            return DiscountValidateResponse(
                is_valid=False,
                coupon_code=clean_code,
                message=reason,
            )

        calc_discount = discount.calculate_discount_amount(subtotal)
        return DiscountValidateResponse(
            is_valid=True,
            coupon_code=clean_code,
            discount_type=discount.discount_type,
            discount_value=discount.discount_value,
            calculated_discount=calc_discount,
            message="Coupon applied successfully.",
        )

    @staticmethod
    def record_usage(
        db: Session,
        discount: Discount,
        customer_id: int,
        invoice_id: int,
        amount_applied: Decimal,
    ) -> DiscountUsage:
        usage = DiscountUsage(
            discount_id=discount.id,
            customer_id=customer_id,
            invoice_id=invoice_id,
            discount_amount_applied=amount_applied,
        )
        db.add(usage)
        discount.current_usage_count += 1
        db.commit()
        return usage

