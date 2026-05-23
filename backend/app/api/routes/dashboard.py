from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
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
from app.schemas.dashboard_actions import DashboardActionsOut
from app.services.dashboard_actions import build_dashboard_actions

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/actions", response_model=DashboardActionsOut)
def dashboard_actions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DashboardActionsOut:
    return build_dashboard_actions(db, user)


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
