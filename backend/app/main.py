"""
Brightloop Nexus — Subscription & Intelligence Engine
Main FastAPI Application Entrypoint
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_connection
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("brightloop.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context: verify database connectivity on startup
    and seed default roles (ADMIN, STAFF, CUSTOMER) and initial admin user.
    """
    logger.info("Initializing Brightloop Nexus Engine...")
    db_check = check_db_connection()
    if db_check.get("status") == "connected":
        logger.info(f"Connected to MySQL successfully. Server version: {db_check.get('version')}")
        from app.core.database import SessionLocal
        from app.services.auth_service import AuthService
        db = SessionLocal()
        try:
            AuthService.seed_initial_roles_and_admin(db)
            logger.info("Default roles and initial admin user verified successfully.")
        except Exception as e:
            logger.error(f"Failed to seed initial roles: {e}")
        finally:
            db.close()
    else:
        logger.error(f"Failed to connect to MySQL: {db_check.get('error')}")
    yield
    logger.info("Shutting down Brightloop Nexus Engine...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Brightloop Nexus — Enterprise Subscription & Intelligence Engine (Member 1). "
        "Provides Customer Management, Product & Variant Management, Plans, Quotations, "
        "Subscription Lifecycle, Automated Renewal Scheduling, Churn Radar, and Subscription Time Machine."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS middleware configuration
origins = settings.CORS_ORIGINS
if isinstance(origins, list):
    origins_list = origins
else:
    origins_list = [str(origins)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }

