"""
Product and Variant Domain Service (Module 3).
Handles Catalog Management, Variant Dynamic Pricing, Search, Filter, and Safe Deletion.
"""
import math
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_, func
from fastapi import HTTPException, status
from app.models.product import Product, ProductVariant
from app.models.quotation import QuotationItem
from app.models.subscription import SubscriptionItem
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    VariantCreate,
    VariantUpdate,
    VariantResponse,
)


class ProductService:
    @staticmethod
    def _generate_product_code(db: Session) -> str:
        """Generate sequential product code: PROD-XXXX."""
        count = db.scalar(select(func.count(Product.id))) or 0
        return f"PROD-{(count + 1):04d}"

    @staticmethod
    def _to_product_response(product: Product) -> ProductResponse:
        """Converts Product ORM model to ProductResponse with computed variant final prices."""
        base_price = product.sales_price
        variant_responses = [
            VariantResponse(
                id=v.id,
                product_id=v.product_id,
                variant_name=v.variant_name,
                sku=v.sku,
                additional_price=v.additional_price,
                is_active=v.is_active,
                created_at=v.created_at,
                final_price=base_price + v.additional_price,
            )
            for v in product.variants
        ]

        return ProductResponse(
            id=product.id,
            product_code=product.product_code,
            name=product.name,
            product_type=product.product_type,
            description=product.description,
            sales_price=product.sales_price,
            cost_price=product.cost_price,
            internal_notes=product.internal_notes,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            variants=variant_responses,
        )

    @staticmethod
    def create_product(db: Session, req: ProductCreate, current_user: User) -> ProductResponse:
        """Create a new product with optional initial variants."""
        code = req.product_code.strip() if req.product_code else ProductService._generate_product_code(db)
        existing = db.scalar(select(Product).where(Product.product_code == code))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with code '{code}' already exists.",
            )

        product = Product(
            product_code=code,
            name=req.name.strip(),
            product_type=req.product_type.upper(),
            description=req.description.strip() if req.description else None,
            sales_price=req.sales_price,
            cost_price=req.cost_price,
            internal_notes=req.internal_notes.strip() if req.internal_notes else None,
            is_active=req.is_active,
        )
        db.add(product)
        db.flush()

        # Add initial variants if provided
        if req.variants:
            for v in req.variants:
                if v.sku:
                    existing_sku = db.scalar(select(ProductVariant).where(ProductVariant.sku == v.sku.strip()))
                    if existing_sku:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Variant with SKU '{v.sku}' already exists.",
                        )
                variant = ProductVariant(
                    product_id=product.id,
                    variant_name=v.variant_name.strip(),
                    sku=v.sku.strip() if v.sku else None,
                    additional_price=v.additional_price,
                    is_active=v.is_active,
                )
                db.add(variant)

        db.commit()
        db.refresh(product)
        return ProductService._to_product_response(product)

    @staticmethod
    def get_products(
        db: Session,
        query: Optional[str] = None,
        product_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ProductListResponse:
        """List products with search, type filter, status filter, and pagination."""
        stmt = select(Product).options(selectinload(Product.variants))

        if query and query.strip():
            search = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Product.name.ilike(search),
                    Product.product_code.ilike(search),
                    Product.description.ilike(search),
                )
            )

        if product_type and product_type.upper() != "ALL":
            stmt = stmt.where(Product.product_type == product_type.upper())

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(page_size)
        items = db.scalars(stmt).all()

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return ProductListResponse(
            items=[ProductService._to_product_response(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> ProductResponse:
        """Fetch product by ID with its variants and computed prices."""
        product = db.scalar(
            select(Product).options(selectinload(Product.variants)).where(Product.id == product_id)
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product #{product_id} not found.",
            )
        return ProductService._to_product_response(product)

    @staticmethod
    def update_product(
        db: Session, product_id: int, req: ProductUpdate, current_user: User
    ) -> ProductResponse:
        """Update existing product."""
        product = db.scalar(
            select(Product).options(selectinload(Product.variants)).where(Product.id == product_id)
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product #{product_id} not found.",
            )

        if req.name is not None:
            product.name = req.name.strip()
        if req.product_type is not None:
            product.product_type = req.product_type.upper()
        if req.description is not None:
            product.description = req.description.strip()
        if req.sales_price is not None:
            product.sales_price = req.sales_price
        if req.cost_price is not None:
            product.cost_price = req.cost_price
        if req.internal_notes is not None:
            product.internal_notes = req.internal_notes.strip()
        if req.is_active is not None:
            product.is_active = req.is_active

        db.commit()
        db.refresh(product)
        return ProductService._to_product_response(product)

    @staticmethod
    def add_variant(
        db: Session, product_id: int, req: VariantCreate, current_user: User
    ) -> VariantResponse:
        """Add a new variant to an existing product."""
        product = db.scalar(select(Product).where(Product.id == product_id))
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product #{product_id} not found.",
            )

        if req.sku:
            existing_sku = db.scalar(select(ProductVariant).where(ProductVariant.sku == req.sku.strip()))
            if existing_sku:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Variant with SKU '{req.sku}' already exists.",
                )

        variant = ProductVariant(
            product_id=product.id,
            variant_name=req.variant_name.strip(),
            sku=req.sku.strip() if req.sku else None,
            additional_price=req.additional_price,
            is_active=req.is_active,
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)

        return VariantResponse(
            id=variant.id,
            product_id=variant.product_id,
            variant_name=variant.variant_name,
            sku=variant.sku,
            additional_price=variant.additional_price,
            is_active=variant.is_active,
            created_at=variant.created_at,
            final_price=product.sales_price + variant.additional_price,
        )

    @staticmethod
    def update_variant(
        db: Session, product_id: int, variant_id: int, req: VariantUpdate, current_user: User
    ) -> VariantResponse:
        """Update existing product variant."""
        variant = db.scalar(
            select(ProductVariant).where(
                ProductVariant.id == variant_id, ProductVariant.product_id == product_id
            )
        )
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant #{variant_id} for Product #{product_id} not found.",
            )

        product = db.scalar(select(Product).where(Product.id == product_id))

        if req.variant_name is not None:
            variant.variant_name = req.variant_name.strip()
        if req.sku is not None:
            new_sku = req.sku.strip() if req.sku else None
            if new_sku and new_sku != variant.sku:
                existing_sku = db.scalar(
                    select(ProductVariant).where(
                        ProductVariant.sku == new_sku, ProductVariant.id != variant_id
                    )
                )
                if existing_sku:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"SKU '{new_sku}' is already in use.",
                    )
            variant.sku = new_sku
        if req.additional_price is not None:
            variant.additional_price = req.additional_price
        if req.is_active is not None:
            variant.is_active = req.is_active

        db.commit()
        db.refresh(variant)

        return VariantResponse(
            id=variant.id,
            product_id=variant.product_id,
            variant_name=variant.variant_name,
            sku=variant.sku,
            additional_price=variant.additional_price,
            is_active=variant.is_active,
            created_at=variant.created_at,
            final_price=product.sales_price + variant.additional_price,
        )

    @staticmethod
    def delete_or_archive_product(db: Session, product_id: int, current_user: User) -> dict:
        """
        Safely deletes or archives a product.
        If product is referenced in Quotations or Subscriptions, prevents hard delete and archives it.
        """
        product = db.scalar(select(Product).where(Product.id == product_id))
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product #{product_id} not found.",
            )

        # Check references in quotation_items and subscription_items
        quote_refs = db.scalar(
            select(func.count(QuotationItem.id)).where(QuotationItem.product_id == product_id)
        ) or 0
        sub_refs = db.scalar(
            select(func.count(SubscriptionItem.id)).where(SubscriptionItem.product_id == product_id)
        ) or 0

        if quote_refs > 0 or sub_refs > 0:
            # Safely archive
            product.is_active = False
            db.commit()
            return {
                "message": (
                    f"Product #{product_id} ('{product.name}') is referenced in active quotations/subscriptions "
                    f"({quote_refs} quotes, {sub_refs} subscriptions) and was safely archived rather than deleted."
                ),
                "action": "archived",
                "product_id": product_id,
                "is_active": False,
            }

        # Safe to hard delete if unreferenced
        db.delete(product)
        db.commit()
        return {
            "message": f"Product #{product_id} ('{product.name}') has no external references and was permanently deleted.",
            "action": "deleted",
            "product_id": product_id,
        }

