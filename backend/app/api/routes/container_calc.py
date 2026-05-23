from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models import User

router = APIRouter(prefix="/container-calculator", tags=["tools"])


class ContainerCalcBody(BaseModel):
    length_cm: float
    width_cm: float
    height_cm: float
    cartons: int


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
