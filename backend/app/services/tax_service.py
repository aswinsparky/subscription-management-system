"""
Tax Domain Service for Brightloop Nexus (Member 2).
Handles tax configuration, effective date matching, and accurate precision calculations.
"""
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.tax import Tax
from app.schemas.tax import TaxCreate, TaxUpdate, TaxCalculationResponse, TaxCalculationItemResult


class TaxService:
    @staticmethod
    def get_taxes(db: Session, active_only: bool = False) -> List[Tax]:
        stmt = select(Tax)
        if active_only:
            stmt = stmt.where(Tax.is_active == True)
        stmt = stmt.order_by(Tax.name)
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_tax_by_id(db: Session, tax_id: int) -> Tax:
        tax = db.scalar(select(Tax).where(Tax.id == tax_id))
        if not tax:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tax with ID {tax_id} not found.",
            )
        return tax

    @staticmethod
    def create_tax(db: Session, data: TaxCreate) -> Tax:
        tax = Tax(
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            tax_type=data.tax_type.upper(),
            rate=data.rate,
            applicability=data.applicability.upper(),
            effective_from=data.effective_from,
            effective_until=data.effective_until,
            is_active=data.is_active,
        )
        db.add(tax)
        db.commit()
        db.refresh(tax)
        return tax

    @staticmethod
    def update_tax(db: Session, tax_id: int, data: TaxUpdate) -> Tax:
        tax = TaxService.get_tax_by_id(db, tax_id)
        if data.name is not None:
            tax.name = data.name.strip()
        if data.description is not None:
            tax.description = data.description.strip() if data.description else None
        if data.tax_type is not None:
            tax.tax_type = data.tax_type.upper()
        if data.rate is not None:
            tax.rate = data.rate
        if data.applicability is not None:
            tax.applicability = data.applicability.upper()
        if data.effective_from is not None:
            tax.effective_from = data.effective_from
        if data.effective_until is not None:
            tax.effective_until = data.effective_until
        if data.is_active is not None:
            tax.is_active = data.is_active

        db.commit()
        db.refresh(tax)
        return tax

    @staticmethod
    def calculate_taxes(db: Session, base_amount: Decimal, tax_ids: List[int]) -> TaxCalculationResponse:
        """Calculate taxes accurately and return itemized breakdown."""
        breakdown: List[TaxCalculationItemResult] = []
        total_tax = Decimal("0.00")

        if not tax_ids:
            return TaxCalculationResponse(
                base_amount=base_amount,
                total_tax_amount=Decimal("0.00"),
                breakdown=[],
            )

        stmt = select(Tax).where(Tax.id.in_(tax_ids), Tax.is_active == True)
        active_taxes = db.scalars(stmt).all()

        for tax in active_taxes:
            if tax.is_currently_effective():
                tax_amt = tax.calculate_tax(base_amount)
                total_tax += tax_amt
                breakdown.append(
                    TaxCalculationItemResult(
                        tax_id=tax.id,
                        name=tax.name,
                        tax_type=tax.tax_type,
                        rate=tax.rate,
                        calculated_amount=tax_amt,
                    )
                )

        return TaxCalculationResponse(
            base_amount=base_amount,
            total_tax_amount=total_tax.quantize(Decimal("0.01")),
            breakdown=breakdown,
        )

