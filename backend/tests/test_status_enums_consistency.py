"""Ensure API validation sets stay aligned with SQLAlchemy Enum definitions."""

from app import constants
from app.models import enums as me


def test_status_frozensets_match_sqlalchemy_enums():
    assert constants.status_enums.LEAD_STAGES == {e.value for e in me.LeadStage}
    assert constants.status_enums.RFQ_STATUSES == {e.value for e in me.RFQStatus}
    assert constants.status_enums.RFQ_CANDIDATE_STATUSES == {e.value for e in me.RFQPartnerCandidateStatus}
    assert constants.status_enums.SAMPLE_STATUSES == {e.value for e in me.SampleStatus}
    assert constants.status_enums.ORDER_PRODUCTION_STATUSES == {e.value for e in me.OrderProductionStatus}
    assert constants.status_enums.ORDER_SHIPPING_STATUSES == {e.value for e in me.OrderShippingStatus}
    assert constants.status_enums.TASK_STATUSES == {e.value for e in me.TaskStatus}
    assert constants.status_enums.PRIORITY_LEVELS == {e.value for e in me.TaskPriority}
    assert constants.status_enums.RISK_LEVELS == {e.value for e in me.RiskLevel}
