"""
Revenue Guardian Anomaly Detection API Endpoints (Member 2).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user
from app.models.user import User
from app.schemas.revenue_guardian import (
    RevenueGuardianFindingResponse,
    RevenueGuardianRunSummary,
    RevenueGuardianResolveRequest,
)
from app.services.revenue_guardian_service import RevenueGuardianService

router = APIRouter()


@router.get("/findings", response_model=List[RevenueGuardianFindingResponse], summary="List revenue leakage audit findings")
def list_findings(
    status: Optional[str] = Query(None, description="Filter by resolution status (OPEN, RESOLVED, DISMISSED)"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    findings = RevenueGuardianService.get_findings(db, status_filter=status, severity_filter=severity)
    return [RevenueGuardianFindingResponse.model_validate(f) for f in findings]


@router.post("/run", response_model=RevenueGuardianRunSummary, summary="Execute on-demand revenue leakage audit")
def run_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return RevenueGuardianService.run_audit(db, run_type="MANUAL", user_id=current_user.id)


@router.post("/findings/{finding_id}/resolve", response_model=RevenueGuardianFindingResponse, summary="Review and resolve finding")
def resolve_finding(
    finding_id: int,
    data: RevenueGuardianResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    finding = RevenueGuardianService.resolve_finding(db, finding_id, data, current_user)
    return RevenueGuardianFindingResponse.model_validate(finding)

