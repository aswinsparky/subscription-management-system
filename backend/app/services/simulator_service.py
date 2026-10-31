"""
Future Revenue Simulator Engine for Brightloop Nexus.
Provides deterministic mathematical recurring revenue forecasting with transparent assumptions.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.subscription import Subscription
from app.models.simulator import RevenueSimulationScenario
from app.schemas.simulator import SimulationRequest, SimulationResponse, MonthlyForecastPoint


class RevenueSimulatorService:
    @staticmethod
    def calculate_simulation(
        db: Session,
        req: SimulationRequest,
        user_id: Optional[int] = None,
        persist: bool = True,
    ) -> SimulationResponse:
        # 1. Fetch current active subscriptions for actual baseline
        active_subs = list(db.scalars(select(Subscription).where(Subscription.status == "ACTIVE")).all())
        active_count = len(active_subs)

        baseline_mrr = Decimal("0.00")
        for sub in active_subs:
            interval = (sub.billing_interval or "MONTHLY").upper()
            amt = sub.total_amount
            if interval == "MONTHLY":
                baseline_mrr += amt
            elif interval == "YEARLY":
                baseline_mrr += (amt / Decimal("12.00"))
            elif interval == "WEEKLY":
                baseline_mrr += (amt * Decimal("4.333"))
            elif interval == "DAILY":
                baseline_mrr += (amt * Decimal("30.00"))

        baseline_mrr = baseline_mrr.quantize(Decimal("0.01"))
        baseline_arr = (baseline_mrr * Decimal("12.00")).quantize(Decimal("0.01"))

        # Average revenue per user (ARPU)
        arpu = (baseline_mrr / Decimal(str(active_count))) if active_count > 0 else Decimal("49.00")
        arpu = arpu.quantize(Decimal("0.01"))

        # 2. Iterate monthly projection
        monthly_forecast: List[MonthlyForecastPoint] = []
        current_mrr = baseline_mrr
        current_subs = active_count
        now = datetime.utcnow()

        monthly_churn_fraction = req.churn_rate_percent / Decimal("100.00")
        monthly_upgrade_fraction = req.plan_upgrade_rate_percent / Decimal("100.00")
        price_factor = Decimal("1.00") + (req.price_change_percent / Decimal("100.00"))
        discount_factor = Decimal("1.00") - (req.discount_campaign_impact_percent / Decimal("100.00"))

        for m in range(1, req.projection_months + 1):
            # Target month label
            future_month = (now.month + m - 1) % 12 + 1
            future_year = now.year + (now.month + m - 1) // 12
            month_label = datetime(future_year, future_month, 1).strftime("%b %Y")

            # Calculations
            churned_revenue = (current_mrr * monthly_churn_fraction).quantize(Decimal("0.01"))
            churned_subs = int(round(float(current_subs) * float(monthly_churn_fraction)))

            expansion_revenue = (current_mrr * monthly_upgrade_fraction).quantize(Decimal("0.01"))

            # New additions
            new_arpu_effective = arpu * price_factor * discount_factor
            new_revenue = (Decimal(str(req.new_customers_monthly)) * new_arpu_effective).quantize(Decimal("0.01"))

            # Net growth
            net_growth = (new_revenue + expansion_revenue - churned_revenue).quantize(Decimal("0.01"))
            projected_mrr_month = max(Decimal("0.00"), current_mrr + net_growth).quantize(Decimal("0.01"))

            current_subs = max(0, current_subs - churned_subs + req.new_customers_monthly)
            current_mrr = projected_mrr_month

            monthly_forecast.append(
                MonthlyForecastPoint(
                    month_index=m,
                    month_label=month_label,
                    baseline_revenue=baseline_mrr,
                    projected_revenue=projected_mrr_month,
                    new_revenue=new_revenue + expansion_revenue,
                    churned_revenue=churned_revenue,
                    net_growth=net_growth,
                    active_subscriptions=current_subs,
                )
            )

        final_projected_mrr = monthly_forecast[-1].projected_revenue if monthly_forecast else baseline_mrr
        net_mrr_impact = (final_projected_mrr - baseline_mrr).quantize(Decimal("0.01"))
        final_projected_arr = (final_projected_mrr * Decimal("12.00")).quantize(Decimal("0.01"))

        growth_rate = (
            ((final_projected_mrr - baseline_mrr) / baseline_mrr * Decimal("100.00")).quantize(Decimal("0.1"))
            if baseline_mrr > 0 else Decimal("0.0")
        )

        assumptions = {
            "baseline_active_subscriptions": active_count,
            "baseline_arpu": float(arpu),
            "new_customers_monthly": req.new_customers_monthly,
            "churn_rate_percent": float(req.churn_rate_percent),
            "plan_upgrade_rate_percent": float(req.plan_upgrade_rate_percent),
            "price_change_percent": float(req.price_change_percent),
            "discount_campaign_impact_percent": float(req.discount_campaign_impact_percent),
            "projection_months": req.projection_months,
            "forecasting_model": "Deterministic Recurring ARPU & Cohort Simulation",
        }

        # Optional persistence
        if persist:
            scenario = RevenueSimulationScenario(
                scenario_name=req.scenario_name,
                description=f"Forecast of {req.projection_months} months with {req.new_customers_monthly} new customers/mo and {req.churn_rate_percent}% churn",
                created_by_user_id=user_id,
                baseline_mrr=baseline_mrr,
                projected_mrr=final_projected_mrr,
                net_mrr_impact=net_mrr_impact,
                baseline_arr=baseline_arr,
                projected_arr=final_projected_arr,
                assumptions_json=assumptions,
                monthly_forecast_json=[p.model_dump(mode="json") for p in monthly_forecast],
            )
            db.add(scenario)
            db.commit()

        return SimulationResponse(
            scenario_name=req.scenario_name,
            baseline_mrr=baseline_mrr,
            projected_mrr=final_projected_mrr,
            net_mrr_impact=net_mrr_impact,
            baseline_arr=baseline_arr,
            projected_arr=final_projected_arr,
            growth_rate_percent=growth_rate,
            assumptions_used=assumptions,
            monthly_forecast=monthly_forecast,
        )

