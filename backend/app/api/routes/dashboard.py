from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    Company,
    Lead,
    ManufacturingPartner,
    Order,
    RFQ,
    Sample,
    Task,
    User,
)
from app.schemas.dashboard import DashboardSummary
from app.schemas.business_execution import BusinessExecutionOut
from app.schemas.dashboard_actions import (
    DailyDecisionQueueOut,
    DailyQueueHandlingRecordOut,
    DailyQueueHandlingUpdate,
    DashboardActionsOut,
)
from app.services.dashboard_actions import build_dashboard_actions
from app.services.business_execution import (
    build_business_execution_center,
    build_customer_value_intelligence,
    build_partner_performance_intelligence,
    build_revenue_forecast_intelligence,
)
from app.services.daily_decision_queue import (
    build_daily_decision_queue,
    list_daily_queue_handling,
    update_daily_queue_handling,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/actions", response_model=DashboardActionsOut)
def dashboard_actions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardActionsOut:
    return build_dashboard_actions(db, user)


@router.get("/daily-decision-queue", response_model=DailyDecisionQueueOut)
def dashboard_daily_decision_queue(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyDecisionQueueOut:
    return build_daily_decision_queue(db, user)


@router.get("/business-execution", response_model=BusinessExecutionOut)
def dashboard_business_execution(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BusinessExecutionOut:
    return build_business_execution_center(db, user)


@router.get("/customer-value-intelligence")
def dashboard_customer_value_intelligence(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return build_customer_value_intelligence(db, limit=limit)


@router.get("/revenue-forecast-intelligence")
def dashboard_revenue_forecast_intelligence(
    limit: int = Query(80, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return build_revenue_forecast_intelligence(db, limit=limit)


@router.get("/partner-performance-intelligence")
def dashboard_partner_performance_intelligence(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return build_partner_performance_intelligence(db, limit=limit)


@router.get("/daily-decision-queue/handling", response_model=list[DailyQueueHandlingRecordOut])
def dashboard_daily_queue_handling_records(
    source_type: str | None = Query(None),
    source_id: str | None = Query(None),
    partner_focus: str | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DailyQueueHandlingRecordOut]:
    return list_daily_queue_handling(
        db,
        source_type=source_type,
        source_id=source_id,
        partner_focus=partner_focus,
        category=category,
    )


@router.patch("/daily-decision-queue/handling", response_model=DailyQueueHandlingRecordOut)
def dashboard_update_daily_queue_handling(
    body: DailyQueueHandlingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DailyQueueHandlingRecordOut:
    try:
        return update_daily_queue_handling(db, user, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardSummary:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    today = date.today()

    leads_week = db.query(func.count(Lead.id)).filter(Lead.created_at >= week_ago).scalar() or 0
    hot_leads = (
        db.query(Lead)
        .filter(Lead.is_active.is_(True), Lead.priority == "high")
        .order_by(Lead.updated_at.desc())
        .limit(10)
        .all()
    )
    strategic = (
        db.query(Company)
        .filter(
            Company.is_active.is_(True),
            Company.strategic_level.isnot(None),
            Company.strategic_level != "",
        )
        .order_by(Company.updated_at.desc())
        .limit(10)
        .all()
    )
    due_tasks = (
        db.query(Task)
        .filter(Task.is_active.is_(True), Task.status == "open", Task.due_at.isnot(None), Task.due_at <= now)
        .order_by(Task.due_at.asc())
        .limit(20)
        .all()
    )
    followup_leads = (
        db.query(Lead)
        .filter(Lead.is_active.is_(True), Lead.next_action_due_date.isnot(None), Lead.next_action_due_date <= today)
        .order_by(Lead.next_action_due_date.asc())
        .limit(20)
        .all()
    )
    return DashboardSummary(
        new_leads_this_week=int(leads_week),
        hot_lead_ids=[str(x.id) for x in hot_leads],
        strategic_company_ids=[str(x.id) for x in strategic],
        overdue_task_ids=[str(x.id) for x in due_tasks],
        followup_due_lead_ids=[str(x.id) for x in followup_leads],
        open_rfqs=int(db.query(func.count(RFQ.id)).filter(RFQ.status != "Closed").scalar() or 0),
        open_samples=int(db.query(func.count(Sample.id)).scalar() or 0),
        active_orders=int(db.query(func.count(Order.id)).scalar() or 0),
        partner_count=int(db.query(func.count(ManufacturingPartner.id)).filter(ManufacturingPartner.is_active.is_(True)).scalar() or 0),
    )
