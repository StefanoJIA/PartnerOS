from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/container-calculator", tags=["tools"])


class ContainerCalcBody(BaseModel):
    length_cm: float
    width_cm: float
    height_cm: float
    cartons: int


class CartonSpec(BaseModel):
    label: str = "Carton"
    length_cm: float = Field(..., gt=0)
    width_cm: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    cartons: int = Field(..., gt=0)
    weight_kg: float | None = Field(default=None, ge=0)


class PalletPlanBody(BaseModel):
    pallet_length_cm: float = Field(default=120, gt=0)
    pallet_width_cm: float = Field(default=100, gt=0)
    pallet_height_cm: float = Field(default=20, ge=0)
    max_total_height_cm: float = Field(default=200, gt=0)
    max_continuous_layers: int = Field(default=8, ge=1)
    container_cbm: float = Field(default=68, gt=0)
    carton_specs: list[CartonSpec] = Field(..., min_length=1)


def _best_layer_fit(carton: CartonSpec, pallet_length: float, pallet_width: float) -> dict:
    normal_x = int(pallet_length // carton.length_cm)
    normal_y = int(pallet_width // carton.width_cm)
    rotated_x = int(pallet_length // carton.width_cm)
    rotated_y = int(pallet_width // carton.length_cm)
    normal = {
        "orientation": "normal",
        "carton_length_cm": carton.length_cm,
        "carton_width_cm": carton.width_cm,
        "along_length": normal_x,
        "along_width": normal_y,
        "cartons_per_layer": normal_x * normal_y,
    }
    rotated = {
        "orientation": "rotated",
        "carton_length_cm": carton.width_cm,
        "carton_width_cm": carton.length_cm,
        "along_length": rotated_x,
        "along_width": rotated_y,
        "cartons_per_layer": rotated_x * rotated_y,
    }
    return max([normal, rotated], key=lambda item: item["cartons_per_layer"])


def _balanced_layer_segments(total_layers: int, max_continuous_layers: int) -> list[int]:
    if total_layers <= 0:
        return []
    segments_count = (total_layers + max_continuous_layers - 1) // max_continuous_layers
    base = total_layers // segments_count
    extra = total_layers % segments_count
    return [base + (1 if idx < extra else 0) for idx in range(segments_count)]


def _max_layers_per_pallet(
    carton_height: float,
    *,
    pallet_height: float,
    max_total_height: float,
    max_continuous_layers: int,
) -> tuple[int, list[int], int, float]:
    max_by_height = int((max_total_height - pallet_height) // carton_height)
    best_layers = 0
    best_segments: list[int] = []
    best_dividers = 0
    best_height = pallet_height
    for layers in range(max_by_height, 0, -1):
        segments = _balanced_layer_segments(layers, max_continuous_layers)
        dividers = max(len(segments) - 1, 0)
        total_height = pallet_height + layers * carton_height + dividers * pallet_height
        if total_height <= max_total_height:
            best_layers = layers
            best_segments = segments
            best_dividers = dividers
            best_height = total_height
            break
    return best_layers, best_segments, best_dividers, best_height


def _plan_carton_spec(body: PalletPlanBody, carton: CartonSpec) -> dict:
    layer_fit = _best_layer_fit(carton, body.pallet_length_cm, body.pallet_width_cm)
    cartons_per_layer = layer_fit["cartons_per_layer"]
    carton_cbm = carton.length_cm * carton.width_cm * carton.height_cm / 1_000_000
    total_cbm = carton_cbm * carton.cartons
    if cartons_per_layer <= 0:
        return {
            "label": carton.label,
            "status": "blocked",
            "reason": "Carton footprint does not fit on the configured pallet.",
            "carton_cbm": round(carton_cbm, 4),
            "total_cbm": round(total_cbm, 4),
            "pallet_positions": 0,
            "physical_pallets": 0,
            "warnings": ["包装箱长宽超过托盘可用尺寸，请确认是否需要特殊托盘或换向包装。"],
        }

    layers_per_full_pallet, layer_segments, divider_pallets, full_pallet_height = _max_layers_per_pallet(
        carton.height_cm,
        pallet_height=body.pallet_height_cm,
        max_total_height=body.max_total_height_cm,
        max_continuous_layers=body.max_continuous_layers,
    )
    if layers_per_full_pallet <= 0:
        return {
            "label": carton.label,
            "status": "blocked",
            "reason": "Carton height leaves no valid layer under pallet height limit.",
            "carton_cbm": round(carton_cbm, 4),
            "total_cbm": round(total_cbm, 4),
            "pallet_positions": 0,
            "physical_pallets": 0,
            "warnings": ["包装箱高度超过托盘总高约束，请重新确认包装高度或改为特殊装载。"],
        }

    cartons_per_full_pallet = cartons_per_layer * layers_per_full_pallet
    remaining = carton.cartons
    pallet_units = []
    while remaining > 0:
        cartons_on_pallet = min(remaining, cartons_per_full_pallet)
        layers_needed = (cartons_on_pallet + cartons_per_layer - 1) // cartons_per_layer
        segments = _balanced_layer_segments(layers_needed, body.max_continuous_layers)
        dividers = max(len(segments) - 1, 0)
        total_height = body.pallet_height_cm + layers_needed * carton.height_cm + dividers * body.pallet_height_cm
        pallet_units.append(
            {
                "cartons": cartons_on_pallet,
                "layers": layers_needed,
                "layer_segments": segments,
                "divider_pallets": dividers,
                "gross_height_cm": round(total_height, 1),
                "physical_pallets": 1 + dividers,
            }
        )
        remaining -= cartons_on_pallet

    pallet_positions = len(pallet_units)
    physical_pallets = sum(unit["physical_pallets"] for unit in pallet_units)
    total_weight = carton.weight_kg * carton.cartons if carton.weight_kg is not None else None
    warnings: list[str] = []
    if full_pallet_height > 180:
        warnings.append("满托高度超过 1.8m，虽然低于当前 2.0m 内部上限，但海运/仓储操作建议复核安全余量。")
    if divider_pallets > 0:
        warnings.append("层数超过连续堆叠上限，系统已加入中间托盘分段。")
    if carton.weight_kg is None:
        warnings.append("未录入单箱重量，暂无法校验托盘承重。")

    return {
        "label": carton.label,
        "status": "ok",
        "carton": carton.model_dump(),
        "carton_cbm": round(carton_cbm, 4),
        "total_cbm": round(total_cbm, 4),
        "best_orientation": layer_fit,
        "cartons_per_layer": cartons_per_layer,
        "layers_per_full_pallet": layers_per_full_pallet,
        "cartons_per_full_pallet": cartons_per_full_pallet,
        "full_pallet_height_cm": round(full_pallet_height, 1),
        "full_pallet_layer_segments": layer_segments,
        "divider_pallets_per_full_pallet": divider_pallets,
        "pallet_positions": pallet_positions,
        "physical_pallets": physical_pallets,
        "total_weight_kg": round(total_weight, 2) if total_weight is not None else None,
        "pallet_units": pallet_units,
        "warnings": warnings,
    }


@router.post("/estimate")
def estimate(
    body: ContainerCalcBody,
    _: User = Depends(get_current_user),
) -> dict:
    carton_cbm = (body.length_cm * body.width_cm * body.height_cm) / 1_000_000
    total_cbm = carton_cbm * body.cartons
    # Rough 40HQ ~ 68 CBM internal (varies)
    est_40hq = total_cbm / 68.0 if total_cbm else 0
    return {"carton_cbm": round(carton_cbm, 4), "total_cbm": round(total_cbm, 4), "approx_40hq_load": round(est_40hq, 3)}


@router.post("/pallet-plan")
def pallet_plan(
    body: PalletPlanBody,
    _: User = Depends(get_current_user),
) -> dict:
    plans = [_plan_carton_spec(body, carton) for carton in body.carton_specs]
    total_cbm = sum(plan.get("total_cbm", 0) for plan in plans)
    total_positions = sum(plan.get("pallet_positions", 0) for plan in plans)
    total_physical_pallets = sum(plan.get("physical_pallets", 0) for plan in plans)
    return {
        "standard": {
            "pallet_length_cm": body.pallet_length_cm,
            "pallet_width_cm": body.pallet_width_cm,
            "pallet_height_cm": body.pallet_height_cm,
            "max_total_height_cm": body.max_total_height_cm,
            "max_continuous_layers": body.max_continuous_layers,
            "container_cbm": body.container_cbm,
            "notes": [
                "Internal planning standard: 120 x 100 cm pallet, 20 cm pallet height, max 200 cm gross height.",
                "Wood pallets for international shipping should be checked for ISPM 15 compliance before shipment.",
                "This estimator does not mix different carton sizes on the same pallet yet.",
            ],
        },
        "summary": {
            "total_cbm": round(total_cbm, 4),
            "approx_container_load": round(total_cbm / body.container_cbm, 3) if body.container_cbm else 0,
            "pallet_positions": total_positions,
            "physical_pallets": total_physical_pallets,
            "blocked_specs": sum(1 for plan in plans if plan.get("status") != "ok"),
        },
        "plans": plans,
        "safety": {
            "external_booking_created": False,
            "carrier_notified": False,
            "shipment_created": False,
            "customer_notified": False,
        },
    }
