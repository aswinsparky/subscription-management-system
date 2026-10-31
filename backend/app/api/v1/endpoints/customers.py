"""
Customer Management API Endpoints (Module 2).
Provides full CRUD, Search, Filter, Pagination, and Historical Associations.
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
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerHistoryResponse,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customer Management"])


@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Customer (Admin/Staff)",
)
def create_customer(
    req: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Provision a new customer record.
    Restricted to ADMIN and STAFF roles.
    """
    return CustomerService.create_customer(db, req, current_user)


@router.get(
    "/",
    response_model=CustomerListResponse,
    summary="List Customers with Search, Filter & Pagination (Admin/Staff)",
)
def list_customers(
    query: Optional[str] = Query(None, description="Search by name, email, company, or customer code"),
    account_status: Optional[str] = Query("ALL", description="Filter: ALL, ACTIVE, SUSPENDED, ARCHIVED"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    """
    Search, filter, and paginate through customer profiles.
    Restricted to ADMIN and STAFF roles.
    """
    return CustomerService.get_customers(
        db=db,
        current_user=current_user,
        query=query,
        status_filter=account_status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/me",
    response_model=CustomerResponse,
    summary="Get My Customer Profile",
)
def get_my_customer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch the customer profile linked to the currently authenticated user session.
    """
    return CustomerService.get_customer_for_current_user(db, current_user)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get Customer Details",
)
def get_customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch details for a specific customer.
    Enforces backend tenant ownership:
    - Admin/Staff: Can access any customer.
    - Customer: Can only access their own linked record.
    """
    return CustomerService.get_customer_by_id(db, customer_id, current_user)


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update Customer Profile",
)
def update_customer(
    customer_id: int,
    req: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update customer contact information, billing address, or account status.
    Enforces ownership validation.
    """
    return CustomerService.update_customer(db, customer_id, req, current_user)


@router.get(
    "/{customer_id}/history",
    response_model=CustomerHistoryResponse,
    summary="Get Customer Subscription & Quotation History",
)
def get_customer_history(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve customer record alongside chronological subscriptions and quotations.
    """
    return CustomerService.get_customer_history(db, customer_id, current_user)
