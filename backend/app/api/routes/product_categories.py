from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import ProductCategory, User
from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: str
    slug: str
    name: str

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/product-categories", tags=["product-categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CategoryOut]:
    rows = db.query(ProductCategory).order_by(ProductCategory.name).all()
    return [CategoryOut(id=str(r.id), slug=r.slug, name=r.name) for r in rows]
