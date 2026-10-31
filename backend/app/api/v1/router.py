"""
API v1 Main Router for Brightloop Nexus (Members 1 & 2).
Aggregates all module endpoints under the /api/v1 prefix.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    customers,
    products,
    plans,
    quotations,
    subscriptions,
    renewals,
    churn,
    timemachine,
    portal,
    taxes,
    discounts,
    invoices,
    payments,
    reconciliation,
    revenue_guardian,
    revenue_simulator,
    ai_assistant,
    analytics,
    billing_recovery,
)

api_router = APIRouter()

# Core diagnostic and health check endpoint
api_router.include_router(health.router, tags=["Health & Diagnostics"])

# Core Subscription & Operations Endpoints
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(plans.router)
api_router.include_router(quotations.router)
api_router.include_router(subscriptions.router)
api_router.include_router(renewals.router)
api_router.include_router(churn.router)
api_router.include_router(timemachine.router)
api_router.include_router(portal.router)

# Financial Intelligence Endpoints
api_router.include_router(taxes.router, prefix="/taxes", tags=["Tax Management"])
api_router.include_router(discounts.router, prefix="/discounts", tags=["Discount Management"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoice Management"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payment Management"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["Payment Reconciliation"])
api_router.include_router(revenue_guardian.router, prefix="/revenue-guardian", tags=["Revenue Guardian"])
api_router.include_router(revenue_simulator.router, prefix="/revenue-simulator", tags=["Future Revenue Simulator"])
api_router.include_router(ai_assistant.router, prefix="/ai-assistant", tags=["Ask Brightloop AI"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Revenue Command Center"])
api_router.include_router(billing_recovery.router, prefix="/billing-recovery", tags=["Self-Healing Billing"])
