"""
Health Check and Diagnostics Endpoint.
Verifies backend status and active database connectivity.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, check_db_connection
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="System Health & Database Diagnostic")
def health_check(db: Session = Depends(get_db)):
    """
    Check API service availability and live MySQL database connectivity.
    """
    db_status = check_db_connection()
    return {
        "status": "online" if db_status.get("status") == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
    }
