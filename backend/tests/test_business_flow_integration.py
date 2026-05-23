"""End-to-end business flow on an isolated PostgreSQL database.

Requires env PARTNEROS_TEST_DATABASE_URL, e.g.:
  postgresql+psycopg://partneros:partneros@127.0.0.1:5432/partneros_test

The database **name** must contain ``test`` or ``testing`` (configured in ``tests/conftest.py``).

Create DB once: createdb partneros_test
Apply schema: see docs/testing.md (Alembic against this URL recommended).

This module uses SQLAlchemy metadata.create_all for speed; for production parity prefer alembic against the same URL.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("PARTNEROS_TEST_DATABASE_URL"),
        reason=(
            "Integration tests need PARTNEROS_TEST_DATABASE_URL pointing to a dedicated PostgreSQL database "
            "(never your primary dev DB)."
        ),
    ),
]


@pytest.fixture(scope="module")
def engine():
    url = os.environ["PARTNEROS_TEST_DATABASE_URL"]
    eng = create_engine(url, poolclass=NullPool)
    from app.core.database import Base

    import app.models  # noqa: F401 register models

    with eng.connect() as c:
        try:
            c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            c.commit()
        except Exception:
            c.rollback()
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def client_and_headers(session_factory):
    from app.core.database import get_db
    from app.core.security import hash_password
    from app.main import create_app
    from app.models import Role, User

    db = session_factory()
    try:
        role = Role(name="Admin", permissions=None)
        db.add(role)
        db.commit()
        db.refresh(role)
        user = User(
            email="p6-flow@example.com",
            full_name="Flow Test User",
            password_hash=hash_password("flow-secret-99"),
            role_id=role.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    finally:
        db.close()

    app = create_app()

    def override_get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"email": "p6-flow@example.com", "password": "flow-secret-99"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    yield client, headers
    app.dependency_overrides.clear()
    client.close()


def test_full_partner_os_business_flow(client_and_headers):
    client, H = client_and_headers
    now = datetime.now(timezone.utc)

    r = client.post(
        "/api/companies",
        headers=H,
        json={
            "company_name": "Integration Demo Co",
            "company_type": "Office Furniture Dealer",
            "city": "Chicago",
            "state": "IL",
            "country": "United States",
        },
    )
    assert r.status_code == 201, r.text
    company_id = r.json()["id"]

    r = client.post(
        "/api/contacts",
        headers=H,
        json={
            "first_name": "Alex",
            "last_name": "Buyer",
            "company_id": company_id,
            "email": "alex.buyer@example.com",
            "contact_type": "Buyer",
        },
    )
    assert r.status_code == 201, r.text
    contact_id = r.json()["id"]

    r = client.post(
        "/api/leads",
        headers=H,
        json={
            "lead_name": "Adjustable frame pilot",
            "company_id": company_id,
            "primary_contact_id": contact_id,
            "source": "LinkedIn",
            "lead_type": "RFQ Opportunity",
            "current_stage": "New",
            "priority": "high",
        },
    )
    assert r.status_code == 201, r.text
    lead_id = r.json()["id"]

    r = client.post(
        "/api/manufacturing-partners",
        headers=H,
        json={
            "partner_name": "Demo Lifting Partner A",
            "partner_type": "Lifting System Manufacturer",
            "country": "China",
            "city": "Shenzhen",
            "certifications": "BIFMA ready",
            "project_fit_rating": 4,
            "risk_level": "low",
        },
    )
    assert r.status_code == 201, r.text
    partner_a_id = r.json()["id"]

    r = client.post(
        "/api/manufacturing-partners",
        headers=H,
        json={
            "partner_name": "Demo Furniture Partner B",
            "partner_type": "Office Furniture Manufacturer",
            "country": "China",
            "city": "Ningbo",
            "certifications": "ISO complete",
            "project_fit_rating": 4,
            "risk_level": "low",
        },
    )
    assert r.status_code == 201, r.text
    partner_b_id = r.json()["id"]

    r = client.post(
        "/api/products",
        headers=H,
        json={
            "product_name": "Heavy-duty Frame (integration)",
            "product_category": "Desk Frame",
            "description": "Integration SKU",
        },
    )
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]

    for pid in (partner_a_id, partner_b_id):
        r = client.post(
            f"/api/products/{product_id}/partners",
            headers=H,
            json={
                "manufacturing_partner_id": pid,
                "capability_level": "high",
                "partner_moq": 10,
                "lead_time_days": 35,
                "partner_price_range": "200-300 USD",
                "sample_available": True,
                "certification_status": "complete",
            },
        )
        assert r.status_code == 201, r.text

    r = client.post(
        "/api/rfqs",
        headers=H,
        json={
            "lead_id": lead_id,
            "company_id": company_id,
            "contact_id": contact_id,
            "customer_requirement": "20 units evaluation",
            "quantity": 20,
            "status": "Draft",
        },
    )
    assert r.status_code == 201, r.text
    rfq_id = r.json()["id"]

    r = client.post(
        f"/api/rfqs/{rfq_id}/items",
        headers=H,
        json={"product_id": product_id, "quantity": 20, "spec_notes": "heavy-duty"},
    )
    assert r.status_code == 201, r.text
    rfq_item_id = r.json()["id"]

    r = client.post(
        f"/api/rfqs/{rfq_id}/partner-candidates",
        headers=H,
        json={"partner_id": partner_a_id, "partner_status": "Candidate"},
    )
    assert r.status_code == 201, r.text
    cand_a = r.json()["id"]

    r = client.post(
        f"/api/rfqs/{rfq_id}/partner-candidates",
        headers=H,
        json={"partner_id": partner_b_id, "partner_status": "Candidate"},
    )
    assert r.status_code == 201, r.text
    cand_b = r.json()["id"]

    r = client.post(
        f"/api/rfqs/{rfq_id}/partner-candidates/{cand_a}/quote-requested",
        headers=H,
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/api/rfqs/{rfq_id}/partner-candidates/{cand_b}/quote-received",
        headers=H,
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/api/rfqs/{rfq_id}/quotations",
        headers=H,
        json={
            "manufacturing_partner_id": partner_a_id,
            "product_id": product_id,
            "quantity": 20,
            "unit_price": "100.00",
            "moq": 10,
            "lead_time": "40 days",
            "sample_cost": "50.00",
            "tooling_cost": "200.00",
            "packaging_cost": "35.00",
            "estimated_shipping_cost": "400.00",
            "landed_cost": "2500.00",
            "target_margin": "0.28",
            "currency": "USD",
            "incoterm": "FOB",
            "valid_until": str(date.today() + timedelta(days=30)),
        },
    )
    assert r.status_code == 201, r.text
    quote_a_id = r.json()["id"]

    r = client.post(
        f"/api/rfqs/{rfq_id}/quotations",
        headers=H,
        json={
            "manufacturing_partner_id": partner_b_id,
            "product_id": product_id,
            "quantity": 20,
            "unit_price": "120.00",
            "moq": 10,
            "lead_time": "38 days",
            "sample_cost": "55.00",
            "tooling_cost": "180.00",
            "packaging_cost": "40.00",
            "estimated_shipping_cost": "450.00",
            "landed_cost": "2900.00",
            "target_margin": "0.25",
            "currency": "USD",
            "incoterm": "CIF",
            "valid_until": str(date.today() + timedelta(days=28)),
        },
    )
    assert r.status_code == 201, r.text
    quote_b_id = r.json()["id"]

    r = client.get(f"/api/rfqs/{rfq_id}/quotation-comparison", headers=H)
    assert r.status_code == 200, r.text
    cmp1 = r.json()
    best_price_1 = (cmp1.get("best_price_option") or {}).get("quotation_id")

    client.put(
        f"/api/manufacturing-partners/{partner_a_id}",
        headers=H,
        json={"partner_name": "Renamed Lifting Partner A"},
    )
    client.put(
        f"/api/manufacturing-partners/{partner_b_id}",
        headers=H,
        json={"partner_name": "Renamed Furniture Partner B"},
    )

    r = client.get(f"/api/rfqs/{rfq_id}/quotation-comparison", headers=H)
    assert r.status_code == 200, r.text
    cmp2 = r.json()
    best_price_2 = (cmp2.get("best_price_option") or {}).get("quotation_id")
    assert best_price_1 == best_price_2 == quote_a_id

    r = client.post(
        f"/api/rfqs/{rfq_id}/convert-to-sample",
        headers=H,
        json={"rfq_item_id": rfq_item_id, "manufacturing_partner_id": partner_a_id},
    )
    assert r.status_code == 201, r.text
    sample_id = r.json()["id"]

    r = client.get(f"/api/samples/{sample_id}/workspace", headers=H)
    assert r.status_code == 200, r.text
    sw = r.json()
    assert sw["sample"]["id"] == sample_id
    assert sw["company"]["id"] == company_id

    r = client.post(
        f"/api/samples/{sample_id}/status",
        headers=H,
        json={"status": "Shipped"},
    )
    assert r.status_code == 200, r.text

    r = client.put(
        f"/api/samples/{sample_id}/shipping",
        headers=H,
        json={"courier": "DEMO-COURIER", "tracking_number": "INT-TRACK-001"},
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/api/samples/{sample_id}/status",
        headers=H,
        json={"status": "Delivered"},
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/api/samples/{sample_id}/feedback",
        headers=H,
        json={"customer_feedback": "Looks solid for phase 2.", "interest_level": "high"},
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/api/samples/{sample_id}/convert-to-order",
        headers=H,
        json={"manufacturing_partner_id": partner_a_id, "generate_milestones": True},
    )
    assert r.status_code == 201, r.text
    order_id = r.json()["id"]

    r = client.get(f"/api/orders/{order_id}/workspace", headers=H)
    assert r.status_code == 200, r.text
    ow = r.json()
    assert ow["order"]["id"] == order_id
    assert len(ow["production_milestones"]) >= 1

    r = client.post(
        f"/api/orders/{order_id}/generate-milestones",
        headers=H,
        params={"force": "true"},
    )
    assert r.status_code == 200, r.text

    r = client.get(f"/api/orders/{order_id}/workspace", headers=H)
    milestones = r.json()["production_milestones"]
    assert len(milestones) >= 2
    m0_id = milestones[0]["id"]
    m1_id = milestones[1]["id"]

    r = client.post(f"/api/orders/{order_id}/milestones/{m0_id}/complete", headers=H)
    assert r.status_code == 200, r.text

    r = client.post(f"/api/orders/{order_id}/milestones/{m1_id}/delayed", headers=H)
    assert r.status_code == 200, r.text

    r = client.put(
        f"/api/orders/{order_id}/milestones/{m1_id}",
        headers=H,
        json={"notes": "Integration: milestone notes after delay review.", "responsible_party": "Demo PM"},
    )
    assert r.status_code == 200, r.text

    r = client.post(
        f"/api/orders/{order_id}/shipping-records",
        headers=H,
        json={
            "origin_port": "Ningbo",
            "destination_port": "Los Angeles",
            "freight_forwarder": "Demo Forwarder",
            "booking_date": str(date.today()),
            "etd": str(date.today() + timedelta(days=7)),
            "eta": str(date.today() + timedelta(days=30)),
        },
    )
    assert r.status_code == 201, r.text

    client.post(
        "/api/tasks",
        headers=H,
        json={
            "title": "Due today task",
            "due_at": now.isoformat(),
            "status": "open",
            "priority": "high",
            "related_object_type": "lead",
            "related_object_id": lead_id,
        },
    )
    client.post(
        "/api/tasks",
        headers=H,
        json={
            "title": "This week task",
            "due_at": (now + timedelta(days=3)).isoformat(),
            "status": "open",
            "priority": "medium",
            "related_object_type": "lead",
            "related_object_id": lead_id,
        },
    )

    r = client.get("/api/dashboard/actions", headers=H)
    assert r.status_code == 200, r.text
    dash = r.json()
    for key in (
        "due_today_tasks",
        "overdue_tasks",
        "rfqs_waiting_partner_quote",
        "orders_delayed_milestones",
        "recommended_actions",
    ):
        assert key in dash

    r = client.get(f"/api/objects/rfq/{rfq_id}/activity", headers=H, params={"page": 1, "limit": 200})
    assert r.status_code == 200, r.text
    actions = {a["action"] for a in r.json()["items"]}
    assert "rfq_created" in actions
    assert "quotation_added" in actions
