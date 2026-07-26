from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import SupplierDiscoveryRecord, User
from app.models.enums import SupplierDiscoveryStatus
from app.schemas.multibrand_export import (
    QualificationDimensionUpdate,
    SupplierDiscoveryCreate,
    SupplierDiscoveryImportResult,
    SupplierDiscoveryOut,
    SupplierDiscoveryUpdate,
)
from app.schemas.pagination import PaginatedResponse
from app.services.activity import log_activity
from app.services.supplier_discovery_service import (
    activate_discovery_as_partner,
    build_dedup_fingerprint,
    find_duplicate_records,
    import_discovery_rows,
    init_qualification_json,
    normalize_domain,
    parse_csv_import,
    update_qualification_dimension,
)

router = APIRouter(prefix="/supplier-discovery", tags=["supplier-discovery"])

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    SupplierDiscoveryStatus.discovered.value: {
        SupplierDiscoveryStatus.contacted.value,
        SupplierDiscoveryStatus.information_requested.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.contacted.value: {
        SupplierDiscoveryStatus.information_requested.value,
        SupplierDiscoveryStatus.evaluating.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.information_requested.value: {
        SupplierDiscoveryStatus.evaluating.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.evaluating.value: {
        SupplierDiscoveryStatus.sample_requested.value,
        SupplierDiscoveryStatus.qualified.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.sample_requested.value: {
        SupplierDiscoveryStatus.sample_received.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.sample_received.value: {
        SupplierDiscoveryStatus.qualified.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.qualified.value: {
        SupplierDiscoveryStatus.active.value,
        SupplierDiscoveryStatus.rejected.value,
        SupplierDiscoveryStatus.paused.value,
    },
    SupplierDiscoveryStatus.active.value: {SupplierDiscoveryStatus.paused.value},
    SupplierDiscoveryStatus.rejected.value: set(),
    SupplierDiscoveryStatus.paused.value: {SupplierDiscoveryStatus.evaluating.value},
}


def _apply_dedup_fields(body: SupplierDiscoveryCreate) -> dict:
    data = body.model_dump()
    domain = normalize_domain(data.get("source_url"))
    data["domain_key"] = domain
    contact_email = None
    if data.get("contacts_json"):
        contact_email = data["contacts_json"][0].get("email")
    data["dedup_fingerprint"] = build_dedup_fingerprint(
        company_name=data["company_name"],
        domain_key=domain,
        factory_address=data.get("factory_address"),
        contact_email=contact_email,
    )
    return data


@router.get("", response_model=PaginatedResponse[SupplierDiscoveryOut])
def list_supplier_discovery(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    q: str | None = None,
) -> PaginatedResponse[SupplierDiscoveryOut]:
    query = db.query(SupplierDiscoveryRecord)
    if status:
        query = query.filter(SupplierDiscoveryRecord.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(SupplierDiscoveryRecord.company_name.ilike(like), SupplierDiscoveryRecord.brand_name.ilike(like))
        )
    total = query.count()
    rows = query.order_by(SupplierDiscoveryRecord.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return PaginatedResponse(
        items=[SupplierDiscoveryOut.model_validate(r) for r in rows], total=total, page=page, limit=limit
    )


@router.post("", response_model=SupplierDiscoveryOut, status_code=status.HTTP_201_CREATED)
def create_supplier_discovery(
    body: SupplierDiscoveryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    data = _apply_dedup_fields(body)
    dupes = find_duplicate_records(db, fingerprint=data["dedup_fingerprint"])
    if dupes:
        raise HTTPException(status_code=409, detail=f"Duplicate supplier discovery record: {dupes[0].company_name}")
    row = SupplierDiscoveryRecord(
        **data,
        status=SupplierDiscoveryStatus.discovered.value,
        qualification_json=init_qualification_json(),
        owner_user_id=user.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, object_type="supplier_discovery", object_id=row.id, action="created", actor_id=user.id)
    db.commit()
    return SupplierDiscoveryOut.model_validate(row)


@router.post("/import-csv", response_model=SupplierDiscoveryImportResult)
async def import_supplier_discovery_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryImportResult:
    content = (await file.read()).decode("utf-8-sig")
    rows = parse_csv_import(content)
    if not rows:
        raise HTTPException(status_code=400, detail="No valid rows found in CSV")
    created, skipped = import_discovery_rows(db, rows, actor_id=user.id)
    db.commit()
    return SupplierDiscoveryImportResult(
        created_count=len(created),
        skipped_count=len(skipped),
        created=[SupplierDiscoveryOut.model_validate(r) for r in created],
        skipped=skipped,
    )


@router.get("/{record_id}", response_model=SupplierDiscoveryOut)
def get_supplier_discovery(
    record_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    row = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier discovery record not found")
    return SupplierDiscoveryOut.model_validate(row)


@router.patch("/{record_id}", response_model=SupplierDiscoveryOut)
def update_supplier_discovery(
    record_id: UUID,
    body: SupplierDiscoveryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    row = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier discovery record not found")
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] != row.status:
        allowed = ALLOWED_TRANSITIONS.get(row.status, set())
        if data["status"] not in allowed:
            raise HTTPException(status_code=400, detail=f"Illegal status transition from {row.status} to {data['status']}")
        if data["status"] == SupplierDiscoveryStatus.active.value:
            raise HTTPException(
                status_code=400,
                detail="Use POST /supplier-discovery/{id}/activate-partner for manual activation approval",
            )
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return SupplierDiscoveryOut.model_validate(row)


@router.post("/{record_id}/qualification-dimension", response_model=SupplierDiscoveryOut)
def update_qualification(
    record_id: UUID,
    body: QualificationDimensionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    row = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier discovery record not found")
    try:
        update_qualification_dimension(
            row,
            dimension_key=body.dimension_key,
            status=body.status,
            evidence=body.evidence,
            reviewer_id=user.id,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    return SupplierDiscoveryOut.model_validate(row)


@router.post("/{record_id}/activate-partner", response_model=SupplierDiscoveryOut)
def activate_partner_from_discovery(
    record_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplierDiscoveryOut:
    row = db.query(SupplierDiscoveryRecord).filter(SupplierDiscoveryRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier discovery record not found")
    try:
        partner = activate_discovery_as_partner(db, row, actor_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(row)
    log_activity(
        db,
        object_type="manufacturing_partner",
        object_id=partner.id,
        action="activated_from_discovery",
        actor_id=user.id,
        details={"discovery_id": str(record_id)},
    )
    db.commit()
    return SupplierDiscoveryOut.model_validate(row)
