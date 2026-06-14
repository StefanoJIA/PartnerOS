"""Tests for the internal External Execution workspace."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User
from app.schemas.external_execution import ExternalExecutionActionCreate


def _console_payload() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "READY_FOR_STAGING_HANDOFF",
        "external_staging_state": "WAITING_FOR_REAL_STAGING_EVIDENCE",
        "actions": [
            {
                "id": str(uuid4()),
                "action_type": "partner rehearsal request",
                "target_partner_system": "HOSUN / JOOBOO",
                "partner_focus": "multi-partner",
                "product_focus": ["lifting systems", "education furniture"],
                "owner": "业务负责人",
                "due_date": None,
                "dependency": "partner rehearsal script",
                "next_step": "manual follow-up only",
                "status": "ready to send",
                "status_label": "待人工发送",
                "response_summary": None,
                "risk_notes": None,
                "blocker_notes": None,
                "redacted_credential_status": None,
                "staging_readiness_key": None,
                "pilot_readiness_key": "partner_feedback",
                "notes": "不自动发送",
                "created_at": now,
                "updated_at": now,
            }
        ],
        "status_options": [{"value": "draft", "label": "草稿"}],
        "status_counts": {"ready to send": 1},
        "staging_readiness": [{"item": "D9 entry gate", "status": "blocked", "detail": "No real evidence."}],
        "lifting_systems_field_review": [{"field": "load", "review_class": "customer-safe candidate", "rule": "needs sign-off"}],
        "partner_coverage": [{"partner": "JOOBOO", "focus": "education furniture", "rule": "peer partner"}],
        "safety": {
            "email_sent": False,
            "sms_sent": False,
            "linkedin_sent": False,
            "customer_notified": False,
            "supplier_notified": False,
            "external_api_called": False,
            "raw_token_recorded": False,
            "staging_validated": False,
            "d9_entered": False,
            "quote_status_changed": False,
            "order_status_changed": False,
        },
    }


def test_external_execution_console_route(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="ops@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield MagicMock())
    monkeypatch.setattr(
        "app.api.v1.routes.external_execution.build_external_execution_console",
        lambda db, actor: _console_payload(),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/external-execution/console")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "READY_FOR_STAGING_HANDOFF"
    assert payload["external_staging_state"] == "WAITING_FOR_REAL_STAGING_EVIDENCE"
    assert payload["actions"][0]["status"] == "ready to send"
    assert payload["safety"]["email_sent"] is False
    assert payload["safety"]["raw_token_recorded"] is False


def test_external_execution_rejects_response_received_without_summary():
    with pytest.raises(ValidationError):
        ExternalExecutionActionCreate(
            action_type="partner rehearsal request",
            target_partner_system="HOSUN",
            status="response received",
        )


def test_external_execution_rejects_token_like_notes():
    with pytest.raises(ValidationError):
        ExternalExecutionActionCreate(
            action_type="staging credentials request",
            target_partner_system="service.intelli-opus.com",
            notes="Authorization: Bearer actual-secret-value",
        )
