"""V1 product catalog routes (D6.2)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.errors import ApiError, NOT_FOUND
from app.core.request_id import get_request_id
from app.core.responses import success_envelope
from app.models import FxRate, ManufacturingPartner, ProductCatalog, ProductCostModel, ProductPriceTier, User
from app.schemas.quote_catalog import ProductCatalogCreate, ProductCatalogOut, ProductCatalogUpdate
from app.services.quotes.fx_rates import ensure_latest_fx_rate
from app.services.quotes.pricing_assumptions import PricingAssumptionSnapshot, get_current_pricing_assumptions
from app.services.quotes.pricing_calculations import compute_cost_breakdown

router = APIRouter(prefix="/products", tags=["v1-products"])


def _decimal_text(value: Decimal | int | float | str | None, places: str = "0.01") -> str | None:
    if value is None:
        return None
    dec = Decimal(str(value))
    return str(dec.quantize(Decimal(places)))


def _latest_fx(db: Session) -> FxRate | None:
    return ensure_latest_fx_rate(db, base="USD", quote="CNY")


def _latest_cost_models(db: Session, product_ids: list[UUID]) -> dict[UUID, ProductCostModel]:
    if not product_ids:
        return {}
    rows = (
        db.query(ProductCostModel)
        .filter(ProductCostModel.product_id.in_(product_ids))
        .order_by(
            ProductCostModel.product_id.asc(),
            ProductCostModel.effective_from.desc().nullslast(),
            ProductCostModel.created_at.desc(),
        )
        .all()
    )
    latest: dict[UUID, ProductCostModel] = {}
    for row in rows:
        latest.setdefault(row.product_id, row)
    return latest


def _target_margin(attrs: dict | None) -> str | None:
    if not attrs:
        return None
    raw = attrs.get("target_margin") or attrs.get("sales_margin_rate")
    if raw is None:
        multiplier = attrs.get("quote_markup_multiplier")
        if multiplier is None:
            return None
        try:
            raw = Decimal(str(multiplier)) - Decimal("1")
        except Exception:
            return None
    try:
        dec = Decimal(str(raw))
    except Exception:
        return None
    return str((dec * Decimal("100")).quantize(Decimal("0.01")))


def _pricing_model_summary(
    product: ProductCatalog,
    *,
    cost_model: ProductCostModel | None,
    latest_fx: FxRate | None,
    quote_interval_count: int,
    assumptions: PricingAssumptionSnapshot | None = None,
) -> dict:
    attrs = product.attributes_json or {}
    fx_age_days: int | None = None
    if latest_fx:
        fx_age_days = (date.today() - latest_fx.rate_date).days
    calculated_cost: dict[str, str | bool | None] = {}
    if cost_model and latest_fx:
        calculated_cost, _ = compute_cost_breakdown(
            unit_material_cost=cost_model.unit_material_cost,
            cost_currency=cost_model.cost_currency or "CNY",
            unit_weight=cost_model.unit_weight,
            ocean_freight_unit_price=assumptions.ocean_freight_unit_price
            if assumptions
            else cost_model.ocean_freight_unit_price,
            domestic_transport_cost=None if assumptions else cost_model.domestic_transport_cost,
            domestic_profit_rate=cost_model.domestic_profit_rate,
            fx_rate_usd_cny=latest_fx.rate,
            stored_fob_cost_usd=cost_model.fob_cost_usd,
            stored_ddp_cost_usd=cost_model.ddp_cost_usd,
            ocean_freight_source=assumptions.ocean_freight_source if assumptions else "product_cost_model",
            use_stored_cost_snapshot=assumptions is None,
        )
    return {
        "internal_only": True,
        "has_cost_model": cost_model is not None,
        "has_interval_pricing": quote_interval_count > 0,
        "customer_quote_mode": attrs.get("customer_safe_pricing_mode") or "full_quantity_interval_quote_table",
        "cost_currency": cost_model.cost_currency if cost_model else None,
        "factory_cost_rmb": _decimal_text(cost_model.unit_material_cost) if cost_model else None,
        "unit_weight_kg": _decimal_text(cost_model.unit_weight, "0.0001") if cost_model else None,
        "ocean_freight_unit_price": _decimal_text(assumptions.ocean_freight_unit_price, "0.0001")
        if assumptions
        else (_decimal_text(cost_model.ocean_freight_unit_price, "0.0001") if cost_model else None),
        "ocean_freight_unit": assumptions.ocean_freight_unit if assumptions else "RMB/kg",
        "ocean_freight_source": assumptions.ocean_freight_source if assumptions else "product_cost_model",
        "ocean_freight_effective_from": assumptions.ocean_freight_effective_from.isoformat()
        if assumptions and assumptions.ocean_freight_effective_from
        else None,
        "domestic_transport_cost_rmb": calculated_cost.get("domestic_transport_cost")
        or (_decimal_text(cost_model.domestic_transport_cost) if cost_model else None),
        "domestic_profit_rate_percent": str((Decimal(str(cost_model.domestic_profit_rate)) * Decimal("100")).quantize(Decimal("0.01")))
        if cost_model and cost_model.domestic_profit_rate is not None
        else None,
        "fob_cost_usd": calculated_cost.get("fob_cost_usd") or (_decimal_text(cost_model.fob_cost_usd) if cost_model else None),
        "ddp_cost_usd": calculated_cost.get("ddp_cost_usd") or (_decimal_text(cost_model.ddp_cost_usd) if cost_model else None),
        "stored_fob_cost_usd_snapshot": _decimal_text(cost_model.fob_cost_usd) if cost_model else None,
        "stored_ddp_cost_usd_snapshot": _decimal_text(cost_model.ddp_cost_usd) if cost_model else None,
        "stored_cost_snapshot_used": bool(calculated_cost.get("stored_cost_snapshot_used", assumptions is None)),
        "product_target_margin_percent": _target_margin(attrs),
        "fx_rate_usd_cny": _decimal_text(latest_fx.rate, "0.0001") if latest_fx else None,
        "fx_rate_date": latest_fx.rate_date.isoformat() if latest_fx else None,
        "fx_source": latest_fx.source if latest_fx else None,
        "fx_is_stale": fx_age_days is not None and fx_age_days > 7,
        "fx_age_days": fx_age_days,
        "calculation_basis": [
            "factory cost is maintained per product in RMB",
            "transport cost = unit weight * ocean freight unit price",
            "FOB/DDP cost is converted by the latest stored USD-CNY FX rate",
            "customer quote displays every quantity interval for each selected product",
            "cost, margin, and logistics assumptions remain internal-only",
        ],
    }


def _configuration_summary(attrs: dict | None) -> dict | None:
    if not attrs:
        return None
    specs = attrs.get("product_specs") or {}
    model = attrs.get("configuration_model") or {}
    colors = attrs.get("color_options_summary") or {}
    inventory = attrs.get("inventory_snapshot") or []
    return {
        "source_system": attrs.get("source_system") or attrs.get("pricing_model_source"),
        "customer_quote_name": attrs.get("customer_quote_name"),
        "base_type": model.get("base_type"),
        "stage": model.get("stage") or specs.get("stages"),
        "column_type": model.get("column_type"),
        "dimensions": model.get("dimensions") or specs.get("specification"),
        "load_capacity": specs.get("load_capacity"),
        "lifting_range": specs.get("lifting_range"),
        "lifting_speed": specs.get("lifting_speed"),
        "package_size": specs.get("package_size"),
        "total_available_colors": colors.get("total_available_colors"),
        "inventory_reference_count": len(inventory) if isinstance(inventory, list) else 0,
        "inventory_not_promised": True,
    }


def _product_payload(
    row: ProductCatalog,
    *,
    partner: ManufacturingPartner | None,
    quote_interval_count: int,
    cost_model: ProductCostModel | None = None,
    latest_fx: FxRate | None = None,
    assumptions: PricingAssumptionSnapshot | None = None,
) -> dict:
    payload = ProductCatalogOut.model_validate(row).model_dump(mode="json")
    payload["partner_code"] = partner.partner_code if partner else None
    payload["partner_name"] = partner.partner_name if partner else None
    payload["quote_interval_count"] = quote_interval_count
    payload["has_interval_pricing"] = quote_interval_count > 0
    payload["configuration_summary"] = _configuration_summary(row.attributes_json)
    payload["pricing_model_summary"] = _pricing_model_summary(
        row,
        cost_model=cost_model,
        latest_fx=latest_fx,
        quote_interval_count=quote_interval_count,
        assumptions=assumptions,
    )
    return payload


@router.get("")
def list_products(
    request: Request,
    partner_id: UUID | None = None,
    partner_code: str | None = None,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(ProductCatalog)
    if partner_id:
        q = q.filter(ProductCatalog.partner_id == partner_id)
    if partner_code:
        partner = (
            db.query(ManufacturingPartner)
            .filter(ManufacturingPartner.partner_code.ilike(partner_code.strip()))
            .first()
        )
        if not partner:
            q = q.filter(False)
        else:
            q = q.filter(ProductCatalog.partner_id == partner.id)
    if category:
        q = q.filter(ProductCatalog.product_category == category)
    if status:
        q = q.filter(ProductCatalog.status == status)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(
            ProductCatalog.product_name.ilike(like)
            | ProductCatalog.internal_sku.ilike(like)
            | ProductCatalog.partner_product_code.ilike(like)
        )
    total = q.count()
    rows = (
        q.order_by(ProductCatalog.image_url.is_(None).asc(), ProductCatalog.product_name.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    partner_ids = {r.partner_id for r in rows}
    product_ids = [r.id for r in rows]
    partners = {
        p.id: p
        for p in db.query(ManufacturingPartner).filter(ManufacturingPartner.id.in_(partner_ids)).all()
    } if partner_ids else {}
    tier_counts = {
        product_id: count
        for product_id, count in (
            db.query(ProductPriceTier.product_id, func.count(ProductPriceTier.id))
            .filter(ProductPriceTier.product_id.in_(product_ids))
            .group_by(ProductPriceTier.product_id)
            .all()
            if product_ids
            else []
        )
    }
    cost_models = _latest_cost_models(db, product_ids)
    latest_fx = _latest_fx(db)
    assumptions = get_current_pricing_assumptions(db)
    items = [
        _product_payload(
            r,
            partner=partners.get(r.partner_id),
            quote_interval_count=int(tier_counts.get(r.id, 0)),
            cost_model=cost_models.get(r.id),
            latest_fx=latest_fx,
            assumptions=assumptions,
        )
        for r in rows
    ]
    rid = get_request_id(request)
    return success_envelope(
        {"items": items, "total": total, "page": page, "limit": limit},
        request_id=rid,
        pagination={"page": page, "limit": limit, "total": total},
    )


@router.get("/{product_id}")
def get_product(
    product_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    row = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "product not found", status_code=404)
    partner = db.query(ManufacturingPartner).filter(ManufacturingPartner.id == row.partner_id).first()
    quote_interval_count = (
        db.query(func.count(ProductPriceTier.id)).filter(ProductPriceTier.product_id == row.id).scalar() or 0
    )
    cost_model = _latest_cost_models(db, [row.id]).get(row.id)
    latest_fx = _latest_fx(db)
    assumptions = get_current_pricing_assumptions(db)
    rid = get_request_id(request)
    return success_envelope(
        _product_payload(
            row,
            partner=partner,
            quote_interval_count=int(quote_interval_count),
            cost_model=cost_model,
            latest_fx=latest_fx,
            assumptions=assumptions,
        ),
        request_id=rid,
    )


@router.post("")
def create_product(
    body: ProductCatalogCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = ProductCatalog(**body.model_dump(), created_by_id=user.id, updated_by_id=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    rid = get_request_id(request)
    return success_envelope(
        ProductCatalogOut.model_validate(row).model_dump(mode="json"),
        request_id=rid,
        status_code=201,
    )


@router.patch("/{product_id}")
def update_product(
    product_id: UUID,
    body: ProductCatalogUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.query(ProductCatalog).filter(ProductCatalog.id == product_id).first()
    if not row:
        raise ApiError(NOT_FOUND, "product not found", status_code=404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_by_id = user.id
    db.commit()
    db.refresh(row)
    rid = get_request_id(request)
    return success_envelope(ProductCatalogOut.model_validate(row).model_dump(mode="json"), request_id=rid)
