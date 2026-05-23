from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Company, Contact, User
from app.schemas.crm import ContactCreate, ContactDetailOut, ContactListItemOut, ContactOut, ContactUpdate
from app.schemas.object_workspaces import ContactWorkspaceOut
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity
from app.services.workspaces import build_contact_workspace

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _contact_list_item(c: Contact, company_name: str | None) -> ContactListItemOut:
    base = ContactDetailOut.model_validate(c).model_dump()
    base["company_name"] = company_name
    return ContactListItemOut.model_validate(base)


@router.get("", response_model=PaginatedResponse[ContactListItemOut])
def list_contacts(
    company_id: UUID | None = None,
    q: str | None = None,
    title: str | None = None,
    contact_type: str | None = None,
    decision_maker_level: str | None = None,
    contact_status: str | None = Query(None, alias="status"),
    has_email: bool | None = None,
    has_linkedin: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[ContactListItemOut]:
    query = db.query(Contact, Company.company_name).join(Company, Contact.company_id == Company.id).filter(
        Contact.is_active.is_(True)
    )
    if company_id:
        query = query.filter(Contact.company_id == company_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Contact.first_name.ilike(like),
                Contact.last_name.ilike(like),
                Contact.email.ilike(like),
                Company.company_name.ilike(like),
            )
        )
    if title:
        query = query.filter(Contact.title.ilike(f"%{title}%"))
    if contact_type:
        query = query.filter(Contact.contact_type == contact_type)
    if decision_maker_level:
        query = query.filter(Contact.decision_maker_level == decision_maker_level)
    if contact_status:
        query = query.filter(Contact.status == contact_status)
    if has_email is True:
        query = query.filter(Contact.email.isnot(None), Contact.email != "")
    if has_email is False:
        query = query.filter(or_(Contact.email.is_(None), Contact.email == ""))
    if has_linkedin is True:
        query = query.filter(Contact.linkedin_url.isnot(None), Contact.linkedin_url != "")
    if has_linkedin is False:
        query = query.filter(or_(Contact.linkedin_url.is_(None), Contact.linkedin_url == ""))
    total = query.count()
    rows = query.order_by(Contact.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    items = [_contact_list_item(c, cn) for c, cn in rows]
    return PaginatedResponse(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(
    body: ContactCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactOut:
    row = Contact(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="contact", object_id=row.id, action="contact_created", actor_id=user.id)
    log_activity(
        db,
        object_type="company",
        object_id=body.company_id,
        action="contact_added_from_company",
        actor_id=user.id,
        diff={"contact_id": str(row.id)},
    )
    db.commit()
    return ContactOut.model_validate(row)


@router.get("/{contact_id}/workspace", response_model=ContactWorkspaceOut)
def get_contact_workspace(
    contact_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContactWorkspaceOut:
    ws = build_contact_workspace(db, contact_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ws


@router.get("/{contact_id}", response_model=ContactDetailOut)
def get_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContactDetailOut:
    row = db.query(Contact).filter(Contact.id == contact_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactDetailOut.model_validate(row)


@router.put("/{contact_id}", response_model=ContactDetailOut)
def update_contact(
    contact_id: UUID,
    body: ContactUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactDetailOut:
    row = db.query(Contact).filter(Contact.id == contact_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="contact", object_id=row.id, action="contact_updated", actor_id=user.id, diff=data)
    db.commit()
    return ContactDetailOut.model_validate(row)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    row = db.query(Contact).filter(Contact.id == contact_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    row.is_active = False
    row.updated_by_id = user.id
    db.commit()
    log_activity(db, object_type="contact", object_id=row.id, action="soft_deleted", actor_id=user.id)
    db.commit()
