"""
Product & Variant Management API Endpoints (Module 3).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_user,
    get_staff_or_admin_user,
)
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
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Product & Variant Management"])


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Product with Variants (Admin/Staff)",
)
def create_product(
    req: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Create a new product in the catalog with optional variants.
    Restricted to ADMIN and STAFF roles.
    """
    return ProductService.create_product(db, req, current_user)


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List Products with Search & Filters",
)
def list_products(
    query: Optional[str] = Query(None, description="Search by name, code, or description"),
    product_type: Optional[str] = Query("ALL", description="Filter: ALL, SERVICE, SOFTWARE, HARDWARE, CONSUMABLE"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List catalog products with dynamic variant pricing.
    Accessible to all authenticated users.
    """
    return ProductService.get_products(
        db=db,
        query=query,
        product_type=product_type,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get Product Details with Variants",
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve product details, pricing, and all variants.
    """
    return ProductService.get_product_by_id(db, product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update Product (Admin/Staff)",
)
def update_product(
    product_id: int,
    req: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Update product fields and pricing.
    """
    return ProductService.update_product(db, product_id, req, current_user)


@router.post(
    "/{product_id}/variants",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Variant to Product (Admin/Staff)",
)
def add_variant(
    product_id: int,
    req: VariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Add a new pricing tier or variant to an existing product.
    """
    return ProductService.add_variant(db, product_id, req, current_user)


@router.put(
    "/{product_id}/variants/{variant_id}",
    response_model=VariantResponse,
    summary="Update Product Variant (Admin/Staff)",
)
def update_variant(
    product_id: int,
    variant_id: int,
    req: VariantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Update variant name, SKU, or additional price.
    """
    return ProductService.update_variant(db, product_id, variant_id, req, current_user)


@router.delete(
    "/{product_id}",
    summary="Safe Delete or Archive Product (Admin/Staff)",
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Safely delete or archive a product.
    If referenced in active quotations or subscriptions, archives instead of deleting.
    """
    return ProductService.delete_or_archive_product(db, product_id, current_user)
