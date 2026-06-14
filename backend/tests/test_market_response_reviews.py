"""Tests for the persisted Market Response review queue."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.database import get_db
from app.core.deps import get_current_user
from app.main import create_app
from app.models import User
from app.schemas.market_response_reviews import MarketResponseReviewCreate
from app.services.market_response_reviews import market_response_review_safety


def _reviews_payload() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "READY_FOR_STAGING_HANDOFF",
        "external_staging_state": "WAITING_FOR_REAL_STAGING_EVIDENCE",
        "reviews": [
            {
                "id": str(uuid4()),
                "partner_focus": "HOSUN",
                "focus_category": "adjustable_desk_frames",
                "product_focus": ["lifting systems", "desk frames"],
                "review_dimension": "load",
                "review_dimension_label": "承重",
                "visibility_class": "needs validation",
                "visibility_class_label": "需要验证",
                "priority": "P1",
                "priority_label": "P1 rehearsal 后优先处理",
                "status": "needs review",
                "status_label": "待人工审查",
                "source_type": "market signal",
                "source_type_label": "市场信号",
                "source_summary": "Load range needs business-safe wording.",
                "evidence_summary": "Quote/order/feedback context required.",
                "customer_safe_summary": None,
                "internal_notes": "Raw test notes stay internal-only.",
                "next_action": "Confirm supported load wording.",
                "owner": "business owner",
                "due_date": None,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "status_options": [{"value": "needs review", "label": "待人工审查"}],
        "visibility_options": [{"value": "needs validation", "label": "需要验证"}],
        "priority_options": [{"value": "P1", "label": "P1 rehearsal 后优先处理"}],
        "source_type_options": [{"value": "market signal", "label": "市场信号"}],
        "review_dimension_options": [{"value": "load", "label": "承重"}],
        "status_counts": {"needs review": 1},
        "visibility_counts": {"needs validation": 1},
        "partner_counts": {"HOSUN": 1},
        "safety": market_response_review_safety(),
    }


def test_market_response_reviews_route(monkeypatch):
    app = create_app()
    user = User(id=uuid4(), email="market-review@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: (yield object())
    monkeypatch.setattr(
        "app.api.v1.routes.market_response.build_market_response_review_console",
        lambda db, actor, **filters: _reviews_payload(),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/market/response-reviews?partner_focus=HOSUN")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "READY_FOR_STAGING_HANDOFF"
    assert payload["external_staging_state"] == "WAITING_FOR_REAL_STAGING_EVIDENCE"
    assert payload["reviews"][0]["review_dimension"] == "load"
    assert payload["reviews"][0]["visibility_class"] == "needs validation"
    assert payload["safety"]["email_sent"] is False
    assert payload["safety"]["quote_status_changed"] is False
    assert payload["safety"]["order_status_changed"] is False
    assert payload["safety"]["staging_validated"] is False


def test_market_response_review_rejects_token_like_internal_notes():
    with pytest.raises(ValidationError):
        MarketResponseReviewCreate(
            partner_focus="JOOBOO",
            focus_category="education_furniture",
            product_focus=["education furniture"],
            review_dimension="resource needs",
            visibility_class="internal-only",
            priority="P2",
            status="needs review",
            source_type="operator review",
            source_summary="Resource review",
            internal_notes="Authorization: Bearer actual-secret-value",
        )


def test_market_response_review_requires_summary_before_customer_safe_reviewed():
    with pytest.raises(ValidationError):
        MarketResponseReviewCreate(
            partner_focus="HOSUN",
            focus_category="adjustable_desk_frames",
            product_focus=["lifting systems"],
            review_dimension="load",
            visibility_class="customer-safe candidate",
            priority="P1",
            status="reviewed",
            source_type="market signal",
            source_summary="Load range looks reusable.",
        )


def test_market_response_review_accepts_peer_partner_dimensions():
    payload = MarketResponseReviewCreate(
        partner_focus="future partner",
        focus_category="future_partner_onboarding",
        product_focus=["onboarding data", "product family"],
        review_dimension="market response metrics",
        visibility_class="needs validation",
        priority="P2",
        status="needs review",
        source_type="partner onboarding",
        source_summary="Define shared metrics without exposing internal scoring.",
    )

    assert payload.partner_focus == "future partner"
    assert payload.review_dimension == "market response metrics"
