"""Rule-based quotation comparison for an RFQ (no partner-name bias)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.models import ManufacturingPartner, Quotation


def _parse_lead_time_days(val: str | None) -> int | None:
    if not val:
        return None
    m = re.search(r"(\d+)", val)
    return int(m.group(1)) if m else None


def _cert_score(text: str | None) -> float | None:
    if not text:
        return None
    t = text.lower()
    if any(x in t for x in ("complete", "ready", "yes", "passed", "available", "certified")):
        return 1.0
    if any(x in t for x in ("pending", "partial", "progress", "in process")):
        return 0.5
    return 0.25


def _margin_score(m: Decimal | None) -> float | None:
    if m is None:
        return None
    try:
        return float(m)
    except Exception:
        return None


@dataclass
class _QuotRow:
    q: Quotation
    partner: ManufacturingPartner | None
    lead_days: int | None
    unit_price_f: float | None
    landed_f: float | None
    moq: int | None
    sample_ok: bool
    cert_score: float | None
    project_fit: float | None
    margin_f: float | None
    risk_partner: str | None
    missing: list[str]


class ComparisonPick(BaseModel):
    quotation_id: UUID | None = None
    rationale: str = ""
    missing_data: bool = False


class QuotationComparisonOut(BaseModel):
    best_price_option: ComparisonPick | None = None
    best_landed_cost_option: ComparisonPick | None = None
    best_lead_time_option: ComparisonPick | None = None
    best_sample_option: ComparisonPick | None = None
    best_certification_option: ComparisonPick | None = None
    best_moq_option: ComparisonPick | None = None
    best_project_fit_option: ComparisonPick | None = None
    best_margin_option: ComparisonPick | None = None
    best_overall_option: ComparisonPick | None = None
    risk_notes: list[str]


def build_quotation_comparison(
    quotations: list[Quotation],
    partners_by_id: dict[UUID, ManufacturingPartner],
) -> QuotationComparisonOut:
    risk_notes: list[str] = []
    rows: list[_QuotRow] = []
    for q in quotations:
        p = partners_by_id.get(q.manufacturing_partner_id) if q.manufacturing_partner_id else None
        missing: list[str] = []
        if q.unit_price is None:
            missing.append("unit_price")
        if q.landed_cost is None:
            missing.append("landed_cost")
        ld = _parse_lead_time_days(q.lead_time)
        if ld is None and q.lead_time:
            missing.append("lead_time_parseable")
        elif ld is None:
            missing.append("lead_time")
        moq = q.moq
        if moq is None:
            missing.append("moq")
        sc = q.sample_cost
        sample_ok = sc is not None and sc >= 0
        cert_txt = p.certifications if p and p.certifications else None
        cert = _cert_score(cert_txt)
        if cert is None:
            missing.append("certification_signal")
        pf: float | None = None
        if p and p.project_fit_rating is not None:
            pf = float(p.project_fit_rating) / 5.0
        else:
            missing.append("project_fit_rating")
        margin = _margin_score(q.target_margin)
        if margin is None:
            missing.append("target_margin")
        risk = (p.risk_level.lower() if p and p.risk_level else None) or None
        if risk == "high":
            risk_notes.append("At least one quoted partner has risk_level=high; verify data independently.")

        rows.append(
            _QuotRow(
                q=q,
                partner=p,
                lead_days=ld,
                unit_price_f=float(q.unit_price) if q.unit_price is not None else None,
                landed_f=float(q.landed_cost) if q.landed_cost is not None else None,
                moq=moq,
                sample_ok=sample_ok,
                cert_score=cert,
                project_fit=pf,
                margin_f=margin,
                risk_partner=risk,
                missing=missing,
            )
        )

    def pick_min(pred, key, label: str) -> ComparisonPick | None:
        cand = [r for r in rows if pred(r) and key(r) is not None]
        if not cand:
            return ComparisonPick(
                quotation_id=None,
                rationale=f"No quotations with comparable {label} data.",
                missing_data=True,
            )
        best = min(cand, key=lambda r: key(r))  # type: ignore[operator]
        return ComparisonPick(
            quotation_id=best.q.id,
            rationale=f"Best {label} by rule (lower is better).",
            missing_data=False,
        )

    def pick_max(pred, key, label: str) -> ComparisonPick | None:
        cand = [r for r in rows if pred(r) and key(r) is not None]
        if not cand:
            return ComparisonPick(quotation_id=None, rationale=f"No data for {label}.", missing_data=True)
        best = max(cand, key=lambda r: key(r))  # type: ignore[operator]
        return ComparisonPick(quotation_id=best.q.id, rationale=f"Best {label} by rule.", missing_data=False)

    best_price = pick_min(lambda r: True, lambda r: r.unit_price_f, "unit price")
    best_landed = pick_min(lambda r: True, lambda r: r.landed_f, "landed cost")
    best_lead = pick_min(lambda r: r.lead_days is not None, lambda r: r.lead_days, "lead time (days)")
    best_moq = pick_min(lambda r: r.moq is not None, lambda r: r.moq, "MOQ")

    sample_capable = [r for r in rows if r.sample_ok]
    if not sample_capable:
        best_sample = ComparisonPick(
            quotation_id=None,
            rationale="No quotation documents sample_cost; cannot infer sample availability.",
            missing_data=True,
        )
    else:
        best_s = min(
            sample_capable,
            key=lambda r: (
                float(r.q.sample_cost or Decimal("0")),
                str(r.q.id),
            ),
        )
        best_sample = ComparisonPick(
            quotation_id=best_s.q.id,
            rationale="Sample-capable quotes ranked by lowest sample_cost (tie-break: quotation id).",
            missing_data=False,
        )

    best_cert = pick_max(lambda r: r.cert_score is not None, lambda r: r.cert_score or 0, "certification signal")
    best_project_fit = pick_max(
        lambda r: r.project_fit is not None, lambda r: r.project_fit or 0, "project fit (partner rating)"
    )
    best_margin = pick_max(lambda r: r.margin_f is not None, lambda r: r.margin_f or 0, "target margin")

    weights = {
        "price": 0.22,
        "landed": 0.22,
        "lead": 0.14,
        "moq": 0.1,
        "cert": 0.1,
        "project": 0.12,
        "margin": 0.1,
    }
    best_overall: ComparisonPick | None = None
    if not rows:
        best_overall = ComparisonPick(
            quotation_id=None, rationale="No quotations to compare.", missing_data=True
        )
    else:
        scored: list[tuple[float, _QuotRow, list[str]]] = []
        prices = [r.unit_price_f for r in rows if r.unit_price_f is not None]
        lands = [r.landed_f for r in rows if r.landed_f is not None]
        leads = [r.lead_days for r in rows if r.lead_days is not None]
        moqs = [r.moq for r in rows if r.moq is not None]
        min_p, max_p = (min(prices), max(prices)) if prices else (None, None)
        min_l, max_l = (min(lands), max(lands)) if lands else (None, None)
        min_ld, max_ld = (min(leads), max(leads)) if leads else (None, None)
        min_moq, max_moq = (min(moqs), max(moqs)) if moqs else (None, None)

        for r in rows:
            miss: list[str] = []
            s = 0.0
            wsum = 0.0
            if r.unit_price_f is not None and min_p is not None and max_p is not None and max_p > min_p:
                s += weights["price"] * (1 - (r.unit_price_f - min_p) / (max_p - min_p))
                wsum += weights["price"]
            else:
                miss.append("unit_price")

            if r.landed_f is not None and min_l is not None and max_l is not None and max_l > min_l:
                s += weights["landed"] * (1 - (r.landed_f - min_l) / (max_l - min_l))
                wsum += weights["landed"]
            else:
                miss.append("landed_cost")

            if r.lead_days is not None and min_ld is not None and max_ld is not None and max_ld > min_ld:
                s += weights["lead"] * (1 - (r.lead_days - min_ld) / (max_ld - min_ld))
                wsum += weights["lead"]
            else:
                miss.append("lead_time")

            if r.moq is not None and min_moq is not None and max_moq is not None and max_moq > min_moq:
                s += weights["moq"] * (1 - (r.moq - min_moq) / (max_moq - min_moq))
                wsum += weights["moq"]
            else:
                miss.append("moq")

            if r.cert_score is not None:
                s += weights["cert"] * r.cert_score
                wsum += weights["cert"]
            else:
                miss.append("certification")

            if r.project_fit is not None:
                s += weights["project"] * r.project_fit
                wsum += weights["project"]
            else:
                miss.append("project_fit")

            if r.margin_f is not None:
                margin_scores = [x.margin_f for x in rows if x.margin_f is not None]
                if margin_scores:
                    mn, mx = min(margin_scores), max(margin_scores)
                    if mx > mn:
                        s += weights["margin"] * ((r.margin_f - mn) / (mx - mn))
                    else:
                        s += weights["margin"] * 0.5
                    wsum += weights["margin"]
            else:
                miss.append("target_margin")

            if wsum < 0.35:
                scored.append((-1.0, r, miss))
            else:
                scored.append((s / wsum, r, miss))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_score, top_row, top_miss = scored[0]
        if top_score < 0:
            best_overall = ComparisonPick(
                quotation_id=None,
                rationale="Missing Data: insufficient comparable fields for scored overall pick.",
                missing_data=True,
            )
            risk_notes.append("Overall comparison deferred until more quote fields are filled.")
        else:
            best_overall = ComparisonPick(
                quotation_id=top_row.q.id,
                rationale="Highest composite score from available numeric fields only.",
                missing_data=bool(top_miss),
            )

    return QuotationComparisonOut(
        best_price_option=best_price,
        best_landed_cost_option=best_landed,
        best_lead_time_option=best_lead,
        best_sample_option=best_sample,
        best_certification_option=best_cert,
        best_moq_option=best_moq,
        best_project_fit_option=best_project_fit,
        best_margin_option=best_margin,
        best_overall_option=best_overall,
        risk_notes=risk_notes,
    )
