"""Canonical string sets for API request bodies (DB columns stay plain text).

Values are derived from ``app.models.enums`` so Python code and DB strings stay aligned.
Validators should import the ``*_STATUSES`` / ``*_LEVELS`` frozensets from this module.
"""

from __future__ import annotations

from typing import ClassVar

from app.models.enums import (
    LeadStage as _LeadStageEnum,
    OrderProductionStatus as _OrderProductionStatusEnum,
    OrderShippingStatus as _OrderShippingStatusEnum,
    RFQPartnerCandidateStatus as _RFQPartnerCandidateStatusEnum,
    RFQStatus as _RFQStatusEnum,
    RiskLevel as _RiskLevelEnum,
    SampleStatus as _SampleStatusEnum,
    TaskPriority as _TaskPriorityEnum,
    TaskStatus as _TaskStatusEnum,
)

LEAD_STAGES: frozenset[str] = frozenset(e.value for e in _LeadStageEnum)
RFQ_STATUSES: frozenset[str] = frozenset(e.value for e in _RFQStatusEnum)
RFQ_CANDIDATE_STATUSES: frozenset[str] = frozenset(e.value for e in _RFQPartnerCandidateStatusEnum)
SAMPLE_STATUSES: frozenset[str] = frozenset(e.value for e in _SampleStatusEnum)
ORDER_PRODUCTION_STATUSES: frozenset[str] = frozenset(e.value for e in _OrderProductionStatusEnum)
ORDER_SHIPPING_STATUSES: frozenset[str] = frozenset(e.value for e in _OrderShippingStatusEnum)
TASK_STATUSES: frozenset[str] = frozenset(e.value for e in _TaskStatusEnum)
PRIORITY_LEVELS: frozenset[str] = frozenset(e.value for e in _TaskPriorityEnum)
RISK_LEVELS: frozenset[str] = frozenset(e.value for e in _RiskLevelEnum)

# Production milestone row workflow (not the order-level production pipeline).
MILESTONE_ROW_STATUSES: frozenset[str] = frozenset(
    ("pending", "in_progress", "completed", "delayed", "done", "complete")
)


class LeadStage:
    VALUES: ClassVar[frozenset[str]] = LEAD_STAGES


class RFQStatus:
    VALUES: ClassVar[frozenset[str]] = RFQ_STATUSES


class RFQCandidateStatus:
    VALUES: ClassVar[frozenset[str]] = RFQ_CANDIDATE_STATUSES


class SampleStatus:
    VALUES: ClassVar[frozenset[str]] = SAMPLE_STATUSES


class OrderProductionStatus:
    VALUES: ClassVar[frozenset[str]] = ORDER_PRODUCTION_STATUSES


class OrderShippingStatus:
    VALUES: ClassVar[frozenset[str]] = ORDER_SHIPPING_STATUSES


class TaskStatus:
    VALUES: ClassVar[frozenset[str]] = TASK_STATUSES


class PriorityLevel:
    VALUES: ClassVar[frozenset[str]] = PRIORITY_LEVELS


class RiskLevel:
    VALUES: ClassVar[frozenset[str]] = RISK_LEVELS
