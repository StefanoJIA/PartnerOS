"""Tests for palletized container planning."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.main import create_app
from app.models import User


def test_pallet_plan_splits_layers_with_middle_pallet():
    app = create_app()
    user = User(id=uuid4(), email="ops@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app) as client:
        response = client.post(
            "/api/container-calculator/pallet-plan",
            json={
                "pallet_length_cm": 120,
                "pallet_width_cm": 100,
                "pallet_height_cm": 20,
                "max_total_height_cm": 200,
                "max_continuous_layers": 8,
                "carton_specs": [
                    {
                        "label": "Desk frame carton",
                        "length_cm": 60,
                        "width_cm": 50,
                        "height_cm": 16,
                        "cartons": 60,
                    }
                ],
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    plan = data["plans"][0]
    assert plan["status"] == "ok"
    assert plan["cartons_per_layer"] == 4
    assert plan["layers_per_full_pallet"] == 10
    assert plan["full_pallet_layer_segments"] == [5, 5]
    assert plan["divider_pallets_per_full_pallet"] == 1
    assert plan["cartons_per_full_pallet"] == 40
    assert data["summary"]["pallet_positions"] == 2
    assert data["summary"]["physical_pallets"] == 3
    assert data["safety"]["carrier_notified"] is False


def test_pallet_plan_blocks_carton_footprint_that_does_not_fit():
    app = create_app()
    user = User(id=uuid4(), email="ops@test.example", is_active=True)
    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app) as client:
        response = client.post(
            "/api/container-calculator/pallet-plan",
            json={
                "carton_specs": [
                    {
                        "label": "Oversize carton",
                        "length_cm": 130,
                        "width_cm": 110,
                        "height_cm": 30,
                        "cartons": 10,
                    }
                ]
            },
        )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["plans"][0]["status"] == "blocked"
    assert data["summary"]["blocked_specs"] == 1
