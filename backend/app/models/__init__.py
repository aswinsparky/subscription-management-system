"""
Unified Models Export for Brightloop Nexus (Members 1 & 2).
Used by SQLAlchemy engine and Alembic metadata auto-detection.
"""
# Member 1 Models
from app.models.user import Role, User, PasswordResetToken
from app.models.customer import Customer
from app.models.product import Product, ProductVariant
from app.models.plan import Plan
from app.models.quotation import (
    QuotationTemplate,
    QuotationTemplateItem,
    Quotation,
    QuotationItem,
)
from app.models.subscription import (
    Subscription,
    SubscriptionItem,
    SubscriptionEvent,
    RenewalBillingRequest,
)
from app.models.churn import ChurnRiskAssessment

# Member 2 Financial & Revenue Intelligence Models
from app.models.tax import Tax
from app.models.discount import Discount, DiscountUsage
from app.models.invoice import (
    Invoice,
    InvoiceItem,
    InvoiceTaxDetail,
    InvoiceDiscountDetail,
    InvoiceGenerationLog,
)
from app.models.payment import Payment
from app.models.reconciliation import PaymentReconciliation
from app.models.revenue_guardian import RevenueGuardianFinding, RevenueGuardianRun
from app.models.recovery import BillingRecoveryAttempt
from app.models.simulator import RevenueSimulationScenario

__all__ = [
    # Member 1
    "Role",
    "User",
    "PasswordResetToken",
    "Customer",
    "Product",
    "ProductVariant",
    "Plan",
    "QuotationTemplate",
    "QuotationTemplateItem",
    "Quotation",
    "QuotationItem",
    "Subscription",
    "SubscriptionItem",
    "SubscriptionEvent",
    "RenewalBillingRequest",
    "ChurnRiskAssessment",
    # Member 2
    "Tax",
    "Discount",
    "DiscountUsage",
    "Invoice",
    "InvoiceItem",
    "InvoiceTaxDetail",
    "InvoiceDiscountDetail",
    "InvoiceGenerationLog",
    "Payment",
    "PaymentReconciliation",
    "RevenueGuardianFinding",
    "RevenueGuardianRun",
    "BillingRecoveryAttempt",
    "RevenueSimulationScenario",
]
