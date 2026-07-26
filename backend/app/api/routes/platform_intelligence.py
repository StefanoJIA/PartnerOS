from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import ChannelIntelligenceMetric, PlatformBenchmarkRecord, User
from app.schemas.multibrand_export import ChannelMetricOut, PlatformBenchmarkOut
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/platform-intelligence", tags=["platform-intelligence"])


@router.get("/benchmarks", response_model=PaginatedResponse[PlatformBenchmarkOut])
def list_platform_benchmarks(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    platform: str | None = None,
) -> PaginatedResponse[PlatformBenchmarkOut]:
    query = db.query(PlatformBenchmarkRecord)
    if platform:
        query = query.filter(PlatformBenchmarkRecord.platform_name.ilike(f"%{platform}%"))
    total = query.count()
    rows = (
        query.order_by(PlatformBenchmarkRecord.build_priority, PlatformBenchmarkRecord.platform_name)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return PaginatedResponse(
        items=[PlatformBenchmarkOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )


@router.get("/channels", response_model=PaginatedResponse[ChannelMetricOut])
def list_channel_metrics(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    channel: str | None = None,
) -> PaginatedResponse[ChannelMetricOut]:
    query = db.query(ChannelIntelligenceMetric)
    if channel:
        query = query.filter(ChannelIntelligenceMetric.channel_source == channel)
    total = query.count()
    rows = query.order_by(ChannelIntelligenceMetric.period_label.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[ChannelMetricOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )
