from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import MarketIntelligenceItem, User
from app.schemas.ai import GenericAIRequest
from app.schemas.market_domain import MarketItemCreate, MarketItemOut, MarketItemUpdate
from app.schemas.pagination import PaginatedResponse
from app.services.ai import client as ai_client
from app.services.ai import prompts as prompt_lib

router = APIRouter(prefix="/market-intelligence", tags=["market-intelligence"])


@router.get("", response_model=PaginatedResponse[MarketItemOut])
def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    related_company_id: UUID | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[MarketItemOut]:
    q = db.query(MarketIntelligenceItem)
    if related_company_id is not None:
        q = q.filter(MarketIntelligenceItem.related_company_id == related_company_id)
    total = q.count()
    rows = q.order_by(MarketIntelligenceItem.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[MarketItemOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)


@router.post("", response_model=MarketItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    body: MarketItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MarketItemOut:
    row = MarketIntelligenceItem(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return MarketItemOut.model_validate(row)


@router.get("/{item_id}", response_model=MarketItemOut)
def get_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MarketItemOut:
    row = db.query(MarketIntelligenceItem).filter(MarketIntelligenceItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return MarketItemOut.model_validate(row)


@router.put("/{item_id}", response_model=MarketItemOut)
def update_item(
    item_id: UUID,
    body: MarketItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MarketItemOut:
    row = db.query(MarketIntelligenceItem).filter(MarketIntelligenceItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return MarketItemOut.model_validate(row)


@router.post("/{item_id}/ai-summary")
def ai_summary(
    item_id: UUID,
    body: GenericAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.query(MarketIntelligenceItem).filter(MarketIntelligenceItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    ctx = {"title": row.title, "content": row.content or "", **body.context}
    msgs = prompt_lib.market_trend_prompt(ctx)
    text = ai_client.chat_completion(msgs)
    row.ai_summary = text
    row.updated_by_id = user.id
    db.commit()
    from app.models import AIOutput

    ao = AIOutput(
        task_type="market_trend_summary",
        input_object_type="market_intelligence",
        input_object_id=row.id,
        prompt=str(msgs)[:50000],
        output_text=text,
        status="draft",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(ao)
    db.commit()
    db.refresh(ao)
    return {"ai_output_id": str(ao.id), "summary": text}
