"""
Subscription Time Machine Service (Module 9).
Reconstructs historical subscription state at arbitrary past timestamps by replaying
the append-only event ledger and executes what-if predictive simulations.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.subscription import Subscription, SubscriptionEvent
from app.models.plan import Plan
from app.services.subscription_service import SubscriptionService
from app.schemas.timemachine import (
    TimelineEvent,
    StateSnapshot,
    TimeMachineReconstructionResponse,
    SimulationRequest,
    SimulationResponse,
)


class TimeMachineService:

    @staticmethod
    def _compute_diff(prev: Optional[Dict[str, Any]], curr: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        diff = {}
        if not prev:
            for k, v in curr.items():
                diff[k] = {"from": None, "to": v}
            return diff

        for k, v in curr.items():
            prev_v = prev.get(k)
            if prev_v != v:
                diff[k] = {"from": prev_v, "to": v}
        return diff

    @classmethod
    def get_timeline(cls, db: Session, subscription_id: int) -> List[TimelineEvent]:
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        events = (
            db.query(SubscriptionEvent)
            .filter(SubscriptionEvent.subscription_id == subscription_id)
            .order_by(SubscriptionEvent.created_at.asc(), SubscriptionEvent.id.asc())
            .all()
        )

        timeline = []
        for e in events:
            diff = cls._compute_diff(e.previous_state, e.new_state)
            timeline.append(
                TimelineEvent(
                    id=e.id,
                    subscription_id=e.subscription_id,
                    event_type=e.event_type,
                    timestamp=e.created_at,
                    actor_email=e.actor_email,
                    actor_role=e.actor_role,
                    reason=e.reason,
                    previous_state=e.previous_state,
                    new_state=e.new_state,
                    metadata_json=e.metadata_json,
                    diff_fields=diff,
                )
            )
        return timeline

    @classmethod
    def reconstruct_as_of(
        cls, db: Session, subscription_id: int, as_of_time: datetime
    ) -> TimeMachineReconstructionResponse:
        sub = (
            db.query(Subscription)
            .options(
                joinedload(Subscription.customer),
                joinedload(Subscription.plan),
            )
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        all_events = (
            db.query(SubscriptionEvent)
            .filter(SubscriptionEvent.subscription_id == subscription_id)
            .order_by(SubscriptionEvent.created_at.asc(), SubscriptionEvent.id.asc())
            .all()
        )

        target_utc = as_of_time.replace(tzinfo=timezone.utc) if as_of_time.tzinfo is None else as_of_time
        replayed_events = []
        for e in all_events:
            e_time = e.created_at.replace(tzinfo=timezone.utc) if e.created_at.tzinfo is None else e.created_at
            if e_time <= target_utc:
                replayed_events.append(e)

        if not replayed_events:
            # Fall back to first available event if as_of is earlier than first event
            if all_events:
                replayed_events = [all_events[0]]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No events exist for this subscription.",
                )

        # Replay states sequentially
        accumulated_state: Dict[str, Any] = {}
        for ev in replayed_events:
            accumulated_state.update(ev.new_state)

        last_evt = replayed_events[-1]
        last_applied = TimelineEvent(
            id=last_evt.id,
            subscription_id=last_evt.subscription_id,
            event_type=last_evt.event_type,
            timestamp=last_evt.created_at,
            actor_email=last_evt.actor_email,
            actor_role=last_evt.actor_role,
            reason=last_evt.reason,
            previous_state=last_evt.previous_state,
            new_state=last_evt.new_state,
            metadata_json=last_evt.metadata_json,
            diff_fields=cls._compute_diff(last_evt.previous_state, last_evt.new_state),
        )

        live_snap_dict = SubscriptionService._snapshot_state(sub)

        return TimeMachineReconstructionResponse(
            subscription_id=sub.id,
            subscription_number=sub.subscription_number,
            customer_name=sub.customer.full_name if sub.customer else f"Customer #{sub.customer_id}",
            target_timestamp=target_utc,
            events_replayed_count=len(replayed_events),
            total_events_count=len(all_events),
            reconstructed_state=StateSnapshot(**accumulated_state),
            current_live_state=StateSnapshot(**live_snap_dict),
            last_applied_event=last_applied,
        )

    @classmethod
    def simulate_action(
        cls, db: Session, subscription_id: int, payload: SimulationRequest
    ) -> SimulationResponse:
        sub = (
            db.query(Subscription)
            .options(joinedload(Subscription.plan))
            .filter(Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")

        current_snap = StateSnapshot(**SubscriptionService._snapshot_state(sub))
        action = payload.action.upper()
        plan = sub.plan

        is_allowed = True
        rejection_reason = None
        predicted: Optional[StateSnapshot] = None
        policy_checks: Dict[str, bool] = {}

        if action == "PAUSE":
            policy_checks["is_active"] = (sub.status == "ACTIVE")
            policy_checks["plan_pause_allowed"] = bool(plan and plan.pause_allowed)
            if not policy_checks["is_active"]:
                is_allowed = False
                rejection_reason = f"Cannot pause subscription with status '{sub.status}'. Must be ACTIVE."
            elif not policy_checks["plan_pause_allowed"]:
                is_allowed = False
                rejection_reason = f"Plan '{plan.name if plan else ''}' policy prohibits pausing."
            else:
                pred_dict = SubscriptionService._snapshot_state(sub)
                pred_dict["status"] = "PAUSED"
                predicted = StateSnapshot(**pred_dict)

        elif action == "RESUME":
            policy_checks["is_paused"] = (sub.status == "PAUSED")
            if not policy_checks["is_paused"]:
                is_allowed = False
                rejection_reason = f"Cannot resume subscription with status '{sub.status}'. Must be PAUSED."
            else:
                pred_dict = SubscriptionService._snapshot_state(sub)
                pred_dict["status"] = "ACTIVE"
                predicted = StateSnapshot(**pred_dict)

        elif action == "RENEW":
            policy_checks["is_active"] = (sub.status == "ACTIVE")
            policy_checks["auto_renew_enabled"] = bool(sub.auto_renew)
            policy_checks["plan_renewal_allowed"] = bool(plan and plan.renewal_allowed)
            if not policy_checks["is_active"]:
                is_allowed = False
                rejection_reason = "Subscription must be ACTIVE to renew."
            elif not policy_checks["plan_renewal_allowed"]:
                is_allowed = False
                rejection_reason = f"Plan '{plan.name if plan else ''}' prohibits renewals."
            else:
                pred_dict = SubscriptionService._snapshot_state(sub)
                delta = SubscriptionService._get_interval_delta(sub.billing_interval)
                next_start = sub.current_period_end
                next_end = next_start + delta
                pred_dict["current_period_start"] = next_start.isoformat()
                pred_dict["current_period_end"] = next_end.isoformat()
                pred_dict["next_billing_date"] = next_end.isoformat()
                predicted = StateSnapshot(**pred_dict)

        elif action == "CANCEL":
            policy_checks["not_terminal"] = (sub.status not in ("CANCELLED", "CLOSED"))
            now = datetime.now(timezone.utc)
            expiry = sub.expiry_date.replace(tzinfo=timezone.utc) if sub.expiry_date.tzinfo is None else sub.expiry_date
            is_early = now < expiry
            policy_checks["early_cancellation_allowed"] = bool(not is_early or (plan and plan.early_cancellation_allowed))

            if not policy_checks["not_terminal"]:
                is_allowed = False
                rejection_reason = f"Subscription is already in terminal status '{sub.status}'."
            elif not policy_checks["early_cancellation_allowed"]:
                is_allowed = False
                rejection_reason = f"Plan '{plan.name if plan else ''}' prohibits early cancellation."
            else:
                pred_dict = SubscriptionService._snapshot_state(sub)
                pred_dict["status"] = "CANCELLED"
                predicted = StateSnapshot(**pred_dict)

        elif action == "CLOSE":
            policy_checks["not_terminal"] = (sub.status not in ("CANCELLED", "CLOSED"))
            if not policy_checks["not_terminal"]:
                is_allowed = False
                rejection_reason = f"Subscription is already in terminal status '{sub.status}'."
            else:
                pred_dict = SubscriptionService._snapshot_state(sub)
                pred_dict["status"] = "CLOSED"
                predicted = StateSnapshot(**pred_dict)
        else:
            is_allowed = False
            rejection_reason = f"Unsupported simulation action '{action}'."

        return SimulationResponse(
            subscription_id=sub.id,
            action=action,
            is_allowed=is_allowed,
            rejection_reason=rejection_reason,
            current_state=current_snap,
            predicted_state=predicted,
            policy_checks=policy_checks,
        )
