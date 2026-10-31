"""
Customer Domain Service.
Handles CRUD, Search, Filter, Pagination, Ownership Checks, and Historical Associations.
"""
from datetime import datetime, timezone
import math
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from fastapi import HTTPException, status
from app.models.customer import Customer
from app.models.user import User
from app.models.quotation import Quotation
from app.models.subscription import Subscription
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerHistoryResponse,
    SubscriptionSummary,
    QuotationSummary,
)


class CustomerService:
    @staticmethod
    def _generate_customer_code(db: Session) -> str:
        """Generate next sequence customer code: CUST-YYYY-XXXX."""
        year = datetime.now(timezone.utc).year
        count = db.scalar(select(func.count(Customer.id))) or 0
        return f"CUST-{year}-{(count + 1):04d}"

    @staticmethod
    def create_customer(db: Session, req: CustomerCreate, current_user: User) -> CustomerResponse:
        """Create a new customer profile (Admin/Staff action)."""
        existing = db.scalar(select(Customer).where(Customer.email == req.email.lower()))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Customer with email '{req.email}' already exists.",
            )

        customer_code = CustomerService._generate_customer_code(db)
        customer = Customer(
            customer_code=customer_code,
            full_name=req.full_name.strip(),
            email=req.email.lower().strip(),
            phone=req.phone.strip() if req.phone else None,
            company_name=req.company_name.strip() if req.company_name else None,
            billing_address=req.billing_address.strip(),
            tax_id=req.tax_id.strip() if req.tax_id else None,
            account_status=req.account_status.upper() if req.account_status else "ACTIVE",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return CustomerResponse.model_validate(customer)

    @staticmethod
    def get_customers(
        db: Session,
        current_user: User,
        query: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> CustomerListResponse:
        """
        List customers with search, status filtering, and pagination.
        Admin and Staff can view all customers.
        """
        stmt = select(Customer)

        # Search filter (name, email, company, code)
        if query and query.strip():
            search = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(search),
                    Customer.email.ilike(search),
                    Customer.company_name.ilike(search),
                    Customer.customer_code.ilike(search),
                )
            )

        # Status filter (ACTIVE, SUSPENDED, ARCHIVED)
        if status_filter and status_filter.strip() and status_filter.upper() != "ALL":
            stmt = stmt.where(Customer.account_status == status_filter.strip().upper())

        # Count total matching records
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Apply ordering and pagination
        offset = (max(page, 1) - 1) * page_size
        stmt = stmt.order_by(Customer.created_at.desc()).offset(offset).limit(page_size)
        items = db.scalars(stmt).all()

        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return CustomerListResponse(
            items=[CustomerResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def get_customer_by_id(db: Session, customer_id: int, current_user: User) -> CustomerResponse:
        """
        Fetch customer details by ID.
        Enforces strict backend tenant ownership:
        - Admin & Staff: can view any customer.
        - Customer: can ONLY view their own customer record (where customer.user_id == current_user.id).
        """
        customer = db.scalar(select(Customer).where(Customer.id == customer_id))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer #{customer_id} not found.",
            )

        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER" and customer.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own customer account.",
            )

        return CustomerResponse.model_validate(customer)

    @staticmethod
    def get_customer_for_current_user(db: Session, current_user: User) -> CustomerResponse:
        """Fetch the linked customer profile for the logged in user."""
        customer = db.scalar(select(Customer).where(Customer.user_id == current_user.id))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No customer profile linked to this user account.",
            )
        return CustomerResponse.model_validate(customer)

    @staticmethod
    def update_customer(
        db: Session, customer_id: int, req: CustomerUpdate, current_user: User
    ) -> CustomerResponse:
        """
        Update an existing customer.
        Enforces ownership check for customers and status validation.
        """
        customer = db.scalar(select(Customer).where(Customer.id == customer_id))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer #{customer_id} not found.",
            )

        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER" and customer.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You cannot modify other customer records.",
            )

        # Update fields if provided
        if req.full_name is not None:
            customer.full_name = req.full_name.strip()
        if req.email is not None:
            # Check unique if changed
            new_email = req.email.lower().strip()
            if new_email != customer.email:
                existing = db.scalar(
                    select(Customer).where(Customer.email == new_email, Customer.id != customer_id)
                )
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Email '{new_email}' is already in use by another customer.",
                    )
                customer.email = new_email
        if req.phone is not None:
            customer.phone = req.phone.strip() if req.phone else None
        if req.company_name is not None:
            customer.company_name = req.company_name.strip() if req.company_name else None
        if req.billing_address is not None:
            customer.billing_address = req.billing_address.strip()
        if req.tax_id is not None:
            customer.tax_id = req.tax_id.strip() if req.tax_id else None
        if req.account_status is not None:
            # Only Admin or Staff can change account status
            if user_role not in ["ADMIN", "STAFF"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only Staff or Administrators can alter account status.",
                )
            customer.account_status = req.account_status.upper()

        customer.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(customer)
        return CustomerResponse.model_validate(customer)

    @staticmethod
    def get_customer_history(
        db: Session, customer_id: int, current_user: User
    ) -> CustomerHistoryResponse:
        """
        Fetch customer record alongside all past subscriptions and quotations.
        Enforces tenant ownership.
        """
        customer = db.scalar(select(Customer).where(Customer.id == customer_id))
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer #{customer_id} not found.",
            )

        user_role = current_user.role.name if current_user.role else "CUSTOMER"
        if user_role == "CUSTOMER" and customer.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You cannot view history for other accounts.",
            )

        # Fetch subscriptions
        subscriptions = db.scalars(
            select(Subscription)
            .where(Subscription.customer_id == customer_id)
            .order_by(Subscription.created_at.desc())
        ).all()

        # Fetch quotations
        quotations = db.scalars(
            select(Quotation)
            .where(Quotation.customer_id == customer_id)
            .order_by(Quotation.created_at.desc())
        ).all()

        sub_summaries = [
            SubscriptionSummary(
                id=s.id,
                subscription_number=s.subscription_number,
                status=s.status,
                billing_interval=s.billing_interval,
                total_amount=str(s.total_amount),
                start_date=s.start_date,
                expiry_date=s.expiry_date,
                next_billing_date=s.next_billing_date,
            )
            for s in subscriptions
        ]

        quote_summaries = [
            QuotationSummary(
                id=q.id,
                quotation_number=q.quotation_number,
                status=q.status,
                total=str(q.total),
                quotation_date=q.quotation_date,
                expiration_date=q.expiration_date,
            )
            for q in quotations
        ]

        return CustomerHistoryResponse(
            customer=CustomerResponse.model_validate(customer),
            subscriptions=sub_summaries,
            quotations=quote_summaries,
        )
