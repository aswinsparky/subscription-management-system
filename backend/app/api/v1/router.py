"""
API v1 Main Router.
Aggregates all module endpoints under the /api/v1 prefix.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, customers, products

api_router = APIRouter()

# Core diagnostic and health check endpoint
api_router.include_router(health.router, tags=["Health & Diagnostics"])

# Module 1: Authentication & RBAC endpoints
api_router.include_router(auth.router)

# Module 2: Customer Management endpoints
api_router.include_router(customers.router)

# Module 3: Product & Variant Management endpoints
api_router.include_router(products.router)
