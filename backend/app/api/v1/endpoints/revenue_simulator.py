"""
Future Revenue Simulator API Endpoints (Member 2).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_staff_or_admin_user
from app.models.user import User
from app.schemas.simulator import SimulationRequest, SimulationResponse
from app.services.simulator_service import RevenueSimulatorService

router = APIRouter()


@router.post("/simulate", response_model=SimulationResponse, summary="Simulate future recurring revenue projections")
def simulate_revenue(
    data: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_staff_or_admin_user),
):
    return RevenueSimulatorService.calculate_simulation(db, data, user_id=current_user.id)

