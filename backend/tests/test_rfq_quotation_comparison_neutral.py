"""Quotation comparison must not depend on partner display names."""

import uuid
from decimal import Decimal

from app.models.partners import ManufacturingPartner
from app.models.rfq import Quotation
from app.services.quotation_comparison import build_quotation_comparison


def _partner(pid: uuid.UUID, name: str, **kwargs) -> ManufacturingPartner:
    return ManufacturingPartner(
        id=pid,
        partner_name=name,
        partner_type="Factory",
        certifications=kwargs.get("certifications", "complete"),
        project_fit_rating=kwargs.get("project_fit_rating", 5),
        risk_level=kwargs.get("risk_level", "low"),
    )


def _quote(qid: uuid.UUID, pid: uuid.UUID, **kwargs) -> Quotation:
    return Quotation(
        id=qid,
        rfq_id=uuid.uuid4(),
        manufacturing_partner_id=pid,
        quantity=100,
        unit_price=kwargs.get("unit_price", Decimal("10")),
        landed_cost=kwargs.get("landed_cost", Decimal("12")),
        moq=kwargs.get("moq", 50),
        lead_time=kwargs.get("lead_time", "20 days"),
        sample_cost=kwargs.get("sample_cost", Decimal("0")),
        target_margin=kwargs.get("target_margin", Decimal("0.15")),
    )


def test_best_overall_unchanged_when_only_partner_names_differ():
    pa = uuid.uuid4()
    pb = uuid.uuid4()
    qa = uuid.uuid4()
    qb = uuid.uuid4()
    p_a = _partner(pa, "Demo Lifting Partner Alpha")
    p_b = _partner(pb, "Generic Partner Beta")
    q_a = _quote(qa, pa, unit_price=Decimal("9"), landed_cost=Decimal("11"))
    q_b = _quote(qb, pb, unit_price=Decimal("20"), landed_cost=Decimal("25"))

    out1 = build_quotation_comparison([q_a, q_b], {pa: p_a, pb: p_b})

    p_a2 = _partner(pa, "Renamed A")
    p_b2 = _partner(pb, "Renamed B")
    out2 = build_quotation_comparison([q_a, q_b], {pa: p_a2, pb: p_b2})

    assert out1.best_overall_option and out1.best_overall_option.quotation_id
    assert out2.best_overall_option and out2.best_overall_option.quotation_id
    assert out1.best_overall_option.quotation_id == out2.best_overall_option.quotation_id


def test_best_project_fit_uses_partner_rating_not_name():
    pa = uuid.uuid4()
    pb = uuid.uuid4()
    qa = uuid.uuid4()
    qb = uuid.uuid4()
    p_a = _partner(pa, "ZZZ Partner", project_fit_rating=3)
    p_b = _partner(pb, "AAA Partner", project_fit_rating=5)
    q_a = _quote(qa, pa, unit_price=Decimal("10"), landed_cost=Decimal("12"), lead_time="20 days")
    q_b = _quote(qb, pb, unit_price=Decimal("10"), landed_cost=Decimal("12"), lead_time="20 days")
    out = build_quotation_comparison([q_a, q_b], {pa: p_a, pb: p_b})
    assert out.best_project_fit_option
    assert out.best_project_fit_option.quotation_id == qb
    assert not out.best_project_fit_option.missing_data


def test_best_sample_is_lowest_sample_cost_tiebreak_by_quotation_id():
    pa = uuid.uuid4()
    pb = uuid.uuid4()
    qa = uuid.uuid4()
    qb = uuid.uuid4()
    p_a = _partner(pa, "Partner A")
    p_b = _partner(pb, "Partner B")
    q_a = _quote(
        qa,
        pa,
        unit_price=Decimal("10"),
        landed_cost=Decimal("12"),
        moq=10,
        lead_time="20 days",
        sample_cost=Decimal("100"),
    )
    q_b = _quote(
        qb,
        pb,
        unit_price=Decimal("11"),
        landed_cost=Decimal("13"),
        moq=10,
        lead_time="21 days",
        sample_cost=Decimal("50"),
    )
    out = build_quotation_comparison([q_a, q_b], {pa: p_a, pb: p_b})
    assert out.best_sample_option and out.best_sample_option.quotation_id == qb


def test_best_price_is_lowest_numeric_not_alphabetical_partner():
    pa = uuid.uuid4()
    pb = uuid.uuid4()
    qa = uuid.uuid4()
    qb = uuid.uuid4()
    p_a = _partner(pa, "ZZZ Late Alphabet Partner")
    p_b = _partner(pb, "AAA Early Alphabet Partner")
    q_a = _quote(qa, pa, unit_price=Decimal("5"))
    q_b = _quote(qb, pb, unit_price=Decimal("50"))

    out = build_quotation_comparison([q_a, q_b], {pa: p_a, pb: p_b})
    assert out.best_price_option and out.best_price_option.quotation_id == qa
