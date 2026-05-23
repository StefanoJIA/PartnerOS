"""Activity log JSON serialization (D5.2.6 P2)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.models import ActivityLog
from app.services.activity import log_activity
from app.services.json_safe import serialize_for_json


class SampleEnum(Enum):
    alpha = "alpha"


def test_serialize_for_json_uuid_datetime_nested():
    uid = uuid4()
    dt = datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc)
    d = date(2026, 5, 23)
    dec = Decimal("12.50")
    raw = {
        "primary_contact_id": uid,
        "nested": {"when": dt, "day": d, "amount": dec, "tag": SampleEnum.alpha},
        "items": [uid, dt],
    }
    out = serialize_for_json(raw)
    assert out["primary_contact_id"] == str(uid)
    assert out["nested"]["when"] == dt.isoformat()
    assert out["nested"]["day"] == "2026-05-23"
    assert out["nested"]["amount"] == "12.50"
    assert out["nested"]["tag"] == "alpha"
    assert out["items"][0] == str(uid)
    json.dumps(out)


def test_log_activity_stores_json_safe_diff():
    db = MagicMock()
    uid = uuid4()
    log_activity(
        db,
        object_type="lead",
        object_id=uid,
        action="lead_updated",
        actor_id=uid,
        diff={"primary_contact_id": uid, "next_action_due_date": date(2026, 6, 1)},
    )
    db.add.assert_called_once()
    entry = db.add.call_args[0][0]
    assert isinstance(entry, ActivityLog)
    assert entry.diff["primary_contact_id"] == str(uid)
    assert entry.diff["next_action_due_date"] == "2026-06-01"
    json.dumps(entry.diff)
