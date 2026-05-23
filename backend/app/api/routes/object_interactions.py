from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.object_type_http import parse_object_type_path
from app.models import Interaction, User
from app.schemas.crm import InteractionOut
from app.schemas.pagination import PaginatedResponse

router_obj = APIRouter(prefix="/objects", tags=["objects"])


@router_obj.get("/{object_type}/{object_id}/interactions", response_model=PaginatedResponse[InteractionOut])
def list_object_interactions(
    object_type: str,
    object_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[InteractionOut]:
    ot = parse_object_type_path(object_type)
    q = db.query(Interaction).filter(
        Interaction.related_object_type == ot,
        Interaction.related_object_id == object_id,
    )
    total = q.count()
    rows = q.order_by(Interaction.interaction_date.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(items=[InteractionOut.model_validate(r) for r in rows], total=total, page=page, limit=limit)
