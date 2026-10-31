"""
Subscription Time Machine Endpoints (Module 9).
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.timemachine import (
    TimelineEvent,
    TimeMachineReconstructionResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.services.timemachine_service import TimeMachineService

router = APIRouter(prefix="/timemachine", tags=["Subscription Time Machine"])


@router.get(
    "/subscriptions/{subscription_id}/timeline",
    response_model=List[TimelineEvent],
    summary="Get full chronological audit timeline of events with computed state diffs",
)
def get_subscription_timeline(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TimeMachineService.get_timeline(db, subscription_id)


@router.get(
    "/subscriptions/{subscription_id}/as-of",
    response_model=TimeMachineReconstructionResponse,
    summary="Reconstruct subscription state at an arbitrary past timestamp",
)
def reconstruct_subscription_state(
    subscription_id: int,
    timestamp: str = Query(..., description="Target ISO datetime to reconstruct state as of"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        parsed_dt = datetime.fromisoformat(timestamp.replace(" ", "+"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO datetime format: '{timestamp}'",
        )
    return TimeMachineService.reconstruct_as_of(db, subscription_id, parsed_dt)


@router.post(
    "/subscriptions/{subscription_id}/simulate",
    response_model=SimulationResponse,
    summary="Simulate a what-if state transition without modifying database",
)
def simulate_state_transition(
    subscription_id: int,
    payload: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TimeMachineService.simulate_action(db, subscription_id, payload)
