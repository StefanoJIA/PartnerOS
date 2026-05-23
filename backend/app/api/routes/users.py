from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.users_domain import UserBriefOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserBriefOut])
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[UserBriefOut]:
    q = db.query(User).filter(User.is_active.is_(True))
    total = q.count()
    rows = q.order_by(User.email).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[UserBriefOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
    )
