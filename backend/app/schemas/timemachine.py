"""
Subscription Time Machine & Event Reconstruction Schemas (Module 9).
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class StateSnapshot(BaseModel):
    status: str
    total_amount: str
    billing_interval: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    next_billing_date: Optional[str] = None
    auto_renew: bool = True


class TimelineEvent(BaseModel):
    id: int
    subscription_id: int
    event_type: str
    timestamp: datetime
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    reason: Optional[str] = None
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Dict[str, Any]
    metadata_json: Optional[Dict[str, Any]] = None
    diff_fields: Dict[str, Dict[str, Any]]  # field: {"from": ..., "to": ...}

    model_config = ConfigDict(from_attributes=True)


class TimeMachineReconstructionResponse(BaseModel):
    subscription_id: int
    subscription_number: str
    customer_name: str
    target_timestamp: datetime
    events_replayed_count: int
    total_events_count: int
    reconstructed_state: StateSnapshot
    current_live_state: StateSnapshot
    last_applied_event: Optional[TimelineEvent] = None


class SimulationRequest(BaseModel):
    action: str  # PAUSE, RESUME, RENEW, CANCEL, CLOSE
    action_date: Optional[datetime] = None
    reason: Optional[str] = None


class SimulationResponse(BaseModel):
    subscription_id: int
    action: str
    is_allowed: bool
    rejection_reason: Optional[str] = None
    current_state: StateSnapshot
    predicted_state: Optional[StateSnapshot] = None
    policy_checks: Dict[str, bool]
