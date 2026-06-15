"""D8.13 growth operations routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import PERM_MARKET_READ, require_permission
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import User
from app.schemas.growth import (
    GrowthCampaignCreate,
    GrowthCampaignTaskCreate,
    GrowthCampaignTaskUpdate,
    GrowthCampaignUpdate,
    SalesOpportunityCreate,
    SalesOpportunityUpdate,
)
from app.services.growth_operations import (
    build_growth_operations_console,
    create_growth_campaign,
    create_growth_campaign_task,
    create_sales_opportunity,
    get_growth_campaign_detail,
    list_sales_opportunities,
    list_growth_campaigns,
    update_sales_opportunity,
    update_growth_campaign,
    update_growth_campaign_task,
)

router = APIRouter(prefix="/growth", tags=["v1-growth-operations"])


@router.get("/operations-console")
def get_growth_operations_console(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = build_growth_operations_console(db)
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/campaigns")
def get_growth_campaigns(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = list_growth_campaigns(db)
    return success_envelope(data, request_id=get_request_id(request))


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def post_growth_campaign(
    payload: GrowthCampaignCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = create_growth_campaign(db, payload, actor)
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/opportunities")
def get_growth_opportunities(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = list_sales_opportunities(db)
    return success_envelope(data, request_id=get_request_id(request))


@router.post("/opportunities", status_code=status.HTTP_201_CREATED)
def post_growth_opportunity(
    payload: SalesOpportunityCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = create_sales_opportunity(db, payload, actor)
    return success_envelope(data, request_id=get_request_id(request))


@router.patch("/opportunities/{opportunity_id}")
def patch_growth_opportunity(
    opportunity_id: UUID,
    payload: SalesOpportunityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = update_sales_opportunity(db, opportunity_id, payload, actor)
    if data is None:
        raise HTTPException(status_code=404, detail="sales opportunity not found")
    return success_envelope(data, request_id=get_request_id(request))


@router.get("/campaigns/{campaign_id}")
def get_growth_campaign(
    campaign_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = get_growth_campaign_detail(db, campaign_id)
    if data is None:
        raise HTTPException(status_code=404, detail="growth campaign not found")
    return success_envelope(data, request_id=get_request_id(request))


@router.patch("/campaigns/{campaign_id}")
def patch_growth_campaign(
    campaign_id: UUID,
    payload: GrowthCampaignUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = update_growth_campaign(db, campaign_id, payload, actor)
    if data is None:
        raise HTTPException(status_code=404, detail="growth campaign not found")
    return success_envelope(data, request_id=get_request_id(request))


@router.post("/campaigns/{campaign_id}/tasks", status_code=status.HTTP_201_CREATED)
def post_growth_campaign_task(
    campaign_id: UUID,
    payload: GrowthCampaignTaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = create_growth_campaign_task(db, campaign_id, payload, actor)
    if data is None:
        raise HTTPException(status_code=404, detail="growth campaign not found")
    return success_envelope(data, request_id=get_request_id(request))


@router.patch("/tasks/{task_id}")
def patch_growth_campaign_task(
    task_id: UUID,
    payload: GrowthCampaignTaskUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(PERM_MARKET_READ)),
):
    data = update_growth_campaign_task(db, task_id, payload, actor)
    if data is None:
        raise HTTPException(status_code=404, detail="growth campaign task not found")
    return success_envelope(data, request_id=get_request_id(request))
